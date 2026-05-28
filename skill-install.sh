#!/bin/bash

# skill-install.sh
# A script to install a skill from the workspace to a specified location.

function show_help() {
    echo "Usage: $0 [options] <skill_name>"
    echo ""
    echo "Options:"
    echo "  -w, --workspace    Install to Workspace (~/.agents/skills/{skill_name}/)"
    echo "  -g, --global       Install to Global (~/.gemini/antigravity-cli/skills/{skill_name}/)"
    echo "  -s, --shared       Install to Shared (~/.gemini/skills/{skill_name}/)"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "If no location option is provided, an interactive prompt will be displayed."
}

LOCATION=""
SKILL_INPUT=""

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -w|--workspace) LOCATION="workspace"; shift ;;
        -g|--global) LOCATION="global"; shift ;;
        -s|--shared) LOCATION="shared"; shift ;;
        -h|--help) show_help; exit 0 ;;
        -*) echo "Error: Unknown parameter passed: $1"; show_help; exit 1 ;;
        *)
            if [[ -z "$SKILL_INPUT" ]]; then
                SKILL_INPUT="$1"
            else
                echo "Error: Multiple skill names provided. Only one is supported."
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

if [[ -z "$SKILL_INPUT" ]]; then
    echo "Error: Skill name is required."
    show_help
    exit 1
fi

# Extract the base name in case the user provides a path like skills/my-skill
SKILL_NAME=$(basename "$SKILL_INPUT")

# Determine the workspace directory relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$SCRIPT_DIR/skills/$SKILL_NAME"

if [[ ! -d "$SKILL_DIR" ]]; then
    echo "Error: Skill directory not found at $SKILL_DIR"
    exit 1
fi

if [[ ! -f "$SKILL_DIR/SKILL.md" ]]; then
    echo "Error: SKILL.md not found in $SKILL_DIR"
    exit 1
fi

if [[ -z "$LOCATION" ]]; then
    echo "Please choose the installation destination for the skill '$SKILL_NAME':"
    echo "  1) Workspace (~/.agents/skills/$SKILL_NAME/)"
    echo "  2) Global    (~/.gemini/antigravity-cli/skills/$SKILL_NAME/)"
    echo "  3) Shared    (~/.gemini/skills/$SKILL_NAME/)"
    read -p "Enter choice [1-3]: " choice
    case $choice in
        1) LOCATION="workspace" ;;
        2) LOCATION="global" ;;
        3) LOCATION="shared" ;;
        *) echo "Error: Invalid choice."; exit 1 ;;
    esac
fi

case $LOCATION in
    workspace)
        DEST_DIR=~/.agents/skills/$SKILL_NAME
        ;;
    global)
        DEST_DIR=~/.gemini/antigravity-cli/skills/$SKILL_NAME
        ;;
    shared)
        DEST_DIR=~/.gemini/skills/$SKILL_NAME
        ;;
esac

echo "Installing $SKILL_NAME to $DEST_DIR..."

mkdir -p "$DEST_DIR"
cp -r "$SKILL_DIR"/. "$DEST_DIR/"

if [[ $? -eq 0 ]]; then
    echo "Successfully installed $SKILL_NAME."
else
    echo "Error: Failed to install $SKILL_NAME."
    exit 1
fi
