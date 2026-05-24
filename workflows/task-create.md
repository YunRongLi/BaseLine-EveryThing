# Task Create Workflow

This workflow initiates a discussion for a new task and sets up the interactive HTML environment.

## AI Instructions
1. Generate an interactive HTML discussion interface tailored for scoping the new task.
2. The interface must allow the user to provide high-level thoughts, descriptions, and metadata, excluding priority, implementation steps, and Technical Risks & Challenges.
3. Start the local HTML server and provide the user with the localhost URL so they can access it in their browser.

## Strict Workspace Cleanup Rules
- **Temporary Path Selection**: Before creating any files or starting servers, you MUST ask the user where to place the temporary files (e.g., 1. $HOME, 2. Current workspace's `.tmp` folder, 3. System temp folder `$env:TEMP` / `/tmp`). Only proceed after the user selects a path.
- **Post-Task Cleanup**: Once the user has finished the task scoping phase and the data is captured, you MUST delete all derivative archives/files generated during this process from the selected temporary path and shut down any background servers started for it.

## System & UI Specifications
- **Interactive UI Layout**: Use modern aesthetics, auto-resizing textareas (using `resize: none; overflow: hidden;` CSS and `autoResizeTextarea` JS logic) to eliminate scrollbars, and collapsible cards (`[ - ]` / `[ + ]`) to maintain neat layouts.
- **Startup Integrity**: The server validates environment variables and will immediately exit with a helpful instruction if the agent API Key is missing.
- **Spec Export & Portability**: Enable copying and exporting of specifications to Markdown files directly from the UI.
