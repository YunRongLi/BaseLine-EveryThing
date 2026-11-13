# AI Agent Skills Installer

AGENT="antigravity"
SCOPE="global"
PLUGIN_NAME="baseline-everything"

# Parse arguments
while [ $# -gt 0 ]; do
    case $1 in
        antigravity|antigravity-ide|opencode) AGENT="$1" ;;
        global|workspace) SCOPE="$1" ;;
        --path=*) TARGET_PATH="${1#*=}" ;;
        --path) TARGET_PATH="$2"; shift ;;
        --plugin-name=*) PLUGIN_NAME="${1#*=}" ;;
        --plugin-name) PLUGIN_NAME="$2"; shift ;;
        -h|--help)
            echo "Usage: ./install.sh [AGENT] [SCOPE] [OPTIONS]"
            echo ""
            echo "Installs AI Agent skills from the current directory."
            echo ""
            echo "Arguments:"
            echo "  AGENT             Which agent format to target: antigravity, antigravity-ide, or opencode (default: antigravity)."
            echo "  SCOPE             Installation scope: global (default) or workspace."
            echo ""
            echo "Options:"
            echo "  --path=<path>     Specific location to install into when SCOPE is workspace."
            echo "  --plugin-name=<n> Name of the plugin bundle (default: baseline-everything)."
            echo "  -h, --help        Show this help message and exit."
            exit 0
            ;;
        *)
            echo "Error: Unknown argument '$1'"
            exit 1
            ;;
    esac
    shift
done

if [ "$SCOPE" = "workspace" ]; then
    if [ -n "$TARGET_PATH" ]; then
        # Ensure TARGET_PATH does not end with /
        PREFIX="${TARGET_PATH%/}/"
    else
        PREFIX=""
    fi

    case $AGENT in
        antigravity)
            BASE_DIR="${PREFIX}.agents/plugins/$PLUGIN_NAME"
            TARGET_SKILLS="$BASE_DIR/skills"
            LEGACY_SKILLS="${PREFIX}.agents/skills"
            ;;
        antigravity-ide)
            BASE_DIR="${PREFIX}.agents/plugins/$PLUGIN_NAME"
            TARGET_SKILLS="$BASE_DIR/skills"
            DIRECT_WORKSPACE_SKILLS="${PREFIX}.agents/skills"
            LEGACY_SKILLS="${PREFIX}.agents/skills"
            ;;
        opencode)
            BASE_DIR="${PREFIX}.opencode"
            TARGET_SKILLS="$BASE_DIR/skills"
            ;;
    esac
    echo "[Building] Installing for $AGENT into Workspace: $BASE_DIR"
else
    case $AGENT in
        antigravity)
            BASE_DIR="$HOME/.gemini/antigravity-cli/plugins/$PLUGIN_NAME"
            TARGET_SKILLS="$BASE_DIR/skills"
            DIRECT_GLOBAL_SKILLS="$HOME/.gemini/antigravity-cli/skills"
            SHARED_SKILLS="$HOME/.gemini/skills"
            ;;
        antigravity-ide)
            BASE_DIR="$HOME/.gemini/antigravity-ide/plugins/$PLUGIN_NAME"
            TARGET_SKILLS="$BASE_DIR/skills"
            DIRECT_GLOBAL_SKILLS="$HOME/.gemini/config/skills"
            SHARED_SKILLS="$HOME/.gemini/skills"
            ;;
        opencode)
            BASE_DIR="$HOME/.config/opencode"
            TARGET_SKILLS="$BASE_DIR/skills"
            ;;
    esac
    echo "[Global] Installing for $AGENT into Global: $BASE_DIR"
fi

# Create target directories
mkdir -p "$BASE_DIR"
if [ -n "$TARGET_SKILLS" ]; then
    mkdir -p "$TARGET_SKILLS"
fi

if [ "$SCOPE" = "workspace" ] && [ "$AGENT" = "antigravity" ]; then
    mkdir -p "$LEGACY_SKILLS"
elif [ "$SCOPE" = "workspace" ] && [ "$AGENT" = "antigravity-ide" ]; then
    mkdir -p "$LEGACY_SKILLS"
    mkdir -p "$DIRECT_WORKSPACE_SKILLS" 2>/dev/null || true
elif [ "$SCOPE" = "global" ] && { [ "$AGENT" = "antigravity" ] || [ "$AGENT" = "antigravity-ide" ]; }; then
    mkdir -p "$SHARED_SKILLS" 2>/dev/null || true
    mkdir -p "$DIRECT_GLOBAL_SKILLS" 2>/dev/null || true
fi

# Install Skills
if [ -n "$TARGET_SKILLS" ] && [ -d "skills" ]; then
    echo "[Packaging] Copying skills from ./skills to $TARGET_SKILLS..."
    cp -r skills/* "$TARGET_SKILLS/" 2>/dev/null || true
    if [ "$SCOPE" = "workspace" ] && [ "$AGENT" = "antigravity" ]; then
        cp -r skills/* "$LEGACY_SKILLS/" 2>/dev/null || true
    elif [ "$SCOPE" = "workspace" ] && [ "$AGENT" = "antigravity-ide" ]; then
        cp -r skills/* "$LEGACY_SKILLS/" 2>/dev/null || true
        # Flatten each skills/<DirName>/SKILL.md -> .agents/skills/<DirName>.md
        for skill_dir in skills/*/; do
            skill_name=$(basename "$skill_dir")
            skill_file="${skill_dir}SKILL.md"
            if [ -f "$skill_file" ]; then
                cp "$skill_file" "$DIRECT_WORKSPACE_SKILLS/${skill_name}.md" 2>/dev/null || true
            fi
        done
    elif [ "$SCOPE" = "global" ] && { [ "$AGENT" = "antigravity" ] || [ "$AGENT" = "antigravity-ide" ]; }; then
        cp -r skills/* "$SHARED_SKILLS/" 2>/dev/null || true
        cp -r skills/* "$DIRECT_GLOBAL_SKILLS/" 2>/dev/null || true
    fi
    echo "[OK] Skills installed."
elif [ -n "$TARGET_SKILLS" ]; then
    echo "[Info] No ./skills directory found."
fi

# Generate/Copy Plugin Manifests for Antigravity Agents
if [ "$AGENT" = "antigravity" ] || [ "$AGENT" = "antigravity-ide" ]; then
    if [ -f "plugin.json" ]; then
        cp "plugin.json" "$BASE_DIR/" 2>/dev/null || true
    else
        cat <<EOF > "$BASE_DIR/plugin.json"
{
  "name": "$PLUGIN_NAME",
  "version": "2.0.0",
  "description": "Centralized skills for Antigravity"
}
EOF
    fi
    if [ -f "mcp_config.json" ]; then
        cp "mcp_config.json" "$BASE_DIR/" 2>/dev/null || true
    fi
    if [ -f "hooks.json" ]; then
        cp "hooks.json" "$BASE_DIR/" 2>/dev/null || true
    fi
fi

echo "Done! $AGENT is now configured ($SCOPE scope)."
