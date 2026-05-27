The user wants to UPDATE the task specifications based on their feedback.
Current Specification Sections:
{sections_str}

User's Feedback/Instructions:
{scoping_input}

Analyze the feedback and output the updated specifications and remaining/new questions.
CRITICAL RULE FOR QUESTIONS: Limit the "open_questions" list strictly to at most three (3) of the most important remaining or new questions that must need the user to decide. Otherwise, you should research contents provided by the user, like local files or codes. Do not ask more than three.
CRITICAL RULE FOR ITEMS: Group related details into a single, cohesive paragraph string. Let the AI determine the optimal semantic grouping. Do NOT blindly split every single sentence or newline into a separate item.
You MUST respond ONLY with a JSON block in this schema:
```json
{{
  "spec": {{
    "sections": [
      {{
        "title": "Section Title",
        "items": ["Item 1 (use basic markdown like bold text if helpful)", "Clean text item 2"]
      }}
    ],
    "open_questions": ["Question 1", "Question 2"]
  }},
  "event_type": "task_spec_update",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
