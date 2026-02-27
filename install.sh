# AI Agent Rules & Skills Installer

AGENT="antigravity"
SCOPE="global"

# Parse arguments
for arg in "$@"; do
    case $arg in
        antigravity|copilot|claude) AGENT="$arg" ;;
        global|workspace) SCOPE="$arg" ;;
    esac
done

if [ "$SCOPE" = "workspace" ]; then
    case $AGENT in
        antigravity)
            BASE_DIR=".agent"
            TARGET_RULES="$BASE_DIR/rules"
            TARGET_SKILLS="$BASE_DIR/skills"
            ;;
        copilot)
            BASE_DIR=".github"
            TARGET_RULES="$BASE_DIR"
            TARGET_SKILLS="$BASE_DIR/skills"
            ;;
        claude)
            BASE_DIR=".claude"
            TARGET_RULES="$BASE_DIR/rules"
            TARGET_SKILLS="$BASE_DIR/skills"
            ;;
    esac
    echo "[Building] Installing for $AGENT into Workspace: $BASE_DIR"
else
    case $AGENT in
        antigravity)
            BASE_DIR="$HOME/.gemini"
            TARGET_RULES="$BASE_DIR"
            TARGET_SKILLS="$BASE_DIR/antigravity/skills"
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
    if [ "$AGENT" = "antigravity" ] && [ "$SCOPE" = "global" ]; then
        echo "[Packaging] Installing Antigravity global rules..."
        if [ -f "rules/GEMINI.md" ]; then
            cp "rules/GEMINI.md" "$TARGET_RULES/"
            echo "[OK] GEMINI.md installed to $TARGET_RULES"
        fi

        SECONDARY_RULES="$TARGET_RULES/rules"
        mkdir -p "$SECONDARY_RULES"

        # Copy everything EXCEPT GEMINI.md to the 'rules' subfolder
        # Use find to list files and filter out GEMINI.md
        find rules -maxdepth 1 -mindepth 1 ! -name "GEMINI.md" -exec cp -r {} "$SECONDARY_RULES/" \; 2>/dev/null || true
        echo "[OK] Secondary rules installed to $SECONDARY_RULES"
    else
        echo "[Packaging] Copying rules from ./rules to $TARGET_RULES..."
        if [ "$AGENT" != "antigravity" ]; then
            # Copy everything except GEMINI.md
            find rules -maxdepth 1 -mindepth 1 ! -name "GEMINI.md" -exec cp -r {} "$TARGET_RULES/" \; 2>/dev/null || true
        else
            cp -r rules/* "$TARGET_RULES/" 2>/dev/null || true
        fi
        echo "[OK] Rules installed."
    fi
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
