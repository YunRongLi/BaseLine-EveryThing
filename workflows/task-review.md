# Task Review Workflow

This workflow handles updating the spec or prototype based on the user's suggestions and feedback in the HTML interface.

## AI Instructions
1. Capture any inputs, edits, or feedback submitted by the user through the interactive elements of the HTML UI.
2. Seamlessly update the corresponding spec or prototype files to reflect the feedback.
3. Present the updated version or a clear revision comparison to the user, allowing continuous iterative review.

## Strict Workspace Cleanup Rules
- **Temporary Path Selection**: Before creating any files or starting servers, you MUST ask the user where to place the temporary files (e.g., 1. $HOME, 2. Current workspace's `.tmp` folder, 3. System temp folder `$env:TEMP` / `/tmp`). Only proceed after the user selects a path.
- **Post-Task Cleanup**: Once the review cycle is complete and the final output is produced, you MUST delete all derivative archives/files generated during this process from the selected temporary path and shut down any background servers started for it.

## System & UI Specifications
- **Interactive UI Layout**: Use modern aesthetics, auto-resizing textareas (using `resize: none; overflow: hidden;` CSS and `autoResizeTextarea` JS logic) to eliminate scrollbars, and collapsible cards (`[ - ]` / `[ + ]`) to maintain neat layouts.
- **Startup Integrity**: The server validates environment variables and will immediately exit with a helpful instruction if the agent API Key is missing.
- **Spec Export & Portability**: Enable copying and exporting of specifications to Markdown files directly from the UI.
