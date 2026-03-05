# BaseLine-EveryThing

A centralized repository for managing rules, skills, and workflows across multiple AI coding assistants, including Antigravity (Gemini), GitHub Copilot, and Claude Code.

## Features

- **Multi-Agent Support**: Unified configuration for Antigravity, GitHub Copilot, and Claude Code.
- **Rules Management**: Centralized storage for architectural standards, coding guidelines, and document conventions (e.g., Obsidian).
- **Workflow Automation**: Standardized processes for common tasks like git operations.
- **Cross-Platform Installers**: Robust installation scripts for both Windows (PowerShell) and Linux/macOS (Bash).

## Directory Structure

```text
.
├── rules/              # Global and project-specific rules
│   ├── GEMINI.md       # Global Antigravity overrides
│   ├── document/       # Documentation standards (Obsidian, etc.)
│   └── engineer/       # Technical guidelines (Architectural, C++, etc.)
├── skills/             # Custom agent skills (External capabilities)
├── workflows/          # Standardized operational workflows (e.g., git)
├── install.ps1         # Windows installer
└── install.sh          # Linux/macOS installer
```

## Installation

### PowerShell (Windows)
```powershell
# Antigravity (Workspace only)
.\install.ps1 -Agent antigravity -Scope workspace

# Copilot (Global)
.\install.ps1 -Agent copilot -Scope global
```

### Bash (Linux/macOS)
```bash
# Antigravity (Workspace only)
./install.sh antigravity workspace

# Claude (Global)
./install.sh claude global
```

## Workflows

### Git Workflow
This repository follows a specific git commit format as defined in `workflows/git-workflow.md`:
- `feat`: New features
- `fix`: Bug fixes
- `update`: Refactor or existing code updates

## License
MIT
