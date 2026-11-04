---
name: azure-devops
description: Enterprise Azure DevOps tool suite for inspecting PR review comments, querying work items, streaming log attachments, and submitting responses under strict Zero-PAT policies. Use when reviewing ADO PR comments, triaging ADO work items, or downloading logs across multiple enterprise domains.
---

# Azure DevOps Skill

This skill provides coding agents and developers with a zero-credential-leakage interface to Azure DevOps (ADO). It queries work items, streams attachments and logs, inspects pull request review threads, and posts review or triage responses across single or multi-domain environments.

Personal Access Tokens (PAT) are strictly prohibited. Authentication is exclusively handled via Azure CLI (`az login`) OAuth 2.0 Bearer tokens.

## 1. Prerequisites and Authentication

Ensure Azure CLI is installed on the host and an active session exists:
```bash
az login
```
The skill automatically acquires and refreshes short-lived tokens via Azure CLI, supporting multi-tenant isolation and custom Azure configuration contexts (`AZURE_CONFIG_DIR`).

## 2. Configuration

Configuration is resolved automatically in the following precedence order:
1. Environment variables (`ADO_PROFILE`, `ADO_ORGANIZATION`, `ADO_PROJECT`, `ADO_PROJECTS`, `ADO_AUTHOR`, `AZURE_CONFIG_DIR`)
2. Local workspace configuration (`.ado.json`)
3. Global user configuration (`~/.config/azure-devops/config.json`)

### Inspect Configuration
```bash
# View active configuration
python scripts/ado.py config

# View specific profile configuration
python scripts/ado.py config --profile secondary
```

### Single-Domain Setup
```bash
# Configure globally
python scripts/ado.py config --set organization=https://dev.azure.com/OrganizationA
python scripts/ado.py config --set project=ProjectAlpha
python scripts/ado.py config --set projects=ProjectAlpha,ProjectBeta

# Configure locally for this workspace
python scripts/ado.py config --set project=ProjectAlpha --local
```

### Multi-Domain / Multi-Profile Setup
Configure independent profiles for distinct organizations or tenants:
```bash
# Configure primary profile
python scripts/ado.py config --profile primary --set organization=https://dev.azure.com/OrganizationA
python scripts/ado.py config --profile primary --set project=ProjectAlpha
python scripts/ado.py config --profile primary --set projects=ProjectAlpha,ProjectBeta
python scripts/ado.py config --profile primary --set azure_config_dir=~/.azure-primary

# Configure secondary profile
python scripts/ado.py config --profile secondary --set organization=https://OrganizationB.visualstudio.com
python scripts/ado.py config --profile secondary --set project=ProjectGamma
python scripts/ado.py config --profile secondary --set projects=ProjectGamma,ProjectDelta
python scripts/ado.py config --profile secondary --set azure_config_dir=~/.azure-secondary

# Set active profile
python scripts/ado.py config --set active_profile=primary
```

Profile resolution automatically switches when:
* An explicit `--profile <name>` flag is passed.
* The target `--project <name>` belongs to a configured profile's projects.
* The active shell has `$AZURE_CONFIG_DIR` pointing to a profile's Azure configuration directory.
* Contextual heuristics match: the current workspace directory name or active git remote URL matches a configured profile or organization.
* Fallback: If `active_profile` is unset or 'default', the first configured profile with a valid organization is used automatically.

## 3. Pull Request Review Workflow

Use this workflow to discover active pull requests and inspect reviewer comments.

### Step 1: Discover Active PRs
```bash
# List active PRs created by the user (authored)
python scripts/ado.py pr --mine

# List active PRs where the user is assigned as a reviewer
python scripts/ado.py pr --assigned

# List active PRs filtered by a specific reviewer name or alias
python scripts/ado.py pr --reviewer "Alice"

# Query PRs across a specific profile or project
python scripts/ado.py pr --profile secondary --assigned
python scripts/ado.py pr --project ProjectGamma --assigned

# List all active PRs across configured projects
python scripts/ado.py pr --list
```

### Step 2: Inspect PR Summary and Review Threads
```bash
# View full PR summary (description, reviewers/votes, changed files, commits, threads)
python scripts/ado.py pr <pr_id>

# View concise tabular summary of all review threads
python scripts/ado.py pr <pr_id> --compact

# View only review threads and comments (skips commits and changed files)
python scripts/ado.py pr <pr_id> --comments

# Filter review threads to only human comments (excludes automated bot noise)
python scripts/ado.py pr <pr_id> --human

# Filter review threads to only automated bot/scanner findings
python scripts/ado.py pr <pr_id> --bots

# Combine filters (e.g. compact summary of human reviews only)
python scripts/ado.py pr <pr_id> --human --compact

# Render agent-ready markdown prompt to stdout
python scripts/ado.py pr <pr_id> --for-agent

# Save prompt to output file
python scripts/ado.py pr <pr_id> --out ./output/pr_<pr_id>_review.md
```

### Step 3: Reply to a Review Comment and Vote
```bash
# Reply to a review thread (auto-resolves repository)
python scripts/ado.py pr <pr_id> --reply "Addressed in commit abc1234." --thread <thread_id>

# Reply and mark thread as resolved/fixed
python scripts/ado.py pr <pr_id> --reply "Resolved." --thread <thread_id> --resolve

# Cast reviewer vote (approve, suggestions, wait, reject, reset)
python scripts/ado.py pr <pr_id> --vote approve

# Sibling command format
python scripts/ado.py reply <pr_id> --type pr --thread <thread_id> --comment "Resolved in commit abc1234." --resolve

## 4. Work Item Triage Workflow

Use this workflow to inspect defects and download attached crash dumps or logs.

### Step 1: Query Work Items
```bash
# List active work items assigned to the current user
python scripts/ado.py wi --mine

# List active bugs assigned to current user
python scripts/ado.py wi --mine --type Bug

# List active bugs assigned to current user under a specific project
python scripts/ado.py wi --mine --project ProjectAlpha --type Bug

# Inspect details, repro steps, related work item links, and discussion comments
python scripts/ado.py wi <work_item_id> --for-agent

# View formatted work item details and discussion in terminal
python scripts/ado.py wi <work_item_id>
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
python scripts/ado.py reply <work_item_id> --type wi --comment "Root cause analysis: detected memory leak in core service component."
```

## 5. Machine-Readable Output

Both `pr` and `wi` subcommands support the `--json` flag for scripting or structured tool pipelines:
```bash
python scripts/ado.py pr --assigned --json
python scripts/ado.py wi 12345 --json
```

## 6. Sibling Skill Contract

This skill adheres to the shared DevOps Issue Tracker specification. Its Jira sibling skill provides identical subcommands (`jira issue`, `jira download`, `jira reply`).
