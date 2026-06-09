---
name: obsidian
trigger: glob
globs: "**/*.{md,canvas,base}"
description: Guidelines for managing Obsidian-flavored Markdown, JSON Canvas, and Obsidian Bases files. Use when creating, editing, or organizing notes and visual diagrams within an Obsidian vault.
---

# Obsidian Document Guidelines

These guidelines are based on the Obsidian Skills framework and serve as the standard for document creation and maintenance within the vault. Always prioritize Obsidian-native features for maximum compatibility and functionality.

## 1. Obsidian-Flavored Markdown (OFM)

Use OFM for all note content to leverage Obsidian's relationship-tracking and visualization capabilities.

### 1.1. Internal Linking (Wikilinks)
- Use standard wikilinks: `[[Note Name]]`
- Use display text: `[[Note Name|Display Text]]`
- Link to headers: `[[Note Name#Header Name]]`
- Link to blocks: `[[Note Name#^block-id]]`
- Block ID creation: Append `^my-id` to any paragraph or list item.

### 1.2. Embeds and Transclusion
- Prefix wikilinks with `!` to embed content: `![[Note Name]]`
- Embed specific sections: `![[Note Name#Header]]`
- Image embedding with width: `![[image.png|300]]`

### 1.3. Properties (Frontmatter)
All notes should begin with a YAML frontmatter block containing essential metadata.
- title: string
- created: date
- updated: date
- tags: list of tags
- aliases: list of alternative names
- status: [draft, active, archived]
- type: [thing, statement, question, quote, person, moc, journal]

Each note type should include specific additional properties as guidelines:
- person: company, role
- statement: origin, related-claims
- moc: topic, status-notes

### 1.4. Callouts and AI-Agent Output Rules
Use callouts for structured information. Format: `> [!type] Title`
- Standard types: note, abstract, info, todo, tip, success, question, warning, failure, danger, bug, example, quote.
- Use `> [!type]-` for collapsed callouts by default.
- **AI Agent Automation Formatting**: When the AI agent processes meeting notes, inbox triage, or summaries:
  - Important risks and critical caveats must be formatted inside `> [!warning]` or `> [!danger]` blocks.
  - Action items and next steps must be formatted inside `> [!todo]` blocks.
  - Actionable tasks must be output as interactive checkboxes `- [ ]` for dynamic user tracking.

### 1.5. Special Formatting
- Highlights: `==highlighted text==`
- Comments: `%%hidden text%%` (invisible in reading view)
- Footnotes: `[^1]` and `[^1]: description` or inline `^[footnote]`
- Math: Use LaTeX with `$` for inline and `$$` for blocks.
- Diagrams: Use Mermaid blocks for flowcharts, sequences, and class diagrams.


### 1.6. Bit and Byte Explanations
- When explaining the bitwise structure of a data byte or date byte (e.g., in a command field or protocol), use Markdown tables to define bit positions, labels, and functional descriptions for maximum clarity.


## 2. JSON Canvas (.canvas)

JSON Canvas is used for visual mapping and spatial organization.


### 2.1. File Structure
- Extension: `.canvas`
- Content: Valid JSON with `nodes` and `edges` arrays.
- ID Generation: Use 16-character lowercase hexadecimal strings (e.g., "6f0ad84f44ce9c17").

### 2.2. Node Types
- Text: `{"type": "text", "text": "..."}`
- File: `{"type": "file", "file": "path/to/note.md"}`
- Link: `{"type": "link", "url": "https://..."}`
- Group: `{"type": "group", "label": "..."}`

### 2.3. Edge Attributes
- `fromNode`: Source ID
- `toNode`: Target ID
- `fromSide` / `toSide`: [top, right, bottom, left]
- `toEnd`: [arrow, none] (default: arrow)

### 2.4. Layout Rules
- Position (x, y) refers to the top-left corner.
- Space nodes 50-100px apart for readability.
- Multiples of 10 or 20 for grid alignment.

## 3. Obsidian Bases (.base)

Bases are used for structured database-like views of vault data.

### 3.1. Structure
- Format: Valid YAML within a `.base` file.
- Primary Sections:
  - filters: Define criteria for the dataset (tags, folders, links).
  - properties: Map note frontmatter or file attributes.
  - formulas: Derive new values using functions.
  - views: Define layout types (table, list, cards, map).
  - summaries: Aggregate data (count, sum, average).

### 3.2. Integration
- Embed a base in a note: `![[Database.base]]`
- Embed a specific view: `![[Database.base#View Name]]`

## 4. Vault Organization (ACE Folder Framework)

Adopting the LYT (Linking Your Thinking) system, vault organization is structured around the **ACE Framework**, which uses broad, top-level physical spaces (folders) corresponding to mental spaces, while avoiding rigid category hierarchies:

- **00_Inbox**: A landing page at the vault root for all raw notes, audio recordings, or temporary files. This is the entry point for automated AI triage or manual classification.
- **01_Atlas** (Knowledge Space / Space): Intended "to understand" (Learning Mode). Stores permanent knowledge cards, MOC indexes, and source reference materials.
- **02_Calendar** (Time Space / Time): Intended "to focus" (Reflection Mode). Stores chronological daily journals, weekly reviews, and meeting records.
- **03_Efforts** (Action Space / Importance): Intended "to act" (Execution Mode). Holds active projects, tasks, focus areas, and completed deliverables.
- **Flat Folder Structure**: Restrict folder depth inside Atlas and Efforts. Rely on links and content maps rather than deep folders to form relationships between notes.
- **File Naming**: Names must be unique, highly descriptive, and avoid OS-unsafe special characters.

## 5. Knowledge Synthesis and Note Types

To ensure notes represent original thought rather than flat definitions, notes within the Atlas knowledge space are structured into **5 distinct note types**:

- **Things**: Concepts, frameworks, or tools ("What is this?").
- **Statements**: Personal opinions, insights, or principles ("What do I think?"). Writing statements is the key driver of value in personal knowledge management.
- **Questions**: Unresolved queries, areas for further exploration ("What am I curious about?").
- **Quotes**: Highlights, citations, and thoughts from others ("What do others say?").
- **People**: Context about individuals, teams, or organizations ("Who is this person?").

## 6. Maps of Content (MOC) Strategy

MOCs serve as curated map notes that index, group, and contextualize links to other notes, providing an essential "bird's-eye view" to balance bottom-up note growth.

### 6.1. Types of MOCs
- **Subject MOC**: Maps out a specific knowledge area. It provides a structured entry point to a cluster of related concepts in the Atlas.
- **Project MOC**: Acts as a dynamic "thinking workspace" or "workbench" to organize ideas, drafts, and tasks for a specific project goal in Efforts.
- **Fleeting MOC**: A temporary workbench for triaging and linking high-growth note clusters before they mature into Atlas MOCs.

### 6.2. Knowledge Synthesis Principles
- **Action over Collection**: Prioritize synthesis and personal thinking over information hoarding.
- **Opinion Notes**: MOCs should contain personal narratives and summaries to weave raw notes into active knowledge.
- **Bottom-up Growth**: Let MOCs emerge organically once notes on a topic reach a critical mass (e.g. 5+ related notes), rather than building rigid top-down schemas prematurely.
- **Incubation and Sedimentation**: Use the MOC workspace to incubate ideas during projects, and sediment refined insights back into the Atlas upon project completion.

## 7. AI-Agent PKM and Google Antigravity Workflows

Google Antigravity interfaces directly with the local Obsidian vault via `obsidian-cli`. To maximize AI coordination and efficiency, follow these guidelines:

### 7.1. MOC-First AI Context
MOCs are the ultimate structure for AI-agent compatibility. Because an MOC indexes an entire subject area, the AI agent can open a single MOC note to instantly comprehend the context and structure of your thoughts, rather than wasting tokens traversing separate files.

### 7.2. Vault Skill Configuration
Establish a standard directory `.agent/skills/` (e.g., `.agent/skills/obsidian/`) to store custom `SKILL.md` documents. These define specific operational rules that the Antigravity agent will automatically parse and follow when editing.

### 7.3. Style Guide & Vibe Coding
Store vault formatting preferences (such as HSL color variables, full-width layouts, or writing style examples) inside a dedicated `Style Guide.md` note. The agent will read this guide to mimic your unique design taste and writing voice.

### 7.4. Inbox Automation & Triage
Utilize natural language prompts to task the Antigravity agent with automated housekeeping:
- "Clean up my Inbox by analyzing note content and suggesting the correct ACE folders."
- "Format this raw transcript, extract next steps into a `> [!todo]` callout, and add interactive checkboxes."

### 7.5. Version Control & Safety
- **Mandatory Backup**: Since the AI agent has direct file-system access, you must use a Git repository (e.g., the Obsidian Git plugin) to track, commit, and audit agent-made edits.
- **Workflows Configuration**: Define local automation chains in `~/.gemini/antigravity/global_workflows/` to trigger slash commands:
  - `/note-onboard`: Scan vault directories and index context.
  - `/note-vault`: Let user to set local path of obsidian vault for context.
  - `/note-inbox`: User provide content (voice, image, or text), AI process and input into the inbox.

## 8. Validation Checklist

Before finalizing a document, ensure:
1. Properties (YAML) are valid and complete, including a descriptive `type`.
2. All wikilinks point to existing notes or intended new notes.
3. Canvas IDs are unique and edge references are valid.
4. Base YAML schema is correct.
5. No icons or emojis are used in the document structure as per project rules.
6. Bit/byte explanations are formatted correctly in Markdown tables for clarity.
7. Vault organization follows the ACE folder framework and MOC synthesis principles.
8. Vault changes are backed up via Git before executing complex AI modifications.
