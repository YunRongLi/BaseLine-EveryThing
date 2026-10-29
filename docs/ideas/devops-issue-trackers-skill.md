# Sibling Skills: Azure DevOps and Jira Issue Trackers

## Problem Statement
How might we enable coding agents to autonomously inspect issues, stream log attachments, parse review comments, and draft replies across enterprise Azure DevOps and Jira systems without hardcoded static secrets or tight coupling to domain log parsers?

## Recommended Direction
Implement two independent, sibling skills in `BaseLine-EveryThing/skills/`:
1. `azure-devops`: Focuses on Azure DevOps Work Items, attachment retrieval, PR review threads, and Azure CLI OAuth session authentication (Zero-PAT policy).
2. `jira`: Focuses on Jira Data Center/Cloud issues, attachment streaming, comments, and dynamic SSO/Bearer token resolution.

Both skills share identical CLI ergonomics, multi-tier configuration resolvers, and structured markdown outputs tailored for AI agents (`--for-agent`, `--markdown`, `--json`).

## Key Assumptions to Validate
- [ ] ADO Auth: Developers have an active `az login` session on their workstation.
- [ ] Jira Auth: Target Jira instance supports Bearer token authentication via corporate SSO session or dynamic credential helper.
- [ ] Attachment Streaming: Large log dumps (.tar.gz, .zip, .log) stream with chunked transfer and local checksum verification.

## MVP Scope

### Phase 1: Azure DevOps Skill (`skills/azure-devops`)
- Extract and package `azure_devops/` and `cli/config.py` from `obmc-dev-tool`.
- Create `scripts/ado.py` CLI supporting:
  - `ado pr --mine` and `ado pr <id> --for-agent`
  - `ado wi <id> [--for-agent]`
  - `ado download <attachment_url> --output <dir>`
  - `ado reply <id> --comment <text>`
- Create `SKILL.md` detailing agent usage, triggers, and workflows.
- Verify installation via `./skill-install.sh`.

### Phase 2: Jira Skill (`skills/jira`)
- Implement Jira counterpart leveraging the same HTTP client, config resolver, and attachment streamer.
- Create `scripts/jira.py` CLI supporting:
  - `jira issue <issue_key> [--for-agent]`
  - `jira issue --mine`
  - `jira download <attachment_id> --output <dir>`
  - `jira reply <issue_key> --comment <text>`
- Dynamic session auth provider supporting CLI session / credential helper command.
- Create `SKILL.md` for Jira operations.

## Not Doing (and Why)
- Monolithic Fusion: We will not combine ADO and Jira into a single bloated tool. Separate skills allow workspaces to load only the tracker relevant to their project.
- Log Parsing Coupling: OpenBMC log analysis remains decoupled from ticket fetching and attachment downloading.
- Hardcoded Secrets: No static passwords or tokens committed to git or plain configuration files.

## Open Questions
- What is the base URL and API version of your target Jira deployment (Atlassian Cloud `rest/api/3` or Jira Data Center / Server `rest/api/2`)?

