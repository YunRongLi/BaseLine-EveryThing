import os, json, asyncio, httpx, sys
from state import WORKFLOW_STATE
from utils import resolve_references, load_requested_files
from search_tools import interactive_search, list_directory, glob_search
from recursive_search import perform_local_recursive_search
from config import check_api_key, check_api_key_anthropic, check_api_key_gemini
from patch_tools import apply_patch

async def call_claude_async(model_name, prompt):
    import httpx
    api_key = os.environ.get("ANTHROPIC_ADMIN_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Anthropic API key is not configured.")
        
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": model_name,
        "max_tokens": 8192,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=data)
        if response.status_code == 200:
            res_json = response.json()
            return res_json["content"][0]["text"]
        else:
            try:
                error_detail = response.json()
                error_msg = error_detail.get("error", {}).get("message", response.text)
            except Exception:
                error_msg = response.text
            raise RuntimeError(f"Anthropic API Error ({response.status_code}): {error_msg}")

async def call_vllm_async(model_name, prompt):
    import httpx
    url = os.environ.get("VLLM_API_URL")
    if not url:
        raise ValueError("VLLM API URL is not configured.")
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer not-needed"
    }
    
    data = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "max_tokens": 8192
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=headers, json=data)
        if response.status_code == 200:
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"]
        else:
            try:
                error_detail = response.json()
                error_msg = str(error_detail)
            except Exception:
                error_msg = response.text
            raise RuntimeError(f"VLLM API Error ({response.status_code}): {error_msg}")

def get_prompt_template(filename, fallback_template):
    try:
        prompts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts")
        file_path = os.path.join(prompts_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        print(f"DEBUG: Failed to read template {filename}: {e}")
    return fallback_template

async def call_agent_async(command, data):
    if not check_api_key():
        return "Error: No API key is configured (Neither GEMINI_API_KEY nor ANTHROPIC_ADMIN_API_KEY)."

    lang = data.get('language', 'en')
    lang_instruction = "Traditional Chinese (zh-TW)" if lang == 'zh' else "English (en)"
    
    prompt = f"CRITICAL: The user's preferred language is {lang_instruction}. You MUST write all titles, items, summaries, questions, and content inside the JSON in {lang_instruction}. Do NOT use any emojis or icons. IMPORTANT: You can use basic text formatting like bullet points ('- ') and bold text ('**word**') to make the insights, steps, and comments human-readable, but avoid heavy layout syntax like tables, raw HTML, or nested headers (e.g., '#', '##'). Return clean, well-formatted descriptions that will be directly displayed in textareas.\n\n"
    
    # Inject reference context if available
    references_list = data.get("references", [])
    ref_context = resolve_references(references_list)
    if ref_context:
        prompt += f"========================================= \nIMPORT REFERENCE MATERIALS & ARCHITECTURAL CONTEXT:\n{ref_context}\n=========================================\n\n"
        prompt += "DYNAMIC REFERENCE FILE ACCESS INSTRUCTIONS:\n"
        prompt += "- If you need to read the contents of any lazy-loaded reference file or directory listed above, you MUST set `\"needs_references\": true` in the root of your JSON response, and list the relative paths of the files you want to read in the `\"requested_files\"` array.\n"
        prompt += "- CRITICAL: If you set `\"needs_references\": true` to load files, you MUST NOT guess or fabricate details in Stage 1! Keep the primary content fields (like `\"insights\"`, `\"workflow_steps\"`, `\"specifications\"`, or `\"code_snippets\"`) empty or keep them minimal (e.g., `[]`), and focus entirely on specifying what relative file/folder paths you need to read in the `\"requested_files\"` array.\n"
        prompt += "- CRITICAL REFERENCE LOOKUP GUIDELINES:\n"
        prompt += "  * Do NOT blindly request the entire parent/workspace directory unless it is extremely small.\n"
        prompt += "  * Practice incremental/progressive lookup: Start by requesting root files (like `README.md`, `package.json`, `CMakeLists.txt`) or specific subfolders first, then deep-dive.\n"
        prompt += "  * If you want to check a folder's structure, request its relative path first (e.g., `\"skills/\"` or `\"src/\"`), which will return its directory tree so you can pick specific target files.\n"
        prompt += "Example response requesting file contents:\n"
        prompt += "```json\n"
        prompt += "{\n"
        prompt += "  \"needs_references\": true,\n"
        prompt += "  \"requested_files\": [\"skills/html-effectiveness/SKILL.md\"]\n"
        prompt += "}\n"
        prompt += "```\n"
        prompt += "If you do not need to read any additional reference contents, or have already received them, you MUST set `\"needs_references\": false` and leave `\"requested_files\"` as an empty list `[]`.\n\n"

    if command == "compress-history":
        history_str = json.dumps(data.get("chat_history", []), indent=2, ensure_ascii=False)
        fallback = """You are a helpful senior system architect. Analyze the following conversation history and compress it into a dense, high-fidelity engineering summary. Retain key structural decisions, requirements, code paths, and constraints. Do NOT use any Markdown symbols or emojis. Write a single cohesive paragraph.
        
        Conversation History:
        {history_str}
        
        Summary:"""
        template = get_prompt_template("compress_history.md", fallback)
        prompt += template.format(history_str=history_str)
    elif command == "task-explore":
        fallback = """Analyze the user's context and generate an exploration strategy.
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
"""
        template = get_prompt_template("task_explore.md", fallback)
        prompt += template.format(context=data.get('context', ''))
    elif command == "task-create":
        fallback = """Analyze this task and generate the specifications.
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
          "Requirements 1 (clean text without list markdown symbols)",
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
      "Clarifying Question 1 (clean text, no markdown)",
      "Clarifying Question 2"
    ]
  }},
  "event_type": "<string: the event type being handled (e.g., 'explore', 'create', 'chat', 'develop')>",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
Provide at least 3-4 sections detailing the full specification, functional scope, and data formats. 
CRITICAL RULE FOR QUESTIONS: Limit the "open_questions" list strictly to at most three (3) of the most important architectural or functional questions that must need the user to decide. Otherwise, you should research contents provided by the user, like local files or codes. Do not ask more than three.
CRITICAL RULE FOR ITEMS: Group related details (e.g., a feature and its sub-descriptions) into a single, cohesive paragraph string. Let the AI determine the optimal semantic grouping. Do NOT blindly split every single sentence or newline into a separate item.
Keep all items clean, high-technical, and professional. Do NOT use markdown.
"""
        template = get_prompt_template("task_create.md", fallback)
        prompt += template.format(
            title=data.get('title', ''),
            category=data.get('category', ''),
            goal=data.get('goal', ''),
            context=data.get('context', '')
        )
    elif command == "task-spec":
        is_update = data.get('is_update', False)
        sections = data.get('sections', [])
        scoping_input = data.get('scoping_input', '')
        sections_str = json.dumps(sections, indent=2, ensure_ascii=False)
        
        if is_update:
            fallback = """The user wants to UPDATE the task specifications based on their feedback.
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
        "items": ["Clean text item 1", "Clean text item 2"]
      }}
    ],
    "open_questions": ["Question 1", "Question 2"]
  }},
  "event_type": "<string: the event type being handled (e.g., 'explore', 'create', 'chat', 'develop')>",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
"""
            template = get_prompt_template("task_spec_update.md", fallback)
            prompt += template.format(
                sections_str=sections_str,
                scoping_input=scoping_input
            )
        else:
            fallback = """The user has finalized the task specifications and wants to generate the develop and architectural design.
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
  "event_type": "<string: the event type being handled (e.g., 'explore', 'create', 'chat', 'develop')>",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
"""
            template = get_prompt_template("task_spec_finalize.md", fallback)
            prompt += template.format(
                sections_str=sections_str,
                scoping_input=scoping_input
            )
    elif command == "task-develop":
        is_update = data.get('is_update', False)
        workflow_steps = data.get('workflow_steps', [])
        file_tree = data.get('file_tree', [])
        code_snippets = data.get('code_snippets', [])
        feedback_input = data.get('feedback_input', '')
        
        workflow_str = json.dumps(workflow_steps, indent=2, ensure_ascii=False)
        file_tree_str = json.dumps(file_tree, indent=2, ensure_ascii=False)
        snippets_str = json.dumps(code_snippets, indent=2, ensure_ascii=False)
        
        if is_update:
            fallback = """The user wants to UPDATE the develop design and code based on their feedback.
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
  "event_type": "<string: the event type being handled (e.g., 'explore', 'create', 'chat', 'develop')>",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
"""
            template = get_prompt_template("task_develop_update.md", fallback)
            prompt += template.format(
                workflow_str=workflow_str,
                file_tree_str=file_tree_str,
                snippets_str=snippets_str,
                feedback_input=feedback_input
            )
        else:
            fallback = """The user has approved the prototype and submitted final implementation and execution instructions.
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
      "Summary detail 1 (clean text without markdown)",
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
  "event_type": "<string: the event type being handled (e.g., 'explore', 'create', 'chat', 'develop')>",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
"""
            template = get_prompt_template("task_develop_finalize.md", fallback)
            prompt += template.format(
                workflow_str=workflow_str,
                file_tree_str=file_tree_str,
                snippets_str=snippets_str,
                feedback_input=feedback_input
            )
    elif command == "task-regression":
        feedback_input = data.get('feedback_input', '')
        test_logs = data.get('test_logs', '')
        code_snippets = data.get('code_snippets', [])
        file_tree = data.get('file_tree', [])
        env_vars = data.get('env_vars', {})
        test_steps = data.get('test_steps', [])
        
        env_vars_str = json.dumps(env_vars, indent=2, ensure_ascii=False)
        test_steps_str = json.dumps(test_steps, indent=2, ensure_ascii=False)
        file_tree_str = json.dumps(file_tree, indent=2, ensure_ascii=False)
        snippets_str = json.dumps(code_snippets, indent=2, ensure_ascii=False)
        
        fallback = """The user's code is undergoing validation and regression verification. Your task is to analyze the runtime environments, develop designs, and command execution outputs to determine if the implemented code conforms to the target design, identify any discrepancies or bugs, and apply fixes.

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
      "Fix detail 1 (clean text without markdown)",
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
  "event_type": "<string: the event type being handled (e.g., 'explore', 'create', 'chat', 'develop')>",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
"""
        template = get_prompt_template("task_regression.md", fallback)
        prompt += template.format(
            env_vars_str=env_vars_str,
            test_steps_str=test_steps_str,
            test_logs=test_logs,
            feedback_input=feedback_input,
            file_tree_str=file_tree_str,
            snippets_str=snippets_str
        )
    elif command == "chat":
        messages = data.get("messages", [])
        user_msg = messages[-1].get("content", "") if messages else ""
        fallback = """The user says: "{user_msg}"

Please respond to the user naturally and helpfully.
You MUST respond ONLY with a JSON block matching this exact schema:
```json
{{
  "chat": "Your textual response here",
  "event_type": "<string: the event type being handled (e.g., 'explore', 'create', 'chat', 'develop')>",
  "needs_references": "<boolean: true if you need to read lazy-loaded files>",
  "requested_files": ["<string: list of relative file paths to read>"]
}}
```
"""
        template = get_prompt_template("chat.md", fallback)
        prompt += template.format(user_msg=user_msg)
    else:
        prompt += "Please process this request. Respond only with JSON block."

    model_name = data.get('model', '')
    from config import check_vllm_url, check_api_key_gemini, check_api_key_anthropic
    
    if model_name:
        is_gem_model = "gemini" in model_name.lower() or "flash" in model_name.lower() or "pro" in model_name.lower()
        is_cld_model = model_name.startswith("claude-")
        
        if is_gem_model and not check_api_key_gemini():
            if check_vllm_url():
                model_name = os.environ.get("VLLM_DEFAULT_MODEL", "devstral")
            elif check_api_key_anthropic():
                model_name = 'claude-3-5-sonnet-latest'
            else:
                model_name = ''
        elif is_cld_model and not check_api_key_anthropic():
            if check_vllm_url():
                model_name = os.environ.get("VLLM_DEFAULT_MODEL", "devstral")
            elif check_api_key_gemini():
                model_name = 'gemini-3.1-flash-lite'
            else:
                model_name = ''

    if not model_name:
        if check_vllm_url() and not check_api_key_gemini() and not check_api_key_anthropic():
            model_name = os.environ.get("VLLM_DEFAULT_MODEL", "devstral")
        elif check_api_key_anthropic():
            model_name = 'claude-3-5-sonnet-latest'
        elif check_api_key_gemini():
            model_name = 'gemini-3.1-flash-lite'
        else:
            model_name = os.environ.get("VLLM_DEFAULT_MODEL", "devstral") if check_vllm_url() else 'gemini-2.5-flash'
            
    async def _execute_inference_inner(model_name, prompt):
        is_claude = model_name.startswith("claude-")
        is_gemini = "gemini" in model_name.lower() or "flash" in model_name.lower() or "pro" in model_name.lower()
        vllm_default = os.environ.get("VLLM_DEFAULT_MODEL", "devstral")
        is_vllm = model_name == vllm_default or (check_vllm_url() and not is_claude and not is_gemini)
        
        # 1. Print and write prompt to debug-console
        prompt_log = f"=== PROMPT SENT TO LLM ===\nModel: {model_name}\n\n{prompt}\n=========================="
        
        # Write to stdout
        if os.environ.get("AGENT_DEBUG", "true").lower() == "true" or os.environ.get("DEBUG", "false").lower() == "true":
            print("======== DEBUG PROMPT ========")
            print(prompt)
            print("==============================")
            sys.stdout.flush()

        # Write to WORKFLOW_STATE debug console
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        if "debug_logs" not in WORKFLOW_STATE:
            WORKFLOW_STATE["debug_logs"] = ""
        WORKFLOW_STATE["debug_logs"] = f"[{timestamp}] {prompt_log}\n\n" + WORKFLOW_STATE["debug_logs"]

        response_text = ""
        if is_claude:
            try:
                response_text = await call_claude_async(model_name, prompt)
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower() or "limit" in error_msg.lower():
                    print(f"Quota exceeded or model {model_name} not available. Falling back to claude-3-5-haiku-latest...")
                    try:
                        response_text = await call_claude_async("claude-3-5-haiku-latest", prompt)
                    except Exception as fallback_e:
                        response_text = f"Agent Generation Error (Fallback also failed): {str(fallback_e)}"
                else:
                    response_text = f"Agent Generation Error: {error_msg}"
        elif is_vllm:
            try:
                response_text = await call_vllm_async(model_name, prompt)
            except Exception as e:
                response_text = f"Agent Generation Error (VLLM): {str(e)}"
        else:
            try:
                from google import genai
                from google.genai import types
                client = genai.Client()
            except ImportError:
                response_text = "Error: google-genai is not installed in the environment."

            if not response_text:
                try:
                    model_id = model_name
                    thinking_level = None
                    
                    if model_name == "Gemini 3.1 Pro (High)":
                        model_id = "gemini-3.1-pro-preview"
                        thinking_level = "HIGH"
                    elif model_name == "Gemini 3.1 Pro (Low)":
                        model_id = "gemini-3.1-pro-preview"
                        thinking_level = "LOW"
                    elif model_name == "Gemini 3.5 flash (High)":
                        model_id = "gemini-3.5-flash"
                        thinking_level = "HIGH"
                    elif model_name == "Gemini 3.5 flash (Medium)":
                        model_id = "gemini-3.5-flash"
                        thinking_level = "MEDIUM"
                    elif model_name == "Gemini 3.5 flash (Low)":
                        model_id = "gemini-3.5-flash"
                        thinking_level = "LOW"
                    else:
                        if ":" in model_id:
                            base_model, level = model_id.rsplit(":", 1)
                            level_upper = level.upper()
                            if level_upper in ["HIGH", "MEDIUM", "LOW"]:
                                model_id = base_model
                                thinking_level = level_upper
                            elif level_upper in ["DEFAULT", "NONE"]:
                                model_id = base_model
                                thinking_level = None
                            else:
                                model_id = base_model
                                thinking_level = None

                    config_kwargs = {
                        "temperature": 0.0,
                        "tools": [interactive_search, list_directory, glob_search, perform_local_recursive_search, apply_patch]
                    }
                    if thinking_level:
                        config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=thinking_level)

                    chat = client.aio.chats.create(
                        model=model_id,
                        config=types.GenerateContentConfig(**config_kwargs)
                    )
                    response = await chat.send_message(prompt)
                    response_text = response.text
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "quota" in error_msg.lower() or "not found" in error_msg.lower():
                        print(f"Quota exceeded or model {model_name} not available. Falling back to gemini-2.5-pro...")
                        try:
                            chat_fallback = client.aio.chats.create(
                                model="gemini-2.5-pro",
                                config=types.GenerateContentConfig(
                                    temperature=0.0,
                                    tools=[interactive_search, list_directory, glob_search, perform_local_recursive_search, apply_patch]
                                )
                            )
                            fallback_response = await chat_fallback.send_message(prompt)
                            response_text = fallback_response.text
                        except Exception as fallback_e:
                            response_text = f"Agent Generation Error (Fallback also failed): {str(fallback_e)}"
                    else:
                        response_text = f"Agent Generation Error: {error_msg}"

        # 2. Print and write response to debug-console
        response_log = f"=== RESPONSE FROM LLM ===\nModel: {model_name}\n\n{response_text}\n========================="
        
        if os.environ.get("AGENT_DEBUG", "true").lower() == "true" or os.environ.get("DEBUG", "false").lower() == "true":
            print("======== DEBUG LLM RESPONSE ========")
            print(response_text)
            print("====================================")
            sys.stdout.flush()
            
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        WORKFLOW_STATE["debug_logs"] = f"[{timestamp}] {response_log}\n\n" + WORKFLOW_STATE["debug_logs"]

        return response_text

    # Determine Stage 1 model (use fast Gemini 3.5 Flash for structuring, unless using a non-Gemini environment)
    stage1_model = model_name
    if ("pro" in model_name.lower() or "claude" in model_name.lower() or "sonnet" in model_name.lower()) and check_api_key_gemini():
        stage1_model = "gemini-3.5-flash"
        
    print(f"[Agent Router] Model Grading: Stage 1 = {stage1_model}, Stage 2 = {model_name}")
    sys.stdout.flush()

    # Stage 1 execution (Fast Structure Assessment)
    response_text = await _execute_inference_inner(stage1_model, prompt)
    
    # 2-Stage dynamic reference loop check
    try:
        # Helper to extract JSON block cleanly
        def extract_json_block(text):
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
            if not json_match:
                json_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
            if json_match:
                return json_match.group(1).strip()
            
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                return text[start_idx:end_idx+1]
            return text.strip()
            
        json_str = extract_json_block(response_text)
        
        # Robust parsing with graceful fallback
        parsed = {}
        try:
            parsed = json.loads(json_str)
        except Exception as json_err:
            print(f"[Agent Router] JSON Parse Error: {str(json_err)}. Attempting standard extraction...")
            sys.stdout.flush()
            # Try to grab needs_references using regex
            import re
            ref_match = re.search(r'"needs_references"\s*:\s*(true|false)', json_str, re.IGNORECASE)
            if ref_match:
                parsed["needs_references"] = (ref_match.group(1).lower() == "true")
            # Try to grab requested_files
            files_match = re.search(r'"requested_files"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
            if files_match:
                files_content = files_match.group(1)
                parsed["requested_files"] = [f.strip(' "\'') for f in files_content.split(',') if f.strip()]
        
        # Enforce exactly 1 reference load depth (infinite loop protection)
        if parsed.get("needs_references") is True and parsed.get("requested_files"):
            requested_files = parsed.get("requested_files")
            references_list = data.get("references", [])
            
            print(f"[Server Stage 1] Model requested reference files: {requested_files}")
            sys.stdout.flush()
            
            # Securely load the contents of the requested files
            loaded_context = load_requested_files(requested_files, references_list)
            
            if loaded_context:
                prompt_stage2 = prompt + f"\n\n=========================================\n"
                prompt_stage2 += f"CONTENTS OF THE REQUESTED REFERENCE FILES:\n{loaded_context}"
                prompt_stage2 += f"=========================================\n\n"
                prompt_stage2 += f"The reference files you requested have been loaded above. Please proceed with analyzing them and generating your final response now. Set `\"needs_references\": false` and `\"requested_files\": []`."
                
                print(f"[Server Stage 2] Triggering follow-up model inference ({model_name}) with loaded context...")
                sys.stdout.flush()
                
                # Execute Stage 2 with the loaded files in context (Main brain model)
                response_text = await _execute_inference_inner(model_name, prompt_stage2)
    except Exception as e:
        # If parsing or execution fails in Stage 1, fall back gracefully to the Stage 1 response
        print(f"[Agent Router] Exception in dynamic routing loop: {str(e)}")
        sys.stdout.flush()
        
    return response_text
