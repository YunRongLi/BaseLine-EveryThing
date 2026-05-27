The user has finalized the task specifications and wants to generate the develop and architectural design.
Final Specification Sections:
{sections_str}

User's Scoping Feedback/Instructions:
{scoping_input}

Analyze these specifications and design the Develop architecture, workflow steps, file tree list, and core logic snippets.
CRITICAL RULE FOR QUESTIONS: Limit the "open_questions" list strictly to at most three (3) of the most important architectural questions that must need the user to decide. Otherwise, you should research contents provided by the user, like local files or codes. Do not ask more than three.
You MUST respond ONLY with a JSON block in this schema:
```json
{{
  "develop": {{
    "workflow_steps": [
      "Step 1: Description of step (clean text)",
      "Step 2: Description of step"
    ],
    "file_tree": [
      {{ "path": "src/main.py", "status": "new" }},
      {{ "path": "tests/test_main.py", "status": "new" }}
    ],
    "code_snippets": [
      {{
        "filename": "src/main.py",
        "language": "python",
        "code": "def core_logic():\\n    pass"
      }}
    ],
    "open_questions": [
      "Question 1 (clean text)",
      "Question 2"
    ]
  }},
  "event_type": "task_spec_finalize",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
