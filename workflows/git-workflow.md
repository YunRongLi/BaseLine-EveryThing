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

## Staging Rules
- Do not add `.agent` or any hidden folders starting with `.` (e.g., `.folder/`) to the repository. These should remain local or be managed via `.gitignore`.

