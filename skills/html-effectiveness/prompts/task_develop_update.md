The user wants to UPDATE the develop design and code based on their feedback.
Current Workflow Steps:
{workflow_str}

Current File Tree:
{file_tree_str}

Current Code Snippets:
{snippets_str}

User's Feedback/Instructions:
{feedback_input}

Analyze the feedback and output the updated develop.
CRITICAL RULE FOR QUESTIONS: Limit the "open_questions" list strictly to at most three (3) of the most important remaining questions that must need the user to decide. Otherwise, you should research contents provided by the user, like local files or codes. Do not ask more than three.
CRITICAL RULE: Group related details into cohesive paragraph strings. Let the AI determine the optimal semantic grouping. Do NOT blindly split every single sentence or newline into a separate item.
You MUST respond ONLY with a JSON block in this schema:
```json
{{
  "develop": {{
    "workflow_steps": ["Step 1: cohesive paragraph...", "Step 2: cohesive paragraph..."],
    "file_tree": [
      {{ "path": "...", "status": "..." }}
    ],
    "code_snippets": [
      {{
        "filename": "...",
        "language": "...",
        "code": "..."
      }}
    ],
    "open_questions": ["Question 1...", "Question 2..."]
  }},
  "event_type": "task_develop_update",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
