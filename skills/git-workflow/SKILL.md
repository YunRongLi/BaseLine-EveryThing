---
name: git-workflow
description: Standard git commit formatting and repository rules.
---

# Git Workflow

## Commit Message Format

```text
<type>: <description>

<optional body>
```

### Commit Message Rules

* **Title Length**: Commit title (first line) <= 72 characters.
* **Body Line Wrap**: Commit body content wrapped at 72 characters
  per line (內容每 72 個字元斷行).
* **Types**:
  * `feat`: new feature
  * `fix`: fix bug
  * `update`: refactor existing code

### Repository and Change Guidelines

* Do not add `.agent` or any hidden folders starting with `.`
  (e.g., `.folder/`) to the repository. These should remain local or
  be managed via `.gitignore`.
* **Split large changes into multiple logical commits.** Each commit
  should represent a single, self-contained change or refactoring.
  Avoid combining unrelated features or fixes.
* **Provide meaningful commit descriptions.** Explain why the change
  is being made and any non-obvious design choices.
