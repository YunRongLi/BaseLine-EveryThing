Analyze this task and generate the specifications.
Task Title: {title}
Category: {category}
Goal: {goal}
Context: {context}

You MUST respond ONLY with a JSON block matching this exact schema:
```json
{{
  "spec": {{
    "sections": [
      {{
        "title": "Functional Requirements / 功能需求",
        "items": [
          "Requirements 1",
          "Requirements 2"
        ]
      }},
      {{
        "title": "Technical Constraints / 技術限制",
        "items": [
          "Constraints 1",
          "Constraints 2"
        ]
      }}
    ],
    "open_questions": [
      "Clarifying Question 1 (use bullet points and bolding if helpful)",
      "Clarifying Question 2"
    ]
  }},
  "event_type": "task_create",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
Provide at least 3-4 sections detailing the full specification, functional scope, and data formats. 
CRITICAL RULE FOR QUESTIONS: Limit the "open_questions" list strictly to at most three (3) of the most important architectural or functional questions that must need the user to decide. Otherwise, you should research contents provided by the user, like local files or codes. Do not ask more than three.
CRITICAL RULE FOR ITEMS: Group related details (e.g., a feature and its sub-descriptions) into a single, cohesive paragraph string. Let the AI determine the optimal semantic grouping. Do NOT blindly split every single sentence or newline into a separate item.
Keep all items clean, highly technical, and professional. Feel free to use light Markdown bullet points or bold text to structure descriptions.
