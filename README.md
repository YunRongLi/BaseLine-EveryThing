# BaseLine-EveryThing

A centralized repository for managing rules, skills, and workflows across multiple AI coding assistants, including Antigravity (Gemini), GitHub Copilot, and Claude Code.

## Features

- **Multi-Agent Support**: Unified configuration for Antigravity, GitHub Copilot, and Claude Code.
- **Rules Management**: Centralized storage for architectural standards and coding guidelines.
- **Workflow Automation**: Standardized processes for common tasks like git operations.
- **Cross-Platform Installers**: Robust installation scripts for both Windows (PowerShell) and Linux/macOS (Bash).

## Directory Structure

```text
.
├── rules/              # Global and project-specific rules
│   ├── GEMINI.md       # Global Antigravity overrides
│   └── engineer/       # Technical guidelines (Architectural, C++, etc.)
├── skills/             # Custom agent skills (Antigravity/Copilot/Claude)
├── workflows/          # Standardized operational workflows (e.g., git)
├── install.ps1         # Windows installer
└── install.sh          # Linux/macOS installer
```

## Installation

### PowerShell (Windows)
```powershell
# Default: Antigravity in Global scope
.\install.ps1

# Specific Agent & Scope
.\install.ps1 -Agent copilot -Scope workspace
```

### Bash (Linux/macOS)
```bash
# Default: Antigravity in Global scope
./install.sh

# Specific Agent & Scope
./install.sh claude workspace
```

## Workflows

### Git Workflow
This repository follows a specific git commit format as defined in `workflows/git-workflow.md`:
- `feat`: New features
- `fix`: Bug fixes
- `update`: Refactor or existing code updates

## License
MIT (or your preferred license)
