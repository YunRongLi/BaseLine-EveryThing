#!/usr/bin/env python3
"""
Azure DevOps CLI Tool for AI Agents and Engineers.
Authentication strictly uses Azure CLI ('az login') OAuth 2.0 Bearer tokens (Zero-PAT policy).
Adheres strictly to no-icons and no-emojis output rules.
"""

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Optional

# Ensure lib directory is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from lib.auth import AzureCliAuthProvider
from lib.client import AzureDevOpsClient
from lib.config import ToolConfig
from lib.exceptions import AdoAuthError, AdoError, AdoNotFoundError
from lib.formatter import (
    PRAgentMarkdownReporter,
    PRTerminalFormatter,
    WIAgentMarkdownReporter,
    WITerminalFormatter,
)
from lib.pull_requests import PullRequestService
from lib.work_items import WorkItemService


def get_client(config: ToolConfig, org: Optional[str] = None, project: Optional[str] = None) -> AzureDevOpsClient:
    target_org = org or config.organization
    if not target_org:
        print("Error: Azure DevOps organization is not configured.", file=sys.stderr)
        print("Run 'python ado.py config --set organization=<URL>' or set ADO_ORGANIZATION env var.", file=sys.stderr)
        sys.exit(1)

    target_proj = project or config.project or None
    auth_provider = AzureCliAuthProvider()
    return AzureDevOpsClient(organization=target_org, project=target_proj, auth_provider=auth_provider)


def cmd_config(args: argparse.Namespace, config: ToolConfig) -> int:
    if args.set:
        for item in args.set:
            if "=" not in item:
                print(f"Error: Invalid configuration format '{item}'. Use key=value.", file=sys.stderr)
                return 1
            key, val = item.split("=", 1)
            key = key.strip()
            val = val.strip()

            if hasattr(config, key):
                if key == "projects":
                    config.projects = [p.strip() for p in val.split(",") if p.strip()]
                else:
                    setattr(config, key, val)
                print(f"Set {key} = {val}")
            else:
                print(f"Error: Unknown configuration key '{key}'.", file=sys.stderr)
                return 1

        if args.local:
            saved_path = config.save_local()
            print(f"Configuration saved locally to {saved_path}")
        else:
            saved_path = config.save_global()
            print(f"Configuration saved globally to {saved_path}")
        return 0

    # Display configuration
    print("Azure DevOps Skill Configuration:")
    print("-" * 50)
    print(f"Organization    : {config.organization or '(Not configured)'}")
    print(f"Default Project : {config.project or '(Not configured)'}")
    print(f"Projects List   : {', '.join(config.projects) if config.projects else '(Empty)'}")
    print(f"Author / User   : {config.get_author() or '(Not detected)'}")
    print(f"Download Dir    : {config.download_dir}")
    print(f"Output Dir      : {config.output_dir}")
    print("-" * 50)
    return 0


def cmd_pr(args: argparse.Namespace, config: ToolConfig) -> int:
    client = get_client(config, org=args.org, project=args.project)
    pr_service = PullRequestService(client)

    if args.list or not args.pr_id:
        author_filter = args.author.strip() if args.author else None
        creator_id = None

        current_user = pr_service.get_current_user()

        if args.mine:
            if current_user and current_user.get("id"):
                creator_id = current_user.get("id")
                author_filter = (
                    current_user.get("customDisplayName")
                    or current_user.get("providerDisplayName")
                    or config.get_author()
                )
            elif config.get_author():
                author_filter = config.get_author()

        projects_to_query = []
        if args.project:
            projects_to_query = [args.project]
        elif creator_id:
            projects_to_query = [None]
        elif config.projects:
            projects_to_query = list(config.projects)
        elif config.project:
            projects_to_query = [config.project]
        else:
            projects_to_query = [None]

        all_prs = []
        seen_ids = set()

        for proj in projects_to_query:
            try:
                prs = pr_service.list_pull_requests(project=proj, creator_id=creator_id)
                for p in prs:
                    if p.id not in seen_ids:
                        if not creator_id and author_filter and not p.matches_author(author_filter):
                            continue
                        seen_ids.add(p.id)
                        all_prs.append(p)
            except Exception as e:
                print(f"Warning: Failed querying PRs for project '{proj}': {str(e)}", file=sys.stderr)

        if args.json:
            out_list = [
                {
                    "id": p.id,
                    "title": p.title,
                    "author": p.created_by,
                    "project": p.project_name,
                    "repo": p.repository_name,
                    "source": p.source_branch,
                    "target": p.target_branch,
                    "url": p.web_url,
                }
                for p in all_prs
            ]
            print(json.dumps(out_list, indent=2))
        else:
            print(PRTerminalFormatter.format_pr_list(all_prs, author_filter=author_filter))
        return 0

    # Specific PR inspection
    pr_id = int(args.pr_id)
    try:
        pr = pr_service.get_pull_request(pr_id)
    except AdoError as e:
        print(f"Error fetching Pull Request #{pr_id}: {str(e)}", file=sys.stderr)
        return 1

    try:
        threads = pr_service.get_threads(
            pr_id=pr.id,
            repository_id=pr.repository_id,
            project=pr.project_name,
            active_only=not args.all,
        )
    except Exception as e:
        print(f"Warning: Error fetching review threads: {str(e)}", file=sys.stderr)
        threads = []

    if args.json:
        threads_data = [
            {
                "id": t.id,
                "status": t.status,
                "file_path": t.file_path,
                "line_start": t.line_start,
                "line_end": t.line_end,
                "comments": [
                    {
                        "author": c.author_name,
                        "date": c.published_date,
                        "content": c.content,
                    }
                    for c in t.human_comments
                ],
            }
            for t in threads
        ]
        out_data = {
            "id": pr.id,
            "title": pr.title,
            "project": pr.project_name,
            "repository": pr.repository_name,
            "source_branch": pr.source_branch,
            "target_branch": pr.target_branch,
            "author": pr.created_by,
            "url": pr.web_url,
            "threads": threads_data,
        }
        print(json.dumps(out_data, indent=2))
        return 0

    agent_prompt_md = PRAgentMarkdownReporter.generate_agent_prompt(
        pr=pr,
        threads=threads,
        active_only=not args.all,
    )

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(agent_prompt_md)
        print(f"Review prompt saved to: {out_path}")

    if args.for_agent:
        print(agent_prompt_md)
    else:
        print(PRTerminalFormatter.format_threads_terminal(pr, threads))

    return 0


def cmd_wi(args: argparse.Namespace, config: ToolConfig) -> int:
    client = get_client(config, org=args.org, project=args.project)
    wit_service = WorkItemService(client)

    if args.mine:
        try:
            items = wit_service.list_my_work_items(project=args.project or config.project)
        except Exception as e:
            print(f"Error querying assigned work items: {str(e)}", file=sys.stderr)
            return 1

        if args.json:
            out_list = [
                {
                    "id": item.id,
                    "title": item.title,
                    "state": item.state,
                    "type": item.work_item_type,
                    "project": item.project,
                    "assigned_to": item.assigned_to,
                    "attachments": len(item.attachments),
                }
                for item in items
            ]
            print(json.dumps(out_list, indent=2))
        else:
            print(WITerminalFormatter.format_work_item_list(items))
        return 0

    if not args.work_item_id:
        print("Error: Work Item ID or --mine required.", file=sys.stderr)
        return 1

    try:
        work_item_id = int(args.work_item_id)
        work_item = wit_service.get_work_item(work_item_id)
    except Exception as e:
        print(f"Error retrieving Work Item #{args.work_item_id}: {str(e)}", file=sys.stderr)
        return 1

    # Optional attachment download
    if args.download and work_item.attachments:
        target_dir = Path(args.output_dir or config.download_dir) / f"wi_{work_item.id}"
        print(f"Downloading {len(work_item.attachments)} attachments to {target_dir}...")
        downloaded = wit_service.download_attachments(work_item, target_dir)
        for d in downloaded:
            print(f"  - Downloaded: {d.name}")

    if args.json:
        out_data = {
            "id": work_item.id,
            "title": work_item.title,
            "state": work_item.state,
            "type": work_item.work_item_type,
            "project": work_item.project,
            "assigned_to": work_item.assigned_to,
            "description": work_item.description,
            "repro_steps": work_item.repro_steps,
            "tags": work_item.tags,
            "attachments": [{"name": a.name, "url": a.url} for a in work_item.attachments],
            "url": work_item.web_url,
        }
        print(json.dumps(out_data, indent=2))
        return 0

    if args.for_agent:
        md = WIAgentMarkdownReporter.generate_agent_prompt(work_item)
        print(md)
    else:
        print(WITerminalFormatter.format_work_item(work_item))

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(WIAgentMarkdownReporter.generate_agent_prompt(work_item))
        print(f"\nWork item document saved to: {out_path}")

    return 0


def cmd_download(args: argparse.Namespace, config: ToolConfig) -> int:
    client = get_client(config, org=args.org)
    dest_path = Path(args.output) if args.output else Path("./downloaded_file")

    print(f"Downloading from {args.url} to {dest_path}...")
    try:
        client.download_file(args.url, dest_path)
        print(f"Saved: {dest_path}")
        return 0
    except Exception as e:
        print(f"Download error: {str(e)}", file=sys.stderr)
        return 1


def cmd_reply(args: argparse.Namespace, config: ToolConfig) -> int:
    client = get_client(config, org=args.org, project=args.project)

    if args.type == "wi":
        wit_service = WorkItemService(client)
        try:
            wit_service.add_comment(int(args.id), args.comment)
            print(f"Successfully posted comment to Work Item #{args.id}.")
            return 0
        except Exception as e:
            print(f"Error posting comment to Work Item: {str(e)}", file=sys.stderr)
            return 1
    elif args.type == "pr":
        if not args.thread or not args.repo:
            print("Error: --thread and --repo are required when replying to a PR.", file=sys.stderr)
            return 1
        pr_service = PullRequestService(client)
        try:
            pr_service.reply_to_thread(
                pr_id=int(args.id),
                repository_id=args.repo,
                thread_id=int(args.thread),
                comment_text=args.comment,
                project=args.project,
            )
            print(f"Successfully posted reply to Thread #{args.thread} on PR #{args.id}.")
            return 0
        except Exception as e:
            print(f"Error posting reply to PR thread: {str(e)}", file=sys.stderr)
            return 1

    print(f"Error: Unsupported reply type '{args.type}'. Use 'wi' or 'pr'.", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ado",
        description="Azure DevOps CLI interface for coding agents and engineers (Zero-PAT policy).",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Config
    p_config = subparsers.add_parser("config", help="View or modify Azure DevOps configurations")
    p_config.add_argument("--set", action="append", help="Set key=value configuration item")
    p_config.add_argument("--local", action="store_true", help="Save configuration locally to .ado.json")

    # PR
    p_pr = subparsers.add_parser("pr", help="Inspect pull requests and review comments")
    p_pr.add_argument("pr_id", nargs="?", help="Pull Request ID to inspect")
    p_pr.add_argument("--list", action="store_true", help="List active pull requests")
    p_pr.add_argument("--mine", action="store_true", help="Filter pull requests created by current user")
    p_pr.add_argument("--author", help="Filter pull requests by author name, email, or alias")
    p_pr.add_argument("--project", help="Override Azure DevOps project")
    p_pr.add_argument("--org", help="Override Azure DevOps organization URL")
    p_pr.add_argument("--all", action="store_true", help="Include resolved and closed comment threads")
    p_pr.add_argument("--for-agent", action="store_true", help="Output agent-ready prompt directly to stdout")
    p_pr.add_argument("--json", action="store_true", help="Output raw JSON data")
    p_pr.add_argument("--out", help="Save markdown prompt to specified path")

    # Work Item
    p_wi = subparsers.add_parser("wi", help="Inspect work items and download attachments")
    p_wi.add_argument("work_item_id", nargs="?", help="Work Item ID")
    p_wi.add_argument("--mine", action="store_true", help="List active work items assigned to current user")
    p_wi.add_argument("--download", action="store_true", help="Download all attachments attached to work item")
    p_wi.add_argument("--for-agent", action="store_true", help="Output agent-ready prompt directly to stdout")
    p_wi.add_argument("--json", action="store_true", help="Output raw JSON data")
    p_wi.add_argument("--project", help="Override Azure DevOps project")
    p_wi.add_argument("--org", help="Override Azure DevOps organization URL")
    p_wi.add_argument("--output-dir", help="Directory where attachments should be downloaded")
    p_wi.add_argument("--out", help="Save markdown prompt to specified path")

    # Download
    p_dl = subparsers.add_parser("download", help="Stream download a file from Azure DevOps")
    p_dl.add_argument("url", help="Attachment download URL")
    p_dl.add_argument("--output", "-o", required=True, help="Destination local file path")
    p_dl.add_argument("--org", help="Override Azure DevOps organization URL")

    # Reply
    p_rep = subparsers.add_parser("reply", help="Submit a comment or reply")
    p_rep.add_argument("id", help="Target Work Item ID or Pull Request ID")
    p_rep.add_argument("--type", choices=["wi", "pr"], default="wi", help="Target type: wi or pr")
    p_rep.add_argument("--comment", required=True, help="Comment content text")
    p_rep.add_argument("--thread", help="Thread ID (required for PR replies)")
    p_rep.add_argument("--repo", help="Repository ID/Name (required for PR replies)")
    p_rep.add_argument("--project", help="Project name (required for PR replies)")
    p_rep.add_argument("--org", help="Override Azure DevOps organization URL")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    config = ToolConfig.load()

    try:
        if args.command == "config":
            return cmd_config(args, config)
        elif args.command == "pr":
            return cmd_pr(args, config)
        elif args.command == "wi":
            return cmd_wi(args, config)
        elif args.command == "download":
            return cmd_download(args, config)
        elif args.command == "reply":
            return cmd_reply(args, config)
    except AdoAuthError as e:
        print(f"\nAuthentication Error:\n{str(e)}", file=sys.stderr)
        return 1
    except AdoError as e:
        print(f"\nAzure DevOps API Error: {str(e)}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print(f"\nUnexpected Error: {str(e)}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
