The user's code is undergoing validation and regression verification. Your task is to analyze the runtime environments, develop designs, and command execution outputs to determine if the implemented code conforms to the target design, identify any discrepancies or bugs, and apply fixes.

=========================================
ACTIVE ENVIRONMENT VARIABLES / 環境變數設定:
{env_vars_str}
=========================================

=========================================
VERIFICATION STEP COMMANDS / 驗證步驟命令:
{test_steps_str}
=========================================

=========================================
TERMINAL LOG OUTPUT / 執行日誌輸出:
{test_logs}
=========================================

=========================================
USER RECOVERY & TRIAGE REMEDIATION INSTRUCTIONS / 使用者反饋與修復指示:
{feedback_input}
=========================================

=========================================
ORIGINAL SOLUTION FILES & DEVELOP DESIGNS / 解決方案原型結構:
{file_tree_str}
=========================================

=========================================
CURRENT IMPLEMENTED WORKSPACE SNIPPETS / 目前工作區實作程式碼:
{snippets_str}
=========================================

CRITICAL REASONING & AUTO-FIX WORKFLOW:
1. Review the active Environment Variables and Verification Test Steps used during execution.
2. Cross-reference the Terminal Log Output with your original Prototyping design and code.
3. Identify exactly why assertions or execution failed.
4. Correct the bugs directly inside the code snippets. You must return the COMPLETE updated file contents (not unified diffs) for any file you modify.
5. Prevent regression: Ensure that fixing one bug does not break other designed components or previously passing tests.

Provide:
1. A summary list of the applied fixes.
2. A list of remaining issues (if any, else empty).
3. The complete revised code for any modified files inside the "code_snippets" array.

You MUST respond ONLY with a JSON block matching this exact schema:
```json
{{
  "testing": {{
    "applied_fixes": [
      "Fix detail 1 (use basic markdown formatting if helpful)",
      "Fix detail 2"
    ],
    "remaining_issues": []
  }},
  "code_snippets": [
    {{
      "filename": "src/main.py",
      "language": "python",
      "code": "def core_logic():\\n    # revised complete code..."
    }}
  ],
  "event_type": "task_regression",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
