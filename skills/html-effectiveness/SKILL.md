---
name: html-effectiveness
description: Instructs the agent to generate rich, interactive HTML artifacts for complex information (exploration, reviews, design, prototyping) instead of linear markdown walls.
---

# HTML Effectiveness Skill

When presenting spatial information, timelines, comparisons, visual designs, or custom editing interfaces, **do not write a wall of markdown.** Instead, generate a self-contained `.html` file.

## 1. Rules
- **Zero Build Step:** Use inline CSS and vanilla JavaScript only. Do not use external frameworks or build steps.
- **Actionable & Navigable:** Layouts must use Flexbox or CSS Grid for side-by-side comparisons to avoid long linear scrolling.
- **Functionality First:** Beautiful UI is NOT the primary goal. Prioritize clear, functional layouts and robust logic over aesthetic polish.
- **Deep Interactivity:** Treat the HTML as a functional application. For example, if designing a test case, build an interface that allows the user to add, modify, or remove test steps directly within the browser, and export the results.
- **Dialogs & Scaffolding:** If any dialog item, modal window, or form will help the user to better design or define their work, it is highly encouraged to use them.
- **No Fabricated Data:** Do not invent runtime data or screenshots.

### Output Constraints (Mandatory for every HTML output)
- **Single-File Self-Containment:** All HTML, CSS, JavaScript, and SVG assets must be fully inlined. Do not rely on CDNs or external libraries.
- **Mandatory Export:** Any HTML file that allows user interaction or input must include a "Copy as Markdown" button to export its state.
- **Desktop Responsive:** The layout must scale beautifully on screens from 1280px laptops up to 1920px external monitors. Mobile responsiveness is not required.
- **Limit Agent Open Questions:** When generating specifications or prototyping steps, always limit the open questions list strictly to at most three (3) of the most important architectural or functional questions to prevent analysis paralysis.

### Style & Design Guidelines (Best Practices)
To produce premium, highly readable HTML artifacts matching reference standards, incorporate these cohesive patterns:
- **System Typography Stacks:** Do not load external fonts. Define and use native system fonts for consistent, fast rendering:
  - Sans-serif (for UI/body): `system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`
  - Serif (for editorial headings): `ui-serif, Georgia, "Times New Roman", Times, serif`
  - Monospace (for code/identifiers): `ui-monospace, "SF Mono", Menlo, Monaco, Consolas, monospace`
- **Cohesive Design Tokens:** Establish a warm, unified color scheme using CSS variables at the `:root`:
  - `--ivory`: `#FAF9F5` (Soft background)
  - `--paper`: `#FFFFFF` (Card background)
  - `--slate`: `#141413` (Main text/dark UI elements)
  - `--clay`: `#D97757` (Primary accent/attention/attention alerts)
  - `--oat`: `#E3DACC` (Warm beige details/medium risk)
  - `--olive`: `#788C5D` (Success/safe states/code additions)
  - `--rust`: `#B04A3F` (Blocking issues/errors/code deletions)
- **Navigation & Scaffolding:**
  - **Eyebrow Headers:** Use a small, tracked, uppercase monospace `.eyebrow` class above serif headings to frame context.
  - **Status & Risk Maps:** At the top of complex documents, provide colored anchor link chips as a navigable index.
  - **Native Accordions:** Style native `<details>` and `<summary>` tags with custom summary text, borders, and hover states for clean collapsible details.
  - **Copy-to-Clipboard Utilities:** Export buttons must trigger standard clipboard APIs with fallback `<textarea>` selection routines.

## 2. Usage Scenario Judgment (Shape Test)
After reading the user's request, perform a "Shape Test" on the expected answer to decide whether to use HTML:

| Answer Shape | Format to Use |
|---|---|
| A single statement, a number, or a brief conclusion | Direct text response |
| A few steps, a list of key points, or a single code snippet | Markdown |
| Complex spatial layouts, timelines, side-by-side comparisons, dashboards, or multi-step editing flows | HTML |

## 3. Triggers
Apply this skill whenever the user requests or the task naturally fits one of the following:
- **Exploration & Planning:** Side-by-side comparisons of code approaches, visual design directions, or implementation timelines.
- **Code Review & Understanding:** Annotated diffs with margin notes, PR writeups, or module maps (boxes and arrows).
- **Design & Prototyping:** Living design systems, component variants, animation sandboxes, or clickable UI flows.
- **Illustrations:** Flowcharts, diagrams, or SVG figure sheets.
- **Presentations/Decks:** Slide decks that can be navigated via arrow keys.
- **Research & Reports:** Feature explainers, concept explainers, weekly status reports, or incident timelines.
- **Custom Editing Interfaces:** Throwaway UIs like ticket triage boards, feature flag editors, or prompt tuners with "copy-to-clipboard" exports.

## 4. Execution
1. Think about the structure and interactive capabilities of the HTML artifact before writing code.
2. Use the `write_to_file` tool to save the `.html` file.
3. Use the `run_command` tool to run the custom HTTP server script located at the skill's install path (e.g., `~/.gemini/skills/html-effectiveness/scripts/serve_html.py` for shared installs, `~/.agents/skills/html-effectiveness/scripts/serve_html.py` for workspace installs, `~/.gemini/antigravity/skills/html-effectiveness/scripts/serve_html.py` for legacy global installs, or `~/.gemini/antigravity-cli/skills/html-effectiveness/scripts/serve_html.py` for CLI global installs). Send it to the background (e.g., `...serve_html.py . &> /dev/null &`) or use appropriate timeouts so it doesn't block. Wait a short duration (e.g. 1000ms) to capture the printed port before making the command async.
4. The script will output the port it chose (e.g., `Server started at http://localhost:43218`). Provide the user with the localhost URL (e.g., `http://localhost:<port>/filename.html`) so they can access it via their browser. Do not output the entire HTML code in your chat response.

## 5. Special Commands
### `/task-explore`
When the user explicitly issues the `/task-explore` command:
1. Generate an interactive HTML interface tailored for exploring the user's codebase, data, or current problem space.
2. The main grid MUST provide a terminal interface allowing the user to communicate back and forth with the Agent.
3. The page MUST provide a dialog box (modal) that allows the user to add/import reference documents or code (files or directories).
4. Start the local HTML server and provide the user with the localhost URL so they can access it in their browser.

### `/task-create`
When the user explicitly issues the `/task-create` command:
1. Generate an interactive HTML discussion interface tailored for scoping the new task.
2. The interface must allow the user to provide high-level thoughts, descriptions, and metadata.
3. Start the local HTML server and provide the user with the localhost URL so they can access it in their browser.

### `/task-spec`
When the user explicitly issues the `/task-spec` command:
1. Based on the initial task discussion, design an interactive specification UI inside the Spec tab.
2. The UI must clearly map out the operating environment, feature requirements, acceptance criteria (conditions), and necessary tools.
3. Enable interactive fields or forms where the specification can be refined, edited, or expanded directly in the browser.
4. **Mandatory Text Dialogue**: You MUST include a large multi-line text input box (`<textarea id="scopingInput">`) so the user can easily draft additional scoped instructions or custom requirements.

### `/task-develop`
When the user explicitly issues the `/task-develop` command:
1. Construct an interactive develop or visual representation of the proposed solution based on the defined spec.
2. Implement mock workflows, interactive wireframes, layouts, or simulated logic so the user can visualize and interact with the main features.
3. Keep the develop highly interactive to encourage hands-on exploration.
4. **Mandatory Text Dialogue & Finalization**: You MUST include a large multi-line text input box (`<textarea id="developFeedback">`) for final implementation/verification feedback.

