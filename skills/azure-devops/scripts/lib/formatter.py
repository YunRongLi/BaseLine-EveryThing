"""
Reporters and formatters for Azure DevOps Work Items and Pull Request Reviews.
Generates terminal formatted outputs and agent-ready markdown prompts.
Strictly adheres to no-icons and no-emojis rules.
"""

from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List, Optional

try:
    from .pull_requests import PullRequest, PRThread, PRComment
    from .work_items import WorkItem, WorkItemAttachment
except ImportError:
    from pull_requests import PullRequest, PRThread, PRComment
    from work_items import WorkItem, WorkItemAttachment


def strip_html(html_str: str) -> str:
    """Removes HTML tags and cleans up entities for agent readability."""
    if not html_str:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", html_str)
    text = re.sub(r"</div>", "\n", text)
    text = re.sub(r"</p>", "\n\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


class PRTerminalFormatter:
    @staticmethod
    def format_pr_list(pull_requests: List[PullRequest], author_filter: Optional[str] = None) -> str:
        if not pull_requests:
            if author_filter:
                return f"No active pull requests found for author '{author_filter}'."
            return "No active pull requests found."

        lines = []
        lines.append(f"{'PR ID':<8} {'Project':<14} {'Repository':<22} {'Branch':<20} {'Author':<20} {'Title'}")
        lines.append("-" * 110)
        for pr in pull_requests:
            branch_info = f"{pr.source_branch} -> {pr.target_branch}"
            if len(branch_info) > 19:
                branch_info = branch_info[:16] + "..."
            lines.append(
                f"#{pr.id:<7} {pr.project_name:<14} {pr.repository_name:<22} {branch_info:<20} {pr.created_by:<20} {pr.title}"
            )
        return "\n".join(lines)

    @staticmethod
    def format_threads_terminal(pr: PullRequest, threads: List[PRThread]) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append(f"PULL REQUEST #{pr.id}: {pr.title}")
        lines.append("=" * 80)
        lines.append(f"Project   : {pr.project_name}")
        lines.append(f"Repository: {pr.repository_name}")
        lines.append(f"Branches  : {pr.source_branch} -> {pr.target_branch}")
        lines.append(f"Author    : {pr.created_by}")
        lines.append(f"Status    : {pr.status.upper()}")
        if pr.web_url:
            lines.append(f"Web URL   : {pr.web_url}")

        active_threads = [t for t in threads if t.is_active and t.human_comments]
        resolved_threads = [t for t in threads if not t.is_active and t.human_comments]

        lines.append(f"\nThreads   : {len(active_threads)} active, {len(resolved_threads)} resolved")
        lines.append("-" * 80)

        if not threads or (not active_threads and not resolved_threads):
            lines.append("No review comments found on this pull request.")
            return "\n".join(lines)

        for t in threads:
            comments = t.human_comments
            if not comments:
                continue

            loc = t.file_path or "Overall PR discussion"
            if t.line_start:
                if t.line_end and t.line_end != t.line_start:
                    loc += f" (Lines {t.line_start}-{t.line_end})"
                else:
                    loc += f" (Line {t.line_start})"

            status_tag = f"[{t.status.upper()}]"
            lines.append(f"\nThread #{t.id} {status_tag} - {loc}")
            lines.append("-" * 60)

            for c in comments:
                lines.append(f"  Author: {c.author_name} ({c.published_date})")
                for c_line in c.content.splitlines():
                    lines.append(f"    {c_line}")
                lines.append("")

        return "\n".join(lines)


class PRAgentMarkdownReporter:
    @staticmethod
    def generate_agent_prompt(
        pr: PullRequest,
        threads: List[PRThread],
        active_only: bool = True,
    ) -> str:
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines = []

        lines.append(f"# Code Review Feedback for PR #{pr.id}: {pr.title}")
        lines.append("")
        lines.append("## Overview")
        lines.append(f"- **Pull Request ID**: #{pr.id}")
        lines.append(f"- **Project**: {pr.project_name}")
        lines.append(f"- **Repository**: {pr.repository_name}")
        lines.append(f"- **Source Branch**: `{pr.source_branch}`")
        lines.append(f"- **Target Branch**: `{pr.target_branch}`")
        lines.append(f"- **Author**: {pr.created_by}")
        lines.append(f"- **Status**: `{pr.status}`")
        if pr.web_url:
            lines.append(f"- **Web URL**: {pr.web_url}")
        lines.append(f"- **Extracted**: {timestamp_str}")
        lines.append("")

        relevant_threads = [t for t in threads if (t.is_active or not active_only) and t.human_comments]

        lines.append("## Instructions for AI Coding Assistant")
        lines.append("Please analyze and address the review feedback below. For each review comment:")
        lines.append("1. Locate the file and specified lines in the repository.")
        lines.append("2. Understand the reviewer's concern or requirement.")
        lines.append("3. Implement the requested modification or provide an architectural clarification.")
        lines.append("4. Ensure all changes adhere to coding guidelines without introducing regressions.")
        lines.append("")

        if not relevant_threads:
            lines.append("### Review Status")
            lines.append("There are no unresolved review comments on this pull request.")
            return "\n".join(lines)

        lines.append(f"## Review Comments ({len(relevant_threads)} Thread{'s' if len(relevant_threads) > 1 else ''})")
        lines.append("")

        for idx, t in enumerate(relevant_threads, start=1):
            file_loc = t.file_path or "Global PR Discussion"
            line_info = ""
            if t.line_start:
                if t.line_end and t.line_end != t.line_start:
                    line_info = f":L{t.line_start}-L{t.line_end}"
                else:
                    line_info = f":L{t.line_start}"

            lines.append(f"### Item {idx}: `{file_loc}{line_info}` (Status: {t.status.upper()})")
            if t.file_path:
                lines.append(f"- **File**: `{t.file_path}`")
            if t.line_start:
                lines.append(f"- **Lines**: {t.line_start} - {t.line_end or t.line_start}")
            lines.append(f"- **Thread ID**: {t.id}")
            lines.append("- **Discussion**:")
            lines.append("")

            for c in t.human_comments:
                lines.append(f"  **{c.author_name}** ({c.published_date}):")
                for c_line in c.content.splitlines():
                    lines.append(f"  > {c_line}")
                lines.append("")

        return "\n".join(lines)


class WITerminalFormatter:
    @staticmethod
    def format_work_item_list(items: List[WorkItem]) -> str:
        if not items:
            return "No work items found."
        lines = []
        lines.append(f"{'ID':<8} {'Type':<12} {'State':<12} {'Project':<16} {'Assigned To':<20} {'Title'}")
        lines.append("-" * 100)
        for item in items:
            lines.append(
                f"#{item.id:<7} {item.work_item_type:<12} {item.state:<12} {item.project:<16} {item.assigned_to:<20} {item.title}"
            )
        return "\n".join(lines)

    @staticmethod
    def format_work_item(item: WorkItem) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append(f"WORK ITEM #{item.id}: {item.title}")
        lines.append("=" * 80)
        lines.append(f"Type        : {item.work_item_type}")
        lines.append(f"State       : {item.state}")
        lines.append(f"Project     : {item.project}")
        lines.append(f"Assigned To : {item.assigned_to}")
        if item.tags:
            lines.append(f"Tags        : {', '.join(item.tags)}")
        if item.web_url:
            lines.append(f"Web URL     : {item.web_url}")

        lines.append(f"\nAttachments : {len(item.attachments)}")
        for att in item.attachments:
            lines.append(f"  - {att.name} ({att.url})")

        cleaned_desc = strip_html(item.description)
        if cleaned_desc:
            lines.append("\nDescription:")
            for l in cleaned_desc.splitlines():
                lines.append(f"  {l}")

        cleaned_repro = strip_html(item.repro_steps)
        if cleaned_repro:
            lines.append("\nRepro Steps:")
            for l in cleaned_repro.splitlines():
                lines.append(f"  {l}")

        lines.append("=" * 80)
        return "\n".join(lines)


class WIAgentMarkdownReporter:
    @staticmethod
    def generate_agent_prompt(item: WorkItem) -> str:
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines = []

        lines.append(f"# Work Item #{item.id}: {item.title}")
        lines.append("")
        lines.append("## Overview")
        lines.append(f"- **ID**: #{item.id}")
        lines.append(f"- **Type**: `{item.work_item_type}`")
        lines.append(f"- **State**: `{item.state}`")
        lines.append(f"- **Project**: {item.project}")
        lines.append(f"- **Assigned To**: {item.assigned_to}")
        if item.tags:
            lines.append(f"- **Tags**: {', '.join(f'`{t}`' for t in item.tags)}")
        if item.web_url:
            lines.append(f"- **Web URL**: {item.web_url}")
        lines.append(f"- **Extracted**: {timestamp_str}")
        lines.append("")

        lines.append("## Instructions for AI Agent")
        lines.append("1. Examine the defect description and repro steps below.")
        lines.append("2. Inspect or download referenced attachments (logs, dumps) if available.")
        lines.append("3. Formulate root cause hypotheses and identify affected components.")
        lines.append("4. Propose a technical fix or triage draft adhering to system guidelines.")
        lines.append("")

        cleaned_desc = strip_html(item.description)
        if cleaned_desc:
            lines.append("## Description")
            lines.append(cleaned_desc)
            lines.append("")

        cleaned_repro = strip_html(item.repro_steps)
        if cleaned_repro:
            lines.append("## Repro Steps")
            lines.append(cleaned_repro)
            lines.append("")

        if item.attachments:
            lines.append(f"## Attachments ({len(item.attachments)})")
            for att in item.attachments:
                lines.append(f"- `{att.name}`")
                lines.append(f"  URL: {att.url}")
            lines.append("")

        return "\n".join(lines)

