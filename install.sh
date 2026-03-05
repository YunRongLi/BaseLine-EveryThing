# AI Agent Rules & Skills Installer

AGENT="antigravity"
SCOPE="global"
RULES="all"

# Parse arguments
while [ $# -gt 0 ]; do
    case $1 in
        antigravity|copilot|claude) AGENT="$1" ;;
        global|workspace) SCOPE="$1" ;;
        --rule=*|--rules=*) RULES="${1#*=}" ;;
        --rule|--rules) RULES="$2"; shift ;;
        --path=*) TARGET_PATH="${1#*=}" ;;
        --path) TARGET_PATH="$2"; shift ;;
        -h|--help)
            echo "Usage: ./install.sh [AGENT] [SCOPE] [OPTIONS]"
            echo ""
            echo "Installs AI Agent rules, skills, and workflows from the current directory."
            echo ""
            echo "Arguments:"
            echo "  AGENT             Which agent format to target: antigravity (default), copilot, or claude."
            echo "  SCOPE             Installation scope: global (default) or workspace."
            echo ""
            echo "Options:"
            echo "  --rules=<rules>   Comma-separated list of rule names to install. Defaults to 'all'."
            echo "  --path=<path>     Specific location to install into when SCOPE is workspace."
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
        antigravity)
            BASE_DIR="${PREFIX}.agents"
            TARGET_RULES="$BASE_DIR/rules"
            TARGET_SKILLS="$BASE_DIR/skills"
            ;;
        copilot)
            BASE_DIR="${PREFIX}.github"
            TARGET_RULES="$BASE_DIR"
            TARGET_SKILLS="$BASE_DIR/skills"
            ;;
        claude)
            BASE_DIR="${PREFIX}.claude"
            TARGET_RULES="$BASE_DIR/rules"
            TARGET_SKILLS="$BASE_DIR/skills"
            ;;
    esac
    echo "[Building] Installing for $AGENT into Workspace: $BASE_DIR"
else
    case $AGENT in
        antigravity)
            echo "[Error] Global installation is not supported for antigravity. Please use workspace scope." >&2
            exit 1
            ;;
        copilot)
            BASE_DIR="$HOME/.copilot"
            TARGET_RULES="$BASE_DIR"
            TARGET_SKILLS="$BASE_DIR/skills"
            ;;
        claude)
            BASE_DIR="$HOME/.claude"
            TARGET_RULES="$BASE_DIR/rules"
            TARGET_SKILLS="$BASE_DIR/skills"
            ;;
    esac
    echo "[Global] Installing for $AGENT into Global: $BASE_DIR"
fi

# Create target directories
mkdir -p "$TARGET_RULES"
mkdir -p "$TARGET_SKILLS"

# Install Rules
if [ -d "rules" ]; then
    echo "[Packaging] Copying rules from ./rules to $TARGET_RULES..."
    
    # Helper to check if rule should be copied
    should_copy_rule() {
        local file_name="${1##*/}"
        local base_name="${file_name%.*}"
        
        if [ "$AGENT" != "antigravity" ] && [ "$file_name" = "GEMINI.md" ]; then
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
    echo "[OK] Skills installed."
else
    echo "[Info] No ./skills directory found."
fi

# Install Workflows
TARGET_WORKFLOWS="$BASE_DIR/workflows"
if [ -d "workflows" ]; then
    mkdir -p "$TARGET_WORKFLOWS"
    echo "[Packaging] Copying workflows from ./workflows to $TARGET_WORKFLOWS..."
    cp -r workflows/* "$TARGET_WORKFLOWS/" 2>/dev/null || true
    echo "[OK] Workflows installed."
else
    echo "[Info] No ./workflows directory found."
fi

echo "Done! $AGENT is now configured ($SCOPE scope)."
