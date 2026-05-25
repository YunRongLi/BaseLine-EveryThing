import os, sys, json, asyncio, urllib.parse
from http.server import SimpleHTTPRequestHandler
from state import WORKFLOW_STATE
from agent import call_agent_async
from recursive_search import perform_local_recursive_search
from config import check_api_key_anthropic, check_api_key_gemini

class AgentHTTPRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urllib.parse.urlparse(path)
        clean_path = parsed.path.lstrip('/')
        
        if clean_path in ["task_create.html", "task_spec.html", "task_prototype.html", "recursive_search.html"]:
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
            
        elif clean_path == "api/debug":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success', 'logs': WORKFLOW_STATE.get("debug_logs", "")}).encode('utf-8'))
            return
            
        elif clean_path in ["", "index.html", "create"]:
            self.path = "/task_create.html"
        elif clean_path == "spec":
            self.path = "/task_spec.html"
        elif clean_path == "prototype":
            self.path = "/task_prototype.html"
            
        if clean_path == 'api/models':
            has_gemini = check_api_key_gemini()
            has_anthropic = check_api_key_anthropic()
            
            if has_anthropic and not has_gemini:
                default_model = "claude-3-5-sonnet-latest"
            elif has_gemini:
                default_model = "Gemini 3.1 Pro (High)"
            else:
                default_model = "Gemini 3.1 Pro (High)"
                
            models = []
            common_claude = ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"]
            
            try:
                if has_gemini:
                    models = [
                        "Gemini 3.1 Pro (High)",
                        "Gemini 3.1 Pro (Low)",
                        "Gemini 3.5 flash (High)",
                        "Gemini 3.5 flash (Medium)",
                        "Gemini 3.5 flash (Low)"
                    ]
                else:
                    models = []
                
                if has_anthropic:
                    for pm in reversed(common_claude):
                        if pm not in models:
                            models.insert(0, pm)
            except Exception as e:
                print(f"Error fetching models: {e}")
                models = [
                    "Gemini 3.1 Pro (High)",
                    "Gemini 3.5 flash (Medium)"
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
            
        elif clean_path == 'api/state':
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
            
        elif self.path == '/api/state/import':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                state_data = payload.get('state', {})
                if state_data:
                    for k in WORKFLOW_STATE.keys():
                        if k in state_data:
                            WORKFLOW_STATE[k] = state_data[k]
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'success', 'message': 'State imported successfully.'}).encode('utf-8'))
                else:
                    raise ValueError("No state data found in payload.")
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
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
                    print("======== DEBUG RESPONSE ========")
                    print(response_text)
                    print("================================")
                    sys.stdout.flush()
                
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
                
        elif self.path == '/api/recursive-search':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
                query = payload.get('query', '')
                target_count = int(payload.get('target_count', 6))
                max_iterations = int(payload.get('max_iterations', 3))
                weights = payload.get('weights', {"rel": 50, "pri": 30, "snr": 20})
                language = payload.get('language', 'en')
                
                if not query:
                    raise ValueError("Search query is required.")
                
                result = perform_local_recursive_search(
                    query=query,
                    target_count=target_count,
                    max_iterations=max_iterations,
                    weights=weights,
                    language=language
                )
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
                
        elif self.path == '/api/debug':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
                log_msg = payload.get('message', '')
                clear = payload.get('clear', False)
                
                if "debug_logs" not in WORKFLOW_STATE:
                    WORKFLOW_STATE["debug_logs"] = ""
                    
                if clear:
                    WORKFLOW_STATE["debug_logs"] = ""
                elif log_msg:
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                    WORKFLOW_STATE["debug_logs"] = f"[{timestamp}] {log_msg}\\n\\n" + WORKFLOW_STATE["debug_logs"]
                    
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode('utf-8'))
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
