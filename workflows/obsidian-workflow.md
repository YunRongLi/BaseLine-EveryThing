# Obsidian Automation Workflow (CLI-Focused)

This workflow defines the standard process for integrating AI Agent (Antigravity) with a local Obsidian vault using **Obsidian CLI** as the primary interface for automation.

## 1. Setup & Requirements

### 1.1. Prerequisite: Obsidian CLI
Ensure `obsidian-cli` is installed and the Obsidian application is running.
- **Install**: `npm install -g obsidian-cli` (or relevant package).
- **Verify**: Run `obsidian vault` to check connection to the active vault.

### 1.2. Integration Methods
- **Method A (CLI Direct)**: Use `obsidian` commands to create and manage notes.
- **Method B (Vault Context)**: Add the Obsidian vault as a root folder in the IDE for background context, but use CLI for active interactions.

## 2. Operation Procedures (via obsidian-cli)

### 2.1. Processing the Inbox
1. **Command**: `/obsidian process-inbox`
2. **AI Action**: 
   - Scans the `Inbox/` directory.
   - For each file, runs: `obsidian create name="target_name.md" path="target/folder" content="processed content"`.
   - Cleans up the inbox after confirmation.

### 2.2. Dynamic Note Creation
To save current session insights:
1. **Instruction**: "AI, save this summary to Obsidian."
2. **CLI Call**: `obsidian create name="Current_Task.md" path="10_Projects" content="# Summary\n..." overwrite`
3. **Best Practice**: Use `obsidian open file="Current_Task.md"` to show the result to the user immediately.

### 2.3. Appending to Daily Notes or Logs
To update an existing project log:
1. **Instruction**: "Add this update to my Project Log."
2. **CLI Call**: `obsidian append file="Project_Log.md" content="- [ ] Update from [Timestamp]"`

### 2.4. Task Management
To sync code TODOs:
1. **Instruction**: "Sync TODOs to Obsidian."
2. **CLI Call**: `obsidian append file="Global_Todo.md" content="### From Codebase\n[ ] Task detail"`

## 3. Best Practices & Constraints
- **No Icons**: Strictly follow the project override; avoid emojis in CLI-generated titles or content.
- **Vault Targeting**: If multiple vaults exist, always specify `vault="VaultName"`.
- **Formatting**: Ensure content passed to CLI is properly escaped for shell execution. Use key=value pairs (e.g., `name="note.md"`, `content="text"`).
- **PARA Consistency**: Use the PARA folder structure within all `obsidian create` path arguments.
- **Safety**: AI MUST ask for explicit user confirmation before executing any `delete` command.
