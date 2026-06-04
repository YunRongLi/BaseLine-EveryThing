#!/bin/bash
set -e

# Find script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
WORKSPACE_PATH="$(cd "$SCRIPT_DIR/../../.." &>/dev/null && pwd)"

SERVICE_TEMPLATE="$SCRIPT_DIR/agent-html.service"
TARGET_DIR="$HOME/.config/systemd/user"
TARGET_FILE="$TARGET_DIR/agent-html.service"

echo "Setting up systemd user service..."
echo "Workspace path: $WORKSPACE_PATH"
echo "Service template: $SERVICE_TEMPLATE"

# Ensure target directory exists
mkdir -p "$TARGET_DIR"

# Replace placeholder and write target service file
# We use | as sed separator because paths contain / characters
sed "s|%WORKSPACE_PATH%|$WORKSPACE_PATH|g" "$SERVICE_TEMPLATE" > "$TARGET_FILE"

echo "Service file written to: $TARGET_FILE"
echo ""
echo "To manage the service, run the following commands:"
echo "  systemctl --user daemon-reload"
echo "  systemctl --user enable agent-html.service"
echo "  systemctl --user start agent-html.service"
echo ""
echo "To check the service status:"
echo "  systemctl --user status agent-html.service"
echo ""
echo "To view logs:"
echo "  journalctl --user -u agent-html.service -f"
