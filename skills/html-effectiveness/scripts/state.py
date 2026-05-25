WORKFLOW_STATE = {
    "current_stage": "create", # "create", "spec", "prototype", "testing", "completed"
    "create_data": {
        "title": "",
        "category": "Feature",
        "goal": "",
        "context": ""
    },
    "spec_data": {
        "sections": [],      # [{ "title": "...", "items": [...] }]
        "open_questions": [] # [ "question 1", "question 2" ]
    },
    "prototype_data": {
        "workflow_steps": [], # [ "step 1", "step 2" ]
        "file_tree": [],      # [{ "path": "...", "status": "new" }]
        "code_snippets": [],  # [{ "filename": "...", "language": "...", "code": "..." }]
        "open_questions": []  # [ "question 1", "question 2" ]
    },
    "testing_data": {
        "test_steps": [],                # [{ "id": 1, "cmd": "...", "desc": "..." }]
        "env_vars": {},                  # { "KEY": "VALUE" }
        "test_runs": [],                 # [{ "timestamp": "...", "logs": "...", "status": "..." }]
        "remediation_instructions": "",  # Pasted or generated instructions when test fails
        "regression_baseline": []        # Locked list of passing tests
    },
    "completed_data": {
        "summary_items": [],         # [ "item 1", "item 2" ]
        "created_files": [],         # [ "file 1", "file 2" ]
        "verification_results": []   # [ "result 1", "result 2" ]
    },
    "references": [] # [{ "type": "local/url", "value": "..." }]
}

