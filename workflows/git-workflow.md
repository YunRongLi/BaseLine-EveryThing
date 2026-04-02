---
description: Git Workflow
---

# Git Workflow

## Commit Message Format
```
<type>: <description>

<optional body>
```

Types: 
  * feat: new feature
  * fix: fix bug
  * update: refactor existing code

- Do not add `.agent` or any hidden folders starting with `.` (e.g., `.folder/`) to the repository. These should remain local or be managed via `.gitignore`.
- **Split large changes into multiple logical commits.** Each commit should represent a single, self-contained change or refactoring. Avoid combining unrelated features or fixes.
- **Provide meaningful commit descriptions.** Explain *why* the change is being made and any non-obvious design choices.
