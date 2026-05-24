import os
import sys
import json
import asyncio
import urllib.parse
from http.server import SimpleHTTPRequestHandler, HTTPServer

def load_env():
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, val = line.split('=', 1)
                        os.environ[key.strip()] = val.strip()

def check_api_key_gemini():
    return "GEMINI_API_KEY" in os.environ

def check_api_key_anthropic():
    return "ANTHROPIC_ADMIN_API_KEY" in os.environ or "ANTHROPIC_API_KEY" in os.environ

def check_api_key():
    return check_api_key_gemini() or check_api_key_anthropic()

# Global Memory state for the workflow (completely structured JSON)
WORKFLOW_STATE = {
    "current_stage": "create", # "create", "spec", "prototype", "completed"
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
    "completed_data": {
        "summary_items": [],         # [ "item 1", "item 2" ]
        "created_files": [],         # [ "file 1", "file 2" ]
        "verification_results": []   # [ "result 1", "result 2" ]
    },
    "references": [] # [{ "type": "local/url", "value": "..." }]
}

def resolve_references(references_list):
    """
    Recursively resolves local file/folder paths and reads their content,
    or formats URLs as high-quality architectural context.
    """
    context_str = ""
    if not references_list:
        return context_str
        
    for ref in references_list:
        ref_type = ref.get("type")
        path_or_url = ref.get("value", "").strip()
        if not path_or_url:
            continue
            
        if ref_type == "local":
            abs_path = os.path.abspath(path_or_url)
            # Security bounding check: must be inside workspace Cwd
            if abs_path.startswith(os.getcwd()) and os.path.exists(abs_path):
                if os.path.isfile(abs_path):
                    try:
                        with open(abs_path, 'r', encoding='utf-8') as f:
                            context_str += f"### REFERENCE LOCAL FILE: {path_or_url}\n```\n{f.read()}\n```\n\n"
                    except Exception as e:
                        context_str += f"### REFERENCE FILE ERROR: {path_or_url} (Could not read: {str(e)})\n\n"
                elif os.path.isdir(abs_path):
                    context_str += f"### REFERENCE LOCAL DIRECTORY: {path_or_url}\n"
                    try:
                        for root, dirs, files in os.walk(abs_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                rel_path = os.path.relpath(file_path, os.getcwd())
                                # Exclude binary / large files
                                if file.endswith(('.py', '.html', '.css', '.js', '.md', '.txt', '.json', '.yml', '.yaml', '.sh', '.bat')):
                                    try:
                                        with open(file_path, 'r', encoding='utf-8') as f:
                                            context_str += f"#### File: {rel_path}\n```\n{f.read()}\n```\n"
                                    except Exception:
                                        pass
                    except Exception as e:
                        context_str += f"Failed to recursively read directory {path_or_url}: {str(e)}\n\n"
            else:
                context_str += f"### REFERENCE LOCAL PATH (RESTRICTED OR NOT FOUND): {path_or_url}\n\n"
        elif ref_type == "url":
            context_str += f"### REFERENCE EXTERNAL SOURCE/URL: {path_or_url}\n(Please use this URL/source repo as standard architectural reference.)\n\n"
            
    return context_str

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
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_filename = f"debug_prompt_{command}_{timestamp}.md"
        debug_filepath = os.path.abspath(debug_filename)
        try:
            with open(debug_filepath, 'w', encoding='utf-8') as df:
                df.write(prompt)
            print(f"Debug: Stored agent prompt in {debug_filepath}")
        except Exception as df_err:
            print(f"Error saving debug prompt file: {df_err}")

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
            client = genai.Client()
        except ImportError:
            return "Error: google-genai is not installed in the environment."

        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                print(f"Quota exceeded or model {model_name} not available. Falling back to gemini-2.5-flash...")
                try:
                    fallback_response = await client.aio.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                    )
                    return fallback_response.text
                except Exception as fallback_e:
                    return f"Agent Generation Error (Fallback also failed): {str(fallback_e)}"
            return f"Agent Generation Error: {error_msg}"

class AgentHTTPRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urllib.parse.urlparse(path)
        clean_path = parsed.path.lstrip('/')
        
        if clean_path in ["task_create.html", "task_spec.html", "task_prototype.html"]:
            local_path = os.path.abspath(clean_path)
            if os.path.exists(local_path):
                return local_path
            
            template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")
            return os.path.abspath(os.path.join(template_dir, clean_path))
            
        return super().translate_path(path)

    def do_GET(self):
        global WORKFLOW_STATE
        clean_path = urllib.parse.urlparse(self.path).path.lstrip('/')
        
        if clean_path == "reset":
            WORKFLOW_STATE = {
                "current_stage": "create",
                "create_data": {
                    "title": "",
                    "category": "Feature",
                    "goal": "",
                    "context": ""
                },
                "spec_data": {
                    "sections": [],
                    "open_questions": []
                },
                "prototype_data": {
                    "workflow_steps": [],
                    "file_tree": [],
                    "code_snippets": [],
                    "open_questions": []
                },
                "completed_data": {
                    "summary_items": [],
                    "created_files": [],
                    "verification_results": []
                },
                "references": []
            }
            self.send_response(302)
            self.send_header('Location', '/create')
            self.end_headers()
            return
            
        elif clean_path in ["", "index.html", "create"]:
            self.path = "/task_create.html"
        elif clean_path == "spec":
            self.path = "/task_spec.html"
        elif clean_path == "prototype":
            self.path = "/task_prototype.html"
            
        if self.path == '/api/models':
            has_gemini = check_api_key_gemini()
            has_anthropic = check_api_key_anthropic()
            
            if has_anthropic and not has_gemini:
                default_model = "claude-3-5-sonnet-latest"
            elif has_gemini:
                default_model = "gemini-3.1-flash-lite"
            else:
                default_model = "gemini-2.5-flash"
                
            models = []
            common_claude = ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"]
            
            try:
                if has_gemini:
                    from google import genai
                    client = genai.Client()
                    models = [
                        m.name.replace('models/', '') 
                        for m in client.models.list() 
                        if 'gemini' in m.name and 'embedding' not in m.name
                    ]
                
                common_models = ["gemini-3.5-flash", "gemini-3.1-pro-preview", "gemini-3.1-flash-lite", "gemini-2.5-pro", "gemini-2.5-flash"]
                for pm in reversed(common_models):
                    if pm not in models:
                        models.insert(0, pm)
            except Exception as e:
                print(f"Error fetching models: {e}")
                models = [
                    "gemini-3.1-flash-lite",
                    "gemini-3.5-flash",
                    "gemini-2.5-pro",
                    "gemini-2.5-flash",
                    "gemini-2.0-flash"
                ]
            
            # Add Claude models if Anthropic is supported or available
            for cm in reversed(common_claude):
                if cm not in models:
                    models.insert(0, cm)
                    
            if default_model not in models:
                models.insert(0, default_model)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            import time
            if not hasattr(self.__class__, 'SERVER_INSTANCE_ID'):
                self.__class__.SERVER_INSTANCE_ID = str(int(time.time()))
            
            self.wfile.write(json.dumps({
                'status': 'success', 
                'models': models,
                'default_model': default_model,
                'server_instance_id': self.__class__.SERVER_INSTANCE_ID
            }).encode('utf-8'))
            return
            
        elif self.path == '/api/state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'success',
                'state': WORKFLOW_STATE
            }).encode('utf-8'))
            return

        super().do_GET()

    def do_POST(self):
        global WORKFLOW_STATE
        if self.path == '/api/state/reset':
            WORKFLOW_STATE = {
                "current_stage": "create",
                "create_data": {
                    "title": "",
                    "category": "Feature",
                    "goal": "",
                    "context": ""
                },
                "spec_data": {
                    "sections": [],
                    "open_questions": []
                },
                "prototype_data": {
                    "workflow_steps": [],
                    "file_tree": [],
                    "code_snippets": [],
                    "open_questions": []
                },
                "completed_data": {
                    "summary_items": [],
                    "created_files": [],
                    "verification_results": []
                },
                "references": []
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success', 'message': 'Workflow state reset.'}).encode('utf-8'))
            return
            
        elif self.path == '/api/agent':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
                command = payload.get('command', '')
                data = payload.get('data', {})
                
                # Capture references in the state
                if "references" in data:
                    WORKFLOW_STATE["references"] = data.get("references", [])
                
                # Make sure the payload contains the complete active references for prompt generation
                data["references"] = WORKFLOW_STATE["references"]
                
                # Execute agent call
                response_text = asyncio.run(call_agent_async(command, data))
                
                # Debug logging of agent response
                if os.environ.get("AGENT_DEBUG", "true").lower() == "true" or os.environ.get("DEBUG", "false").lower() == "true":
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    debug_filename = f"debug_response_{command}_{timestamp}.md"
                    debug_filepath = os.path.abspath(debug_filename)
                    try:
                        with open(debug_filepath, 'w', encoding='utf-8') as df:
                            df.write(response_text)
                        print(f"Debug: Stored agent response in {debug_filepath}")
                        sys.stdout.flush()
                        response_text_clean = response_text + f"\n\n[System Debug: Stored agent response in {debug_filename}]"
                    except Exception as df_err:
                        print(f"Error saving debug file: {df_err}")
                        sys.stdout.flush()
                        response_text_clean = response_text
                else:
                    response_text_clean = response_text
                
                # Parse JSON response from agent to update state
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL | re.IGNORECASE)
                if not json_match:
                    json_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL | re.IGNORECASE)
                
                if json_match:
                    json_str = json_match.group(1).strip()
                else:
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}')
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx+1]
                    else:
                        json_str = response_text.strip()
                
                try:
                    parsed_response = json.loads(json_str)
                    
                    if command == "task-create":
                        WORKFLOW_STATE["create_data"] = {
                            "title": data.get("title", ""),
                            "category": data.get("category", "Feature"),
                            "goal": data.get("goal", ""),
                            "context": data.get("context", "")
                        }
                        spec_info = parsed_response.get("spec", {})
                        WORKFLOW_STATE["spec_data"] = {
                            "sections": spec_info.get("sections", []),
                            "open_questions": spec_info.get("open_questions", [])
                        }
                        WORKFLOW_STATE["current_stage"] = "spec"
                        
                    elif command == "task-spec":
                        is_update = data.get("is_update", False)
                        if is_update:
                            spec_info = parsed_response.get("spec", {})
                            WORKFLOW_STATE["spec_data"] = {
                                "sections": spec_info.get("sections", []),
                                "open_questions": spec_info.get("open_questions", [])
                            }
                        else:
                            proto_info = parsed_response.get("prototype", {})
                            WORKFLOW_STATE["prototype_data"] = {
                                "workflow_steps": proto_info.get("workflow_steps", []),
                                "file_tree": proto_info.get("file_tree", []),
                                "code_snippets": proto_info.get("code_snippets", []),
                                "open_questions": proto_info.get("open_questions", [])
                            }
                            WORKFLOW_STATE["current_stage"] = "prototype"
                            
                    elif command == "task-prototype":
                        is_update = data.get("is_update", False)
                        if is_update:
                            proto_info = parsed_response.get("prototype", {})
                            WORKFLOW_STATE["prototype_data"] = {
                                "workflow_steps": proto_info.get("workflow_steps", []),
                                "file_tree": proto_info.get("file_tree", []),
                                "code_snippets": proto_info.get("code_snippets", []),
                                "open_questions": proto_info.get("open_questions", [])
                            }
                        else:
                            completed_info = parsed_response.get("completed", {})
                            WORKFLOW_STATE["completed_data"] = {
                                "summary_items": completed_info.get("summary_items", []),
                                "created_files": completed_info.get("created_files", []),
                                "verification_results": completed_info.get("verification_results", [])
                            }
                            WORKFLOW_STATE["current_stage"] = "completed"
                            
                            # Write approved files into workspace
                            try:
                                code_snippets = WORKFLOW_STATE["prototype_data"].get("code_snippets", [])
                                workspace_path = data.get("workspace_path", ".")
                                base_workspace = os.path.abspath(workspace_path)
                                for snippet in code_snippets:
                                    filename = snippet.get("filename")
                                    code = snippet.get("code")
                                    if filename and code:
                                        clean_filename = filename.lstrip('/\\')
                                        filepath = os.path.abspath(os.path.join(base_workspace, clean_filename))
                                        if filepath.startswith(base_workspace):
                                            os.makedirs(os.path.dirname(filepath), exist_ok=True)
                                            with open(filepath, 'w', encoding='utf-8') as f:
                                                f.write(code)
                                            print(f"System: Automatically wrote {filename} to {base_workspace}")
                            except Exception as exec_err:
                                print(f"Error executing final workspace changes: {exec_err}")
                            
                except Exception as parse_err:
                    print(f"Error parsing agent JSON response: {parse_err}")
                    sys.stdout.flush()
                    response_text_clean += f"\n\n[System Error: Failed to parse Agent response as JSON. Error: {str(parse_err)}]"
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'response': response_text_clean}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
                
        elif self.path == '/api/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
                filepath = payload.get('filepath', '')
                content = payload.get('content', '')
                
                if not filepath:
                    raise ValueError("Filepath is required.")
                
                abs_path = os.path.abspath(filepath)
                if not abs_path.startswith(os.getcwd()):
                    raise PermissionError("Access outside workspace is restricted.")
                
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'message': f'File saved to {filepath}'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def find_free_port(start_port=8000):
    import socket
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except socket.error:
                port += 1
    raise RuntimeError("No free ports found.")

def listen_for_eof(server):
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
    except (IOError, ValueError, KeyboardInterrupt):
        pass
    finally:
        print("\nEOF received. Shutting down server.")
        sys.stdout.flush()
        server.shutdown()

def main():
    load_env()
    
    if not check_api_key():
        print("ERROR: Neither GEMINI_API_KEY nor ANTHROPIC_ADMIN_API_KEY environment variable is set.")
        print("Please configure at least one API key in your system environment or within a local .env file.")
        print("Exiting server startup.")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
        if os.path.isdir(target_dir):
            os.chdir(target_dir)
            
    port = find_free_port()
    server = HTTPServer(('127.0.0.1', port), AgentHTTPRequestHandler)
    print(f"Server started at http://localhost:{port}")
    print("Press Ctrl+C or Ctrl+D (Ctrl+Z + Enter on Windows) to stop the server.")
    sys.stdout.flush()
    
    import threading
    stdin_thread = threading.Thread(target=listen_for_eof, args=(server,))
    stdin_thread.daemon = True
    stdin_thread.start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Shutting down server.")
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
