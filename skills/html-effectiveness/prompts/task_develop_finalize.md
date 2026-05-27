The user has approved the prototype and submitted final implementation and execution instructions.
Final Workflow Steps:
{workflow_str}

Final File Tree:
{file_tree_str}

Final Code Snippets:
{snippets_str}

Final Feedback/Instructions:
{feedback_input}

Finalize the task. Provide a completion summary list, list of files implemented, and verification logs/results.
You MUST respond ONLY with a JSON block in this schema:
```json
{{
  "completed": {{
    "summary_items": [
      "Summary detail 1 (use basic markdown formatting if helpful)",
      "Summary detail 2"
    ],
    "created_files": [
      "src/main.py",
      "tests/test_main.py"
    ],
    "verification_results": [
      "Test 1: Scan vault (Pass)",
      "Test 2: Inbox archiving (Pass)"
    ]
  }},
  "event_type": "task_develop_finalize",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
