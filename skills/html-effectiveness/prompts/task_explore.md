Analyze the user's context and generate an exploration strategy.
Context: {context}

You MUST respond ONLY with a JSON block matching this exact schema:
```json
{{
  "explore": {{
    "insights": ["<resonpse>"]
  }},
  "event_type": "task_explore",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
