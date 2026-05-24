# Task Prototype Workflow

This workflow describes and builds the main functionality or contents of the task based on the spec.

## AI Instructions
1. In the prototype workflow, the first important thing is to provide a detailed **Design Overview** following the draft spec and any previous feedback.
2. If the task is a feature or test case implementation, prioritize outlining the design overview, architecture, components, and workflows.
3. Present this Design Overview to the user so they are able to modify, add, or delete the contents before generating final code.
4. If a functional UI mock is needed, provide instructions for the user to view it or output specific snippets, but the main output must be the structured design logic.

## Strict Workspace Cleanup Rules
- **Temporary Path Selection**: Before creating any files or starting servers, you MUST ask the user where to place the temporary files (e.g., 1. $HOME, 2. Current workspace's `.tmp` folder, 3. System temp folder `$env:TEMP` / `/tmp`). Only proceed after the user selects a path.
- **Post-Task Cleanup**: Once the user has finished evaluating the prototype and provided approval, you MUST delete all derivative archives/files generated during this process from the selected temporary path and shut down any background servers started for it.

## System & UI Specifications
- **Interactive UI Layout**: Use modern aesthetics, auto-resizing textareas (using `resize: none; overflow: hidden;` CSS and `autoResizeTextarea` JS logic) to eliminate scrollbars, and collapsible cards (`[ - ]` / `[ + ]`) to maintain neat layouts.
- **Startup Integrity**: The server validates environment variables and will immediately exit with a helpful instruction if the agent API Key is missing.
- **Spec Export & Portability**: Enable copying and exporting of both specifications and prototypes to Markdown files directly from the UI.
- **Workspace Path Memory**: Persist the user's customized 'Implementation Workspace Path' input using local browser storage (`localStorage`) so that it is automatically remembered and restored on page refreshes.
