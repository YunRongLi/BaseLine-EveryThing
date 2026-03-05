---
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

### 1.4. Callouts
Use callouts for structured information. Format: `> [!type] Title`
- Standard types: note, abstract, info, todo, tip, success, question, warning, failure, danger, bug, example, quote.
- Use `> [!type]-` for collapsed callouts by default.

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

## 4. Vault Organization and Naming

- File names should be descriptive and unique.
- Avoid special characters in filenames that are not OS-safe.
- Folder structure should follow a logical hierarchy (e.g., Projects, Resources, Archive).
- Use tags for cross-cutting concerns (e.g., #urgent, #review-needed).

## 5. Validation Checklist

Before finalizing a document, ensure:
1. Properties (YAML) are valid and complete.
2. All wikilinks point to existing notes or intended new notes.
3. Canvas IDs are unique and edge references are valid.
4. Base YAML schema is correct.
5. No icons or emojis are used in the document structure as per project rules.
6. Bit/byte explanations are formatted correctly in Markdown tables for clarity.

