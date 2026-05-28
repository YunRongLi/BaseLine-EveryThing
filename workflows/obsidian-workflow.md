# Obsidian Automation Workflow (CLI-Focused)

This workflow defines the standard process for integrating the AI Agent (Antigravity) with a local Obsidian vault, utilizing the `obsidian-cli` tool and the Python scripts provided in the `obsidian-cli` global skill.

## 1. Setup & Requirements

### 1.1. Prerequisites
- **Official Obsidian App**: Must be installed. Used for vault status checking and background execution (via `--hidden` flag).
- **Community obsidian-cli**: The third-party CLI tool used for safe file operations (`create`, `append`).
- **Global Skill**: The automation scripts (`main.py`, `cli_wrapper.py`, `classifier.py`, `indexer.py`) are located in `~/.gemini/skills/obsidian-cli/`.

### 1.2. Configuration
The Python wrapper requires two paths configured:
- `vault_path`: The absolute path to the local Obsidian vault.
- `obsidian_app_path`: The path to the official Obsidian executable.

## 2. Operation Procedures

The standard AI automation pipeline follows the flow defined in the `obsidian-cli` skill's `main.py`:

### 2.1. Initialization and Indexing
1. **Vault Connection**: Start Obsidian in the background (`--hidden`) and verify vault status.
2. **Indexing**: Run the `indexer.py` (ContentMapIndexer) to scan the vault structure and build a content map.

### 2.2. Processing the Inbox (Classification)
When processing raw notes from `00_Inbox/`:
1. **Classification**: Analyze the content (via `classifier.py`) and determine the category (Action, Context, Reference) and the specific Note Type (Thing, Statement, Question, Quote, Person).
2. **Formatting**: 
   - Apply YAML properties based on the Note Type (e.g., `origin` for Statements, `topic` for MOCs).
   - Format action items in `> [!todo]` blocks with `- [ ]` checkboxes.
   - Format caveats in `> [!warning]` blocks.
3. **Routing (ACE Framework)**: Determine the target folder based on classification:
   - Action -> `03_Efforts/Projects`
   - Context -> `01_Atlas/Contexts`
   - Reference -> `01_Atlas/Resources`
4. **Creation**: Use the CLI wrapper (`obsidian-cli create --path <path> --content <content>`) to save the note. Filenames must be sanitized to avoid special characters.

### 2.3. Content Map (MOC) Synthesis
To prevent orphaned notes and support bottom-up growth:
1. **Find MOC**: Query the indexer to find the most relevant existing Map of Content (MOC).
2. **Append Link**: Automatically update the related MOC by appending a wikilink to the newly created note (e.g., `obsidian-cli append --path <moc_path> --content "- [[New Note]] : Summary"`).
3. **Incremental Update**: Refresh the internal index with the new link.

## 3. Best Practices & Constraints
- **Command Injection Prevention**: Always pass paths and content as discrete arguments, utilizing the `cli_wrapper.py` functions to safely interface with the OS.
- **No Icons**: Strictly follow the project override; avoid emojis in CLI-generated titles, properties, or content.
- **ACE Consistency**: Adhere strictly to the ACE (01_Atlas, 02_Calendar, 03_Efforts) and 00_Inbox folder framework. Do not create deep category hierarchies.
- **Safety**: The AI MUST ask for explicit user confirmation before executing any `delete` commands or performing batch destructive operations.
