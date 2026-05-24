# Task Spec Workflow

This workflow defines the environment, requirements, conditions, and tools for a task.

## AI Instructions
1. Based on the initial task discussion, design an interactive specification UI.
2. The UI must clearly map out the operating environment, feature requirements, acceptance criteria (conditions), and necessary tools.
3. Enable interactive fields or forms where the specification can be refined, edited, or expanded directly in the browser.

## Strict Workspace Cleanup Rules
- **Temporary Path Selection**: Before creating any files or starting servers, you MUST ask the user where to place the temporary files (e.g., 1. $HOME, 2. Current workspace's `.tmp` folder, 3. System temp folder `$env:TEMP` / `/tmp`). Only proceed after the user selects a path.
- **Post-Task Cleanup**: Once the user has finished the specification phase and the spec is finalized, you MUST delete all derivative archives/files generated during this process from the selected temporary path and shut down any background servers started for it.

## System & UI Specifications
- **Interactive UI Layout**: Use modern aesthetics, auto-resizing textareas (using `resize: none; overflow: hidden;` CSS and `autoResizeTextarea` JS logic) to eliminate scrollbars, and collapsible cards (`[ - ]` / `[ + ]`) to maintain neat layouts.
- **Startup Integrity**: The server validates environment variables and will immediately exit with a helpful instruction if the agent API Key is missing.
- **Spec Export & Portability**: Enable copying and exporting of specifications to Markdown files directly from the UI.
