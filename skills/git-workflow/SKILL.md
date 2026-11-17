---
name: git-workflow
description: Standard git commit formatting, branch hygiene, and repository rules.
---

# Git Workflow

## Commit Message Format

```text
<type>: <description>

<optional body>

<optional footers>
```

For kernel commits, use `subsystem: <description>` per upstream convention.

### Commit Message Rules

* **Title Length**: Commit title (first line) <= 72 characters.
* **Blank Line**: Separate the title from the body with a single blank line.
* **Imperative Mood**: Write the title in the imperative mood so it completes
  "If applied, this commit will `<title>`" (e.g., `fix: resolve null pointer`,
  not `fixed` or `fixes`).
* **Capitalization & Punctuation**: Capitalize the first letter of the
  description (or subject) and do not end the title with a period.
* **Body Line Wrap**: Wrap commit body content at 72 characters per line.
* **Body Content (What & Why)**: Explain *what* changed and *why* (including
  non-obvious design choices), rather than *how* the code implements it. Omit
  the body if the title is self-explanatory.
* **Types**:
  * `feat`: new feature
  * `fix`: bug fix
  * `update`: update or refactor existing code
  * `ci`: CI/pipeline changes
  * `docs`: documentation only
  * `release`: release or version bump
  * `task`: general task
* **Footers / Trailers**:
  * Include `Signed-off-by: Name <email>` when required by project policy.
  * Place issue or ticket references in the footer rather than the commit
    title.

## Branch and History Guidelines

* **One Logical Change per Commit**: Split large changes into multiple
  logical, self-contained commits. Avoid combining unrelated features, fixes,
  or distinct components (e.g., separate different recipes, configs, or DTS
  changes).
* **No Merge Commits**: Keep feature and topic branches linear without merge
  commits. Rebase instead of merging when updating or collaborating on the same
  branch.
* **No Incremental Fix-Up Commits**: Do not push follow-up commits to address
  review comments or fix typos. Use `git commit --amend` or `git rebase -i`
  to update the original commit and force-push, keeping history clean and
  bisectable.

## Pull Request Guidelines

* **PR Title**: Use a concise, imperative one-line summary <= 72 characters,
  formatted as `<type>: <subject>` (or `<type>(<scope>): <subject>`).
* **PR Description**: Summarize *what* changed and *why* without repeating the
  PR title. Reference relevant design documents or dependent PRs when
  applicable.

## Repository Guidelines

* Do not add `.agent` or any hidden folders starting with `.`
  (e.g., `.folder/`) to the repository. Keep them local or manage them via
  `.gitignore`.
