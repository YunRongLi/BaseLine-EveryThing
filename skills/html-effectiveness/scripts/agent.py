import os, json, asyncio, httpx
from state import WORKFLOW_STATE
from utils import resolve_references
from search_tools import interactive_search
from recursive_search import perform_local_recursive_search
from config import check_api_key, check_api_key_anthropic, check_api_key_gemini

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

async def call_agent_async(command, data):
    if not check_api_key():
        return "Error: No API key is configured (Neither GEMINI_API_KEY nor ANTHROPIC_ADMIN_API_KEY)."

    lang = data.get('language', 'en')
    lang_instruction = "Traditional Chinese (zh-TW)" if lang == 'zh' else "English (en)"
    
    prompt = f"CRITICAL: The user's preferred language is {lang_instruction}. You MUST write all titles, items, summaries, questions, and content inside the JSON in {lang_instruction}. Do NOT use any emojis or icons. IMPORTANT: Do NOT include any raw Markdown syntax (such as '#', '##', '###', '**', or bullet points '- ') inside your JSON string values. Return clean text descriptions that will be directly displayed in textareas.\n\n"
    
    # Inject reference context if available
    references_list = data.get("references", [])
    ref_context = resolve_references(references_list)
    if ref_context:
        prompt += f"========================================= \nIMPORT REFERENCE MATERIALS & ARCHITECTURAL CONTEXT:\n{ref_context}\n=========================================\n\n"

    if command == "task-create":
        prompt += f"""Analyze this task and generate the specifications.
Task Title: {data.get('title')}
Category: {data.get('category')}
Goal: {data.get('goal')}
Context: {data.get('context')}

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
  }}
}}
```
Provide at least 3-4 sections detailing the full specification, functional scope, and data formats. 
CRITICAL RULE FOR QUESTIONS: Limit the "open_questions" list strictly to at most three (3) of the most important architectural or functional questions that must need the user to decide. Otherwise, you should research contents provided by the user, like local files or codes. Do not ask more than three.
CRITICAL RULE FOR ITEMS: Group related details (e.g., a feature and its sub-descriptions) into a single, cohesive paragraph string. Let the AI determine the optimal semantic grouping. Do NOT blindly split every single sentence or newline into a separate item.
Keep all items clean, high-technical, and professional. Do NOT use markdown.
"""
    elif command == "task-spec":
        is_update = data.get('is_update', False)
        sections = data.get('sections', [])
        scoping_input = data.get('scoping_input', '')
        
        sections_str = json.dumps(sections, indent=2, ensure_ascii=False)
        
        if is_update:
            prompt += f"""The user wants to UPDATE the task specifications based on their feedback.
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
  }}
}}
```
"""
        else:
            prompt += f"""The user has finalized the task specifications and wants to generate the prototype and architectural design.
Final Specification Sections:
{sections_str}

User's Scoping Feedback/Instructions:
{scoping_input}

Analyze these specifications and design the Prototype architecture, workflow steps, file tree list, and core logic snippets.
CRITICAL RULE FOR QUESTIONS: Limit the "open_questions" list strictly to at most three (3) of the most important architectural questions that must need the user to decide. Otherwise, you should research contents provided by the user, like local files or codes. Do not ask more than three.
You MUST respond ONLY with a JSON block in this schema:
```json
{{
  "prototype": {{
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
  }}
}}
```
"""
    elif command == "task-prototype":
        is_update = data.get('is_update', False)
        workflow_steps = data.get('workflow_steps', [])
        file_tree = data.get('file_tree', [])
        code_snippets = data.get('code_snippets', [])
        feedback_input = data.get('feedback_input', '')
        
        workflow_str = json.dumps(workflow_steps, indent=2, ensure_ascii=False)
        file_tree_str = json.dumps(file_tree, indent=2, ensure_ascii=False)
        snippets_str = json.dumps(code_snippets, indent=2, ensure_ascii=False)
        
        if is_update:
            prompt += f"""The user wants to UPDATE the prototype design and code based on their feedback.
Current Workflow Steps:
{workflow_str}

Current File Tree:
{file_tree_str}

Current Code Snippets:
{snippets_str}

User's Feedback/Instructions:
{feedback_input}

Analyze the feedback and output the updated prototype.
CRITICAL RULE FOR QUESTIONS: Limit the "open_questions" list strictly to at most three (3) of the most important remaining questions that must need the user to decide. Otherwise, you should research contents provided by the user, like local files or codes. Do not ask more than three.
CRITICAL RULE: Group related details into cohesive paragraph strings. Let the AI determine the optimal semantic grouping. Do NOT blindly split every single sentence or newline into a separate item.
You MUST respond ONLY with a JSON block in this schema:
```json
{{
  "prototype": {{
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
  }}
}}
```
"""
        else:
            prompt += f"""The user has approved the prototype and submitted final implementation and execution instructions.
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
  }}
}}
```
"""
    else:
        prompt += "Please process this request. Respond only with JSON block."

    model_name = data.get('model', '')
    if not model_name:
        if check_api_key_anthropic():
            model_name = 'claude-3-5-sonnet-latest'
        elif check_api_key_gemini():
            model_name = 'gemini-3.1-flash-lite'
        else:
            model_name = 'gemini-2.5-flash'
            
    is_claude = model_name.startswith("claude-")
    
    if os.environ.get("AGENT_DEBUG", "true").lower() == "true" or os.environ.get("DEBUG", "false").lower() == "true":
        print("======== DEBUG PROMPT ========")
        print(prompt)
        print("==============================")

    if is_claude:
        try:
            return await call_claude_async(model_name, prompt)
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower() or "limit" in error_msg.lower():
                print(f"Quota exceeded or model {model_name} not available. Falling back to claude-3-5-haiku-latest...")
                try:
                    return await call_claude_async("claude-3-5-haiku-latest", prompt)
                except Exception as fallback_e:
                    return f"Agent Generation Error (Fallback also failed): {str(fallback_e)}"
            return f"Agent Generation Error: {error_msg}"
    else:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client()
        except ImportError:
            return "Error: google-genai is not installed in the environment."

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
                        # Fallback for unrecognized suffix
                        model_id = base_model
                        thinking_level = None


            config_kwargs = {
                "temperature": 0.0,
                "tools": [interactive_search, perform_local_recursive_search]
            }
            if thinking_level:
                config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=thinking_level)

            chat = client.aio.chats.create(
                model=model_id,
                config=types.GenerateContentConfig(**config_kwargs)
            )
            response = await chat.send_message(prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower() or "not found" in error_msg.lower():
                print(f"Quota exceeded or model {model_name} not available. Falling back to gemini-2.5-pro...")
                try:
                    chat_fallback = client.aio.chats.create(
                        model="gemini-2.5-pro",
                        config=types.GenerateContentConfig(
                            temperature=0.0,
                            tools=[interactive_search, perform_local_recursive_search]
                        )
                    )
                    fallback_response = await chat_fallback.send_message(prompt)
                    return fallback_response.text
                except Exception as fallback_e:
                    return f"Agent Generation Error (Fallback also failed): {str(fallback_e)}"
            return f"Agent Generation Error: {error_msg}"
