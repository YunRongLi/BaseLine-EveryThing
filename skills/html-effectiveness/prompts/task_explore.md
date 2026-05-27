Analyze the user's context and generate an exploration strategy.
Context: {context}

You MUST respond ONLY with a JSON block matching this exact schema:
```json
{{
  "explore": {{
    "insights": [
      "[Component Overview] Description of the component/file and its design intent based on reference materials.",
      "[Key Capabilities] Concrete features, APIs, or system flows identified.",
      "[Suggested Next Steps] Recommended files, scripts, or directories to examine next for deep-dive."
    ]
  }},
  "event_type": "task_explore",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
