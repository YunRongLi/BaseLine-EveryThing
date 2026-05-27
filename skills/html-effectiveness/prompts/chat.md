The user says: "{user_msg}"

Please respond to the user naturally and helpfully.
You MUST respond ONLY with a JSON block matching this exact schema:
```json
{{
  "chat": "Your textual response here",
  "event_type": "chat",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
