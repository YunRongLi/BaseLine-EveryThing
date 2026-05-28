# AI Agent Rules & Skills Installer

AGENT="antigravity"
SCOPE="global"
RULES="all"
PLUGIN_NAME="baseline-everything"

# Parse arguments
while [ $# -gt 0 ]; do
    case $1 in
        antigravity|antigravity-ide|copilot|claude) AGENT="$1" ;;
        global|workspace) SCOPE="$1" ;;
        --rule=*|--rules=*) RULES="${1#*=}" ;;
        --rule|--rules) RULES="$2"; shift ;;
        --path=*) TARGET_PATH="${1#*=}" ;;
        --path) TARGET_PATH="$2"; shift ;;
        --plugin-name=*) PLUGIN_NAME="${1#*=}" ;;
        --plugin-name) PLUGIN_NAME="$2"; shift ;;
        -h|--help)
            echo "Usage: ./install.sh [AGENT] [SCOPE] [OPTIONS]"
            echo ""
            echo "Installs AI Agent rules, skills, and workflows from the current directory."
            echo ""
            echo "Arguments:"
            echo "  AGENT             Which agent format to target: antigravity, antigravity-ide, copilot, or claude (default: antigravity)."
            echo "  SCOPE             Installation scope: global (default) or workspace."
            echo ""
            echo "Options:"
            echo "  --rules=<rules>   Comma-separated list of rule names to install. Defaults to 'all'."
            echo "  --path=<path>     Specific location to install into when SCOPE is workspace."
            echo "  --plugin-name=<n> Name of the plugin bundle (default: baseline-everything)."
            echo "  -h, --help        Show this help message and exit."
            exit 0
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
        antigravity|antigravity-ide)
            BASE_DIR="${PREFIX}.agents/plugins/$PLUGIN_NAME"
            TARGET_RULES="$BASE_DIR/rules"
            TARGET_SKILLS="$BASE_DIR/skills"
            TARGET_WORKFLOWS="$BASE_DIR/workflows"
            LEGACY_RULES="${PREFIX}.agents/rules"
            LEGACY_SKILLS="${PREFIX}.agents/skills"
            LEGACY_WORKFLOWS="${PREFIX}.agents/workflows"
            ;;
        copilot)
            BASE_DIR="${PREFIX}.github"
            TARGET_RULES="$BASE_DIR"
            TARGET_SKILLS="$BASE_DIR/skills"
            TARGET_WORKFLOWS="$BASE_DIR/workflows"
            ;;
        claude)
            BASE_DIR="${PREFIX}.claude"
            TARGET_RULES="$BASE_DIR/rules"
            TARGET_SKILLS="$BASE_DIR/skills"
            TARGET_WORKFLOWS="$BASE_DIR/workflows"
            ;;
    esac
    echo "[Building] Installing for $AGENT into Workspace: $BASE_DIR"
else
    case $AGENT in
        antigravity)
            BASE_DIR="$HOME/.gemini/antigravity-cli/plugins/$PLUGIN_NAME"
            TARGET_RULES="$BASE_DIR/rules"
            TARGET_SKILLS="$BASE_DIR/skills"
            TARGET_WORKFLOWS="$BASE_DIR/workflows"
            DIRECT_GLOBAL_RULES="$HOME/.gemini/antigravity-cli/rules"
            DIRECT_GLOBAL_SKILLS="$HOME/.gemini/antigravity-cli/skills"
            DIRECT_GLOBAL_WORKFLOWS="$HOME/.gemini/antigravity-cli/workflows"
            SHARED_RULES="$HOME/.gemini/rules"
            SHARED_SKILLS="$HOME/.gemini/skills"
            SHARED_WORKFLOWS="$HOME/.gemini/workflows"
            ;;
        antigravity-ide)
            BASE_DIR="$HOME/.gemini/antigravity-ide/plugins/$PLUGIN_NAME"
            TARGET_RULES="$BASE_DIR/rules"
            TARGET_SKILLS="$BASE_DIR/skills"
            TARGET_WORKFLOWS="$BASE_DIR/workflows"
            DIRECT_GLOBAL_RULES="$HOME/.gemini/antigravity-ide/rules"
            DIRECT_GLOBAL_SKILLS="$HOME/.gemini/antigravity-ide/skills"
            DIRECT_GLOBAL_WORKFLOWS="$HOME/.gemini/antigravity-ide/workflows"
            SHARED_RULES="$HOME/.gemini/rules"
            SHARED_SKILLS="$HOME/.gemini/skills"
            SHARED_WORKFLOWS="$HOME/.gemini/workflows"
            ;;
        copilot)
            BASE_DIR="$HOME/.copilot"
            TARGET_RULES="$BASE_DIR"
            TARGET_SKILLS="$BASE_DIR/skills"
            TARGET_WORKFLOWS="$BASE_DIR/workflows"
            ;;
        claude)
            BASE_DIR="$HOME/.claude"
            TARGET_RULES="$BASE_DIR/rules"
            TARGET_SKILLS="$BASE_DIR/skills"
            TARGET_WORKFLOWS="$BASE_DIR/workflows"
            ;;
    esac
    echo "[Global] Installing for $AGENT into Global: $BASE_DIR"
fi

# Create target directories
mkdir -p "$BASE_DIR"
mkdir -p "$TARGET_RULES"
mkdir -p "$TARGET_SKILLS"
mkdir -p "$TARGET_WORKFLOWS"
if [ "$SCOPE" = "workspace" ] && { [ "$AGENT" = "antigravity" ] || [ "$AGENT" = "antigravity-ide" ]; }; then
    mkdir -p "$LEGACY_RULES"
    mkdir -p "$LEGACY_SKILLS"
    mkdir -p "$LEGACY_WORKFLOWS"
elif [ "$SCOPE" = "global" ] && { [ "$AGENT" = "antigravity" ] || [ "$AGENT" = "antigravity-ide" ]; }; then
    mkdir -p "$SHARED_RULES" 2>/dev/null || true
    mkdir -p "$SHARED_SKILLS" 2>/dev/null || true
    mkdir -p "$SHARED_WORKFLOWS" 2>/dev/null || true
    mkdir -p "$DIRECT_GLOBAL_RULES" 2>/dev/null || true
    mkdir -p "$DIRECT_GLOBAL_SKILLS" 2>/dev/null || true
    mkdir -p "$DIRECT_GLOBAL_WORKFLOWS" 2>/dev/null || true
fi

# Install Rules
if [ -d "rules" ]; then
    echo "[Packaging] Copying rules from ./rules to $TARGET_RULES..."
    
    # Helper to check if rule should be copied
    should_copy_rule() {
        local file_name="${1##*/}"
        local base_name="${file_name%.*}"
        
        if [ "$AGENT" != "antigravity" ] && [ "$AGENT" != "antigravity-ide" ] && [ "$file_name" = "GEMINI.md" ]; then
            return 1
        fi
        
        if [ "$RULES" = "all" ]; then
            return 0
        fi
        
        IFS=','
        for r in $RULES; do
            if [ "$r" = "$file_name" ] || [ "$r" = "$base_name" ]; then
                return 0
            fi
        done
        return 1
    }

    find rules -type f -name "*.md" | while read -r rule_file; do
        if should_copy_rule "$rule_file"; then
            cp "$rule_file" "$TARGET_RULES/" 2>/dev/null || true
            if [ "$SCOPE" = "workspace" ] && { [ "$AGENT" = "antigravity" ] || [ "$AGENT" = "antigravity-ide" ]; }; then
                cp "$rule_file" "$LEGACY_RULES/" 2>/dev/null || true
            elif [ "$SCOPE" = "global" ] && { [ "$AGENT" = "antigravity" ] || [ "$AGENT" = "antigravity-ide" ]; }; then
                cp "$rule_file" "$SHARED_RULES/" 2>/dev/null || true
                cp "$rule_file" "$DIRECT_GLOBAL_RULES/" 2>/dev/null || true
            fi
        fi
    done
    
    echo "[OK] Rules installed."
else
    echo "[Warning] No ./rules directory found."
fi

# Install Skills
if [ -d "skills" ]; then
    echo "[Packaging] Copying skills from ./skills to $TARGET_SKILLS..."
    cp -r skills/* "$TARGET_SKILLS/" 2>/dev/null || true
    if [ "$SCOPE" = "workspace" ] && { [ "$AGENT" = "antigravity" ] || [ "$AGENT" = "antigravity-ide" ]; }; then
        cp -r skills/* "$LEGACY_SKILLS/" 2>/dev/null || true
    elif [ "$SCOPE" = "global" ] && { [ "$AGENT" = "antigravity" ] || [ "$AGENT" = "antigravity-ide" ]; }; then
        cp -r skills/* "$SHARED_SKILLS/" 2>/dev/null || true
        cp -r skills/* "$DIRECT_GLOBAL_SKILLS/" 2>/dev/null || true
    fi
    echo "[OK] Skills installed."
else
    echo "[Info] No ./skills directory found."
fi

# Install Workflows
if [ -d "workflows" ]; then
    echo "[Packaging] Copying workflows from ./workflows to $TARGET_WORKFLOWS..."
    cp -r workflows/* "$TARGET_WORKFLOWS/" 2>/dev/null || true
    if [ "$SCOPE" = "workspace" ] && { [ "$AGENT" = "antigravity" ] || [ "$AGENT" = "antigravity-ide" ]; }; then
        cp -r workflows/* "$LEGACY_WORKFLOWS/" 2>/dev/null || true
    elif [ "$SCOPE" = "global" ] && { [ "$AGENT" = "antigravity" ] || [ "$AGENT" = "antigravity-ide" ]; }; then
        cp -r workflows/* "$SHARED_WORKFLOWS/" 2>/dev/null || true
        cp -r workflows/* "$DIRECT_GLOBAL_WORKFLOWS/" 2>/dev/null || true
    fi
    echo "[OK] Workflows installed."
else
    echo "[Info] No ./workflows directory found."
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
  "description": "Centralized rules, skills, and workflows for Antigravity"
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
