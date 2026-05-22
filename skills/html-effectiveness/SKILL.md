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

## 2. Triggers
Apply this skill whenever the user requests or the task naturally fits one of the following:
- **Exploration & Planning:** Side-by-side comparisons of code approaches, visual design directions, or implementation timelines.
- **Code Review & Understanding:** Annotated diffs with margin notes, PR writeups, or module maps (boxes and arrows).
- **Design & Prototyping:** Living design systems, component variants, animation sandboxes, or clickable UI flows.
- **Illustrations:** Flowcharts, diagrams, or SVG figure sheets.
- **Presentations/Decks:** Slide decks that can be navigated via arrow keys.
- **Research & Reports:** Feature explainers, concept explainers, weekly status reports, or incident timelines.
- **Custom Editing Interfaces:** Throwaway UIs like ticket triage boards, feature flag editors, or prompt tuners with "copy-to-clipboard" exports.

## 3. Execution
1. Think about the structure and interactive capabilities of the HTML artifact before writing code.
2. Use the `write_to_file` tool to save the `.html` file.
3. Use the `run_command` tool to run the custom HTTP server script: `~/.gemini/antigravity/skills/html-effectiveness/scripts/serve_html.py <directory_of_html_file>`. Send it to the background (e.g., `...serve_html.py . &> /dev/null &`) or use appropriate timeouts so it doesn't block. Wait a short duration (e.g. 1000ms) to capture the printed port before making the command async.
4. The script will output the port it chose (e.g., `Server started at http://localhost:43218`). Provide the user with the localhost URL (e.g., `http://localhost:<port>/filename.html`) so they can access it via their browser. Do not output the entire HTML code in your chat response.

## 4. Special Commands
### `/task-create`
When the user explicitly issues the `/task-create` command:
1. Generate an interactive HTML discussion interface tailored for scoping the new task.
2. The interface must allow the user to provide high-level thoughts, descriptions, and metadata.
3. Start the local HTML server and provide the user with the localhost URL so they can access it in their browser.

### `/task-spec`
When the user explicitly issues the `/task-spec` command:
1. Based on the initial task discussion, design an interactive specification UI.
2. The UI must clearly map out the operating environment, feature requirements, acceptance criteria (conditions), and necessary tools.
3. Enable interactive fields or forms where the specification can be refined, edited, or expanded directly in the browser.

### `/task-prototype`
When the user explicitly issues the `/task-prototype` command:
1. Construct an interactive prototype or visual representation of the proposed solution based on the defined spec.
2. Implement mock workflows, interactive wireframes, layouts, or simulated logic so the user can visualize and interact with the main features.
3. Keep the prototype highly interactive to encourage hands-on exploration.

### `/task-review`
When the user explicitly issues the `/task-review` command:
1. Capture any inputs, edits, or feedback submitted by the user through the interactive elements of the HTML UI.
2. Seamlessly update the corresponding spec or prototype files to reflect the feedback.
3. Present the updated version or a clear revision comparison to the user, allowing continuous iterative review.
