---
name: azure-devops
description: Enterprise Azure DevOps tool suite for inspecting PR review comments, querying work items, streaming log attachments, and submitting responses under strict Zero-PAT policies. Use when reviewing ADO PR comments, triaging ADO work items, or downloading logs.
---

# Azure DevOps Skill

This skill provides coding agents and developers with a zero-credential-leakage interface to Azure DevOps (ADO). It queries work items, streams attachments and logs, inspects pull request review threads, and posts review or triage responses.

Personal Access Tokens (PAT) are strictly prohibited. Authentication is exclusively handled via Azure CLI (`az login`) OAuth 2.0 Bearer tokens.

## 1. Prerequisites and Authentication

Ensure Azure CLI is installed on the host and an active session exists:
```bash
az login
```
The skill automatically acquires and refreshes short-lived tokens for the Azure DevOps well-known resource ID (`499b84ac-1321-427f-aa17-267ca6975798`).

## 2. Configuration

Configuration is resolved automatically in the following precedence order:
1. Environment variables (`ADO_ORGANIZATION`, `ADO_PROJECT`, `ADO_PROJECTS`, `ADO_AUTHOR`)
2. Local workspace configuration (`.ado.json` or `.obmc-tool.json`)
3. Global user configuration (`~/.config/azure-devops/config.json` or fallback `~/.config/obmc-dev-tool/config.json`)

To inspect or update configuration:
```bash
# View active configuration
python scripts/ado.py config

# Configure globally
python scripts/ado.py config --set organization=https://dev.azure.com/YourOrg
python scripts/ado.py config --set project=YourProject
python scripts/ado.py config --set projects=Dev,OpenBMC

# Configure locally for this workspace
python scripts/ado.py config --set project=OpenBMC --local
```

## 3. Pull Request Review Workflow

Use this workflow to address reviewer comments on active pull requests.

### Step 1: Discover Active PRs
```bash
# List all active PRs created by the user
python scripts/ado.py pr --mine

# List all active PRs across configured projects
python scripts/ado.py pr --list
```

### Step 2: Extract Review Comments for Agent
```bash
# Render agent-ready markdown prompt to stdout
python scripts/ado.py pr <pr_id> --for-agent

# Save prompt to output file
python scripts/ado.py pr <pr_id> --out ./output/pr_<pr_id>_review.md
```

### Step 3: Reply to a Review Comment
```bash
python scripts/ado.py reply <pr_id> --type pr --thread <thread_id> --repo <repo_name_or_id> --comment "Resolved in commit abc1234."
```

## 4. Work Item Triage Workflow

Use this workflow to inspect defects and download attached crash dumps or logs.

### Step 1: Query Work Items
```bash
# List active work items assigned to the current user
python scripts/ado.py wi --mine

# Inspect details of a specific work item
python scripts/ado.py wi <work_item_id> --for-agent
```

### Step 2: Download Attachments
```bash
# Automatically download all attachments linked to the work item
python scripts/ado.py wi <work_item_id> --download --output-dir ./downloads/

# Or stream download a specific file via URL
python scripts/ado.py download "<attachment_url>" --output ./downloads/journal.log
```

### Step 3: Post Triage Findings
```bash
python scripts/ado.py reply <work_item_id> --type wi --comment "Root cause analysis: detected memory leak in phosphor-pid-control."
```

## 5. Machine-Readable Output

Both `pr` and `wi` subcommands support the `--json` flag for scripting or structured tool pipelines:
```bash
python scripts/ado.py pr --mine --json
python scripts/ado.py wi 12345 --json
```

## 6. Sibling Skill Contract

This skill adheres to the shared DevOps Issue Tracker specification (`docs/ideas/devops-issue-trackers-skill.md`). Its Jira sibling skill provides identical subcommands (`jira issue`, `jira download`, `jira reply`).

