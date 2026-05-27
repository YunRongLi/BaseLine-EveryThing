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
        
        if clean_path in ["task_explore.html", "task_create.html", "task_spec.html", "task_develop.html", "task_testing.html", "task_workflow.html", "recursive_search.html", "sessions.js"]:
            local_path = os.path.abspath(clean_path)
            if os.path.exists(local_path):
                return local_path
            
            template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")
            return os.path.abspath(os.path.join(template_dir, clean_path))
            
        return super().translate_path(path)

    def log_message(self, format, *args):
        # Ignore polling requests for api/debug to prevent log spamming loop
        if len(args) > 0 and isinstance(args[0], str) and "api/debug" in args[0]:
            return
        
        # Write standard HTTP logs to stdout instead of stderr to prevent [ERROR] prefixes in UI
        sys.stdout.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args))



    def load_session_to_workflow_state(self, session_id=None):
        import session_manager
        from state import WORKFLOW_STATE
        if not session_id:
            if "?" in self.path:
                from urllib.parse import parse_qs, urlparse
                query = parse_qs(urlparse(self.path).query)
                session_id = query.get('session_id', [None])[0]
        if not session_id:
            session_id = session_manager.get_active_session_id()
        
        session_data = session_manager.load_session(session_id)
        
        # Clear and update WORKFLOW_STATE in place to keep the same dict object
        WORKFLOW_STATE.clear()
        WORKFLOW_STATE.update(session_data["state"])
        
        self.current_session_id = session_id
        self.current_session_data = session_data

    def save_workflow_state_to_session(self):
        if hasattr(self, 'current_session_id') and hasattr(self, 'current_session_data'):
            import session_manager
            from state import WORKFLOW_STATE
            self.current_session_data["state"] = dict(WORKFLOW_STATE)
            self.current_session_data["current_stage"] = WORKFLOW_STATE.get("current_stage", "explore")
            session_manager.save_session(self.current_session_id, self.current_session_data)

    def do_GET(self):
        self.load_session_to_workflow_state()
        try:
            self._handle_do_GET()
        finally:
            self.save_workflow_state_to_session()

    def _handle_do_GET(self):
        global WORKFLOW_STATE
        clean_path = urllib.parse.urlparse(self.path).path.lstrip('/')
        
        if clean_path == "api/sessions":
            import session_manager
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'success',
                'sessions': session_manager.list_sessions(),
                'active_session_id': session_manager.get_active_session_id()
            }).encode('utf-8'))
            return
            
        elif clean_path == "reset":
            WORKFLOW_STATE.clear()
            WORKFLOW_STATE.update({
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
                "develop_data": {
                    "workflow_steps": [],
                    "file_tree": [],
                    "code_snippets": [],
                    "open_questions": []
                },
                "testing_data": {
                    "test_steps": [],
                    "env_vars": {},
                    "test_runs": [],
                    "remediation_instructions": "",
                    "regression_baseline": []
                },
                "completed_data": {
                    "summary_items": [],
                    "created_files": [],
                    "verification_results": []
                },
                "references": []
            })
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
            
        elif clean_path in ["", "index.html", "explore", "task-explore", "task_explore"]:
            self.path = "/task_explore.html"
        elif clean_path in ["create", "task-create", "task_create"]:
            self.path = "/task_create.html"
        elif clean_path in ["spec", "task-spec", "task_spec"]:
            self.path = "/task_spec.html"
        elif clean_path in ["develop", "develop", "task-develop", "task_develop"]:
            self.path = "/task_develop.html"
        elif clean_path in ["testing", "task-testing", "task_testing"]:
            self.path = "/task_testing.html"
        elif clean_path in ["workflow", "task-workflow", "task_workflow"]:
            self.path = "/task_workflow.html"
            
        if clean_path == 'api/models':
            from config import check_vllm_url
            has_gemini = check_api_key_gemini()
            has_anthropic = check_api_key_anthropic()
            has_vllm = check_vllm_url()
            
            if has_vllm and not has_gemini and not has_anthropic:
                default_model = os.environ.get("VLLM_DEFAULT_MODEL", "devstral")
            elif has_anthropic and not has_gemini:
                default_model = "claude-3-5-sonnet-latest"
            elif has_gemini:
                default_model = "Gemini 3.1 Pro (High)"
            else:
                default_model = os.environ.get("VLLM_DEFAULT_MODEL", "devstral") if has_vllm else "Gemini 3.1 Pro (High)"
                
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
            if has_anthropic:
                for cm in reversed(common_claude):
                    if cm not in models:
                        models.insert(0, cm)
            
            if has_vllm:
                vllm_m = os.environ.get("VLLM_DEFAULT_MODEL", "devstral")
                if vllm_m not in models:
                    models.insert(0, vllm_m)
                    
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
            
        elif clean_path == 'api/agent-config':
            import config
            config.load_env()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            cfg = {
                "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", ""),
                "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
                "VLLM_API_URL": os.environ.get("VLLM_API_URL", ""),
                "VLLM_DEFAULT_MODEL": os.environ.get("VLLM_DEFAULT_MODEL", "devstral")
            }
            
            avail = {
                "gemini": config.check_api_key_gemini(),
                "anthropic": config.check_api_key_anthropic(),
                "vllm": config.check_vllm_url()
            }
            
            self.wfile.write(json.dumps({
                'status': 'success',
                'config': cfg,
                'available_backends': avail
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
        import io, json
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''
        self.rfile = io.BytesIO(body)
        
        session_id = self.headers.get('Session-Id') or self.headers.get('x-session-id')
        if not session_id:
            try:
                payload = json.loads(body.decode('utf-8'))
                session_id = payload.get('session_id') or payload.get('data', {}).get('session_id')
            except Exception:
                pass
                
        self.load_session_to_workflow_state(session_id)
        try:
            self._handle_do_POST()
        finally:
            self.save_workflow_state_to_session()

    def _handle_do_POST(self):
        global WORKFLOW_STATE
        import session_manager
        
        if self.path == '/api/sessions/create':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            title = None
            try:
                payload = json.loads(post_data.decode('utf-8'))
                title = payload.get('title')
            except Exception:
                pass
            new_sess = session_manager.create_session(title)
            session_manager.set_active_session_id(new_sess["session_id"])
            
            # Immediately update the memory copy so the finally block saves it correctly
            self.current_session_id = new_sess["session_id"]
            self.current_session_data = new_sess
            WORKFLOW_STATE.clear()
            WORKFLOW_STATE.update(new_sess["state"])
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success', 'session': new_sess}).encode('utf-8'))
            return
            
        elif self.path == '/api/sessions/select':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            session_id = None
            try:
                payload = json.loads(post_data.decode('utf-8'))
                session_id = payload.get('session_id')
            except Exception:
                pass
            if session_id:
                session_manager.set_active_session_id(session_id)
                sess = session_manager.load_session(session_id)
                self.current_session_id = session_id
                self.current_session_data = sess
                WORKFLOW_STATE.clear()
                WORKFLOW_STATE.update(sess["state"])
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'session_id': session_id}).encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': 'Missing session_id'}).encode('utf-8'))
            return
            
        elif self.path == '/api/sessions/delete':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            session_id = None
            try:
                payload = json.loads(post_data.decode('utf-8'))
                session_id = payload.get('session_id')
            except Exception:
                pass
            if session_id:
                session_manager.delete_session(session_id)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': 'Missing session_id'}).encode('utf-8'))
            return

        elif self.path == '/api/agent-config':
            import config
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                cfg = payload.get('config', {})
                config.persist_env(cfg)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'message': 'Configuration updated.'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
            return

        if self.path == '/api/state/reset':
            WORKFLOW_STATE.clear()
            WORKFLOW_STATE.update({
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
                "develop_data": {
                    "workflow_steps": [],
                    "file_tree": [],
                    "code_snippets": [],
                    "open_questions": []
                },
                "testing_data": {
                    "test_steps": [],
                    "env_vars": {},
                    "test_runs": [],
                    "remediation_instructions": "",
                    "regression_baseline": []
                },
                "completed_data": {
                    "summary_items": [],
                    "created_files": [],
                    "verification_results": []
                },
                "references": []
            })
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
                
                # Pre-execute tests before agent analysis if command is task-regression
                if command == "task-regression":
                    print("System (Triage Loop): Executing verification steps before triaging...")
                    test_steps = WORKFLOW_STATE["testing_data"].get("test_steps", [])
                    env_vars = WORKFLOW_STATE["testing_data"].get("env_vars", {})
                    workspace_path = data.get("workspace_path", ".")
                    cwd = os.path.abspath(workspace_path)
                    
                    import subprocess, time
                    run_env = os.environ.copy()
                    for k, v in env_vars.items():
                        run_env[str(k)] = str(v)
                        
                    aggregated_logs = []
                    
                    if not test_steps:
                        # Guess default test command based on workspace file structures
                        default_cmd = "pytest"
                        for snippet in WORKFLOW_STATE["develop_data"].get("code_snippets", []):
                            filename = snippet.get("filename", "")
                            if filename.endswith(".js") or filename.endswith(".ts"):
                                default_cmd = "npm test"
                                break
                            elif filename.endswith(".rs"):
                                default_cmd = "cargo test"
                                break
                        test_steps = [{"id": 1, "cmd": default_cmd, "desc": "Default verification"}]
                        WORKFLOW_STATE["testing_data"]["test_steps"] = test_steps
                    
                    for step in test_steps:
                        cmd = step.get("cmd")
                        if cmd:
                            print(f"System (Triage Loop): Executing command '{cmd}' in {cwd}...")
                            start_time = time.time()
                            try:
                                result = subprocess.run(
                                    cmd,
                                    shell=True,
                                    capture_output=True,
                                    text=True,
                                    cwd=cwd,
                                    env=run_env,
                                    timeout=30
                                )
                                duration = time.time() - start_time
                                status = "pass" if result.returncode == 0 else "fail"
                                step_logs = (result.stdout or "") + "\n" + (result.stderr or "")
                                returncode = result.returncode
                            except subprocess.TimeoutExpired as te:
                                duration = 30.0
                                status = "fail"
                                step_logs = f"Timeout Expired: Command timed out after 30 seconds.\n{te.stdout or ''}\n{te.stderr or ''}"
                                returncode = -1
                            except Exception as e:
                                duration = 0.0
                                status = "fail"
                                step_logs = f"Execution Error: {str(e)}"
                                returncode = -2
                                
                            test_run_entry = {
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "cmd": cmd,
                                "status": status,
                                "logs": step_logs,
                                "duration_sec": round(duration, 2),
                                "returncode": returncode
                            }
                            
                            if "test_runs" not in WORKFLOW_STATE["testing_data"]:
                                WORKFLOW_STATE["testing_data"]["test_runs"] = []
                            WORKFLOW_STATE["testing_data"]["test_runs"].insert(0, test_run_entry)
                            
                            aggregated_logs.append(f"STEP: {step.get('desc')} ({cmd})\nSTATUS: {status.upper()}\nLOGS:\n{step_logs}\n=====================")
                    
                    data["test_logs"] = "\n".join(aggregated_logs)
                    data["env_vars"] = env_vars
                    data["test_steps"] = test_steps
                
                # Execute agent call
                response_text = asyncio.run(call_agent_async(command, data))
                
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
                    
                    # Extract text values from JSON so the UI console displays cleanly
                    def extract_text(obj):
                        texts = []
                        if isinstance(obj, dict):
                            for k, v in obj.items():
                                if k != "file_tree":  # file_tree is structured differently and verbose
                                    texts.extend(extract_text(v))
                        elif isinstance(obj, list):
                            for item in obj:
                                texts.extend(extract_text(item))
                        elif isinstance(obj, str):
                            texts.append(obj)
                        return texts
                    
                    agent_text = "\n".join(extract_text(parsed_response))
                    response_text_clean = agent_text
                    
                    # Debug logging of agent response cleanly
                    if os.environ.get("AGENT_DEBUG", "true").lower() == "true" or os.environ.get("DEBUG", "false").lower() == "true":
                        print("> Agent:")
                        print(agent_text)
                        sys.stdout.flush()
                        
                    if command == "task-explore":
                        WORKFLOW_STATE["current_stage"] = "create"
                        
                    elif command == "task-create":
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
                            proto_info = parsed_response.get("develop", {})
                            WORKFLOW_STATE["develop_data"] = {
                                "workflow_steps": proto_info.get("workflow_steps", []),
                                "file_tree": proto_info.get("file_tree", []),
                                "code_snippets": proto_info.get("code_snippets", []),
                                "open_questions": proto_info.get("open_questions", [])
                            }
                            WORKFLOW_STATE["current_stage"] = "develop"
                            
                    elif command == "task-develop":
                        is_update = data.get("is_update", False)
                        if is_update:
                            proto_info = parsed_response.get("develop", {})
                            WORKFLOW_STATE["develop_data"] = {
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
                            WORKFLOW_STATE["current_stage"] = "testing"
                            
                            # Guess default test command based on created files
                            default_cmd = "pytest"
                            for f in completed_info.get("created_files", []):
                                if f.endswith(".js") or f.endswith(".ts"):
                                    default_cmd = "npm test"
                                    break
                                elif f.endswith(".rs"):
                                    default_cmd = "cargo test"
                                    break
                            
                            if not WORKFLOW_STATE["testing_data"]["test_steps"]:
                                WORKFLOW_STATE["testing_data"]["test_steps"] = [
                                    {"id": 1, "cmd": default_cmd, "desc": "Execute test suite"}
                                ]
                            
                            # Write approved files into workspace
                            try:
                                code_snippets = WORKFLOW_STATE["develop_data"].get("code_snippets", [])
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
                            
                    elif command == "task-regression":
                        testing_info = parsed_response.get("testing", {})
                        if "remediation_instructions" not in WORKFLOW_STATE["testing_data"]:
                            WORKFLOW_STATE["testing_data"]["remediation_instructions"] = ""
                        WORKFLOW_STATE["testing_data"]["remediation_instructions"] = data.get("feedback_input", "")
                        
                        # Apply patches/updates to the workspace returned by the agent
                        applied_snippets = []
                        try:
                            code_snippets = parsed_response.get("code_snippets", [])
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
                                        print(f"System (Regression Fix): Automatically wrote {filename} to {base_workspace}")
                                        applied_snippets.append(snippet)
                                        
                            # Proactively update develop snippet memory with correct code as well
                            if applied_snippets:
                                if "code_snippets" not in WORKFLOW_STATE["develop_data"]:
                                    WORKFLOW_STATE["develop_data"]["code_snippets"] = []
                                for app_sn in applied_snippets:
                                    existing = next((s for s in WORKFLOW_STATE["develop_data"]["code_snippets"] if s["filename"] == app_sn["filename"]), None)
                                    if existing:
                                        existing["code"] = app_sn["code"]
                                    else:
                                        WORKFLOW_STATE["develop_data"]["code_snippets"].append(app_sn)
                        except Exception as exec_err:
                            print(f"Error executing regression workspace changes: {exec_err}")
                            
                        # Run verification steps again after applying the agent's fixes
                        print("System (Post-Fix Verification): Re-running verification steps after applying fixes...")
                        test_steps = WORKFLOW_STATE["testing_data"].get("test_steps", [])
                        env_vars = WORKFLOW_STATE["testing_data"].get("env_vars", {})
                        workspace_path = data.get("workspace_path", ".")
                        cwd = os.path.abspath(workspace_path)
                        
                        import subprocess, time
                        run_env = os.environ.copy()
                        for k, v in env_vars.items():
                            run_env[str(k)] = str(v)
                            
                        for step in test_steps:
                            cmd = step.get("cmd")
                            if cmd:
                                print(f"System (Post-Fix Verification): Executing command '{cmd}' in {cwd}...")
                                start_time = time.time()
                                try:
                                    result = subprocess.run(
                                        cmd,
                                        shell=True,
                                        capture_output=True,
                                        text=True,
                                        cwd=cwd,
                                        env=run_env,
                                        timeout=30
                                    )
                                    duration = time.time() - start_time
                                    status = "pass" if result.returncode == 0 else "fail"
                                    step_logs = (result.stdout or "") + "\n" + (result.stderr or "")
                                    returncode = result.returncode
                                except subprocess.TimeoutExpired as te:
                                    duration = 30.0
                                    status = "fail"
                                    step_logs = f"Timeout Expired: Command timed out after 30 seconds.\n{te.stdout or ''}\n{te.stderr or ''}"
                                    returncode = -1
                                except Exception as e:
                                    duration = 0.0
                                    status = "fail"
                                    step_logs = f"Execution Error: {str(e)}"
                                    returncode = -2
                                    
                                test_run_entry = {
                                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "cmd": cmd,
                                    "status": status,
                                    "logs": step_logs,
                                    "duration_sec": round(duration, 2),
                                    "returncode": returncode
                                }
                                
                                if "test_runs" not in WORKFLOW_STATE["testing_data"]:
                                    WORKFLOW_STATE["testing_data"]["test_runs"] = []
                                WORKFLOW_STATE["testing_data"]["test_runs"].insert(0, test_run_entry)

                            
                except Exception as parse_err:
                    print(f"Error parsing agent JSON response: {parse_err}")
                    sys.stdout.flush()
                    response_text_clean += f"\n\n[System Error: Failed to parse Agent response as JSON. Error: {str(parse_err)}]"
                
                # Append to chat history
                user_msg = data.get("context") or data.get("scoping_input") or data.get("feedback_input") or f"Command: {command}"
                if user_msg and hasattr(self, 'current_session_data'):
                    import time
                    self.current_session_data.setdefault("chat_history", []).append({
                        "role": "user",
                        "content": user_msg,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    self.current_session_data.setdefault("chat_history", []).append({
                        "role": "assistant",
                        "content": response_text_clean,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    # Check for compression (> 15 messages)
                    if len(self.current_session_data.get("chat_history", [])) > 15:
                        print("System: Compressing session history to optimize token space...")
                        try:
                            history_to_compress = self.current_session_data["chat_history"][:-4]
                            retained_history = self.current_session_data["chat_history"][-4:]
                            
                            compression_data = {
                                "model": data.get("model", ""),
                                "chat_history": history_to_compress,
                                "language": data.get("language", "en")
                            }
                            summary = asyncio.run(call_agent_async("compress-history", compression_data))
                            
                            existing_summary = self.current_session_data.get("summary", "")
                            if existing_summary:
                                new_summary = f"{existing_summary}\n\nPreviously: {summary}"
                            else:
                                new_summary = summary
                                
                            self.current_session_data["summary"] = new_summary
                            self.current_session_data["chat_history"] = retained_history
                            print("System: History successfully compressed.")
                        except Exception as compression_err:
                            print(f"Error during automatic history compression: {compression_err}")
                
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
                
        elif self.path == '/api/agent/event':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
                if "event" in payload and isinstance(payload["event"], dict):
                    event_data = payload["event"]
                else:
                    event_data = payload
                
                from event_router import LLMAgentEventRouter
                router = LLMAgentEventRouter()
                result = router.route_event(event_data)
                
                # Check outcome and update WORKFLOW_STATE / debug_logs
                import datetime
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                if "debug_logs" not in WORKFLOW_STATE:
                    WORKFLOW_STATE["debug_logs"] = ""
                
                status = result.get("status")
                if status == "requires_confirmation":
                    WORKFLOW_STATE["pending_permission"] = {
                        "permission": result.get("permission"),
                        "target": result.get("target"),
                        "message": result.get("message")
                    }
                    log_msg = f"[PERMISSION REQUIRED] {result.get('message')}"
                    WORKFLOW_STATE["debug_logs"] = f"[{timestamp}] {log_msg}\n\n" + WORKFLOW_STATE["debug_logs"]
                elif status == "approved":
                    log_msg = f"[PERMISSION APPROVED] {result.get('permission')} approved on: {result.get('target')}"
                    WORKFLOW_STATE["debug_logs"] = f"[{timestamp}] {log_msg}\n\n" + WORKFLOW_STATE["debug_logs"]
                elif status == "processed":
                    log_msg = f"[EVENT] {result.get('message')}"
                    WORKFLOW_STATE["debug_logs"] = f"[{timestamp}] {log_msg}\n\n" + WORKFLOW_STATE["debug_logs"]
                    
                    if result.get("type") == "tool":
                        if "tool_tracking" not in WORKFLOW_STATE:
                            WORKFLOW_STATE["tool_tracking"] = {}
                        WORKFLOW_STATE["tool_tracking"]["status"] = result.get("tool_status")
                        WORKFLOW_STATE["tool_tracking"]["message"] = result.get("message")
                elif status == "stream":
                    log_msg = f"[STREAM DELTA ({result.get('field')})] {result.get('delta')}"
                    WORKFLOW_STATE["debug_logs"] = f"[{timestamp}] {log_msg}\n\n" + WORKFLOW_STATE["debug_logs"]
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'routing_result': result}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
                
        elif self.path == '/api/agent/permission/respond':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
                approved = payload.get('approved', False)
                
                import datetime
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                if "debug_logs" not in WORKFLOW_STATE:
                    WORKFLOW_STATE["debug_logs"] = ""
                
                pending = WORKFLOW_STATE.get("pending_permission")
                if pending:
                    perm = pending.get("permission")
                    target = pending.get("target")
                    if approved:
                        log_msg = f"[USER ALLOWED] Granted permission to execute: {perm} on {target}"
                        WORKFLOW_STATE["debug_logs"] = f"[{timestamp}] {log_msg}\n\n" + WORKFLOW_STATE["debug_logs"]
                    else:
                        log_msg = f"[USER DENIED] Blocked permission to execute: {perm} on {target}"
                        WORKFLOW_STATE["debug_logs"] = f"[{timestamp}] {log_msg}\n\n" + WORKFLOW_STATE["debug_logs"]
                    
                    WORKFLOW_STATE.pop("pending_permission", None)
                else:
                    log_msg = "[SYSTEM WARNING] Received user permission response, but no pending request was active."
                    WORKFLOW_STATE["debug_logs"] = f"[{timestamp}] {log_msg}\n\n" + WORKFLOW_STATE["debug_logs"]
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'approved': approved}).encode('utf-8'))
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
                
        elif self.path == '/api/run-tests':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
                cmd = payload.get('cmd', '')
                env_vars = payload.get('env_vars', {})
                
                # Update environment variables and steps in local state
                WORKFLOW_STATE["testing_data"]["env_vars"] = env_vars
                if "test_steps" in payload:
                    WORKFLOW_STATE["testing_data"]["test_steps"] = payload.get("test_steps", [])
                
                if not cmd:
                    raise ValueError("Test command is required.")
                
                # Execute in the active workspace
                workspace_path = payload.get('workspace_path', '.')
                cwd = os.path.abspath(workspace_path)
                
                # Set up environment variables
                import os as env_os
                run_env = env_os.environ.copy()
                for k, v in env_vars.items():
                    run_env[str(k)] = str(v)
                
                import subprocess, time
                print(f"System: Running test step '{cmd}' in {cwd}...")
                
                start_time = time.time()
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=cwd,
                    env=run_env,
                    timeout=30 # Prevent hangs
                )
                duration = time.time() - start_time
                
                status = "pass" if result.returncode == 0 else "fail"
                logs = (result.stdout or "") + "\n" + (result.stderr or "")
                
                test_run_entry = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "cmd": cmd,
                    "status": status,
                    "logs": logs,
                    "duration_sec": round(duration, 2),
                    "returncode": result.returncode
                }
                
                if "test_runs" not in WORKFLOW_STATE["testing_data"]:
                    WORKFLOW_STATE["testing_data"]["test_runs"] = []
                WORKFLOW_STATE["testing_data"]["test_runs"].insert(0, test_run_entry)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'success',
                    'test_run': test_run_entry,
                    'state': WORKFLOW_STATE
                }).encode('utf-8'))
                
            except subprocess.TimeoutExpired as te:
                import time
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                test_run_entry = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "cmd": cmd,
                    "status": "fail",
                    "logs": f"Timeout Expired: Command timed out after 30 seconds.\n{te.stdout or ''}\n{te.stderr or ''}",
                    "duration_sec": 30.0,
                    "returncode": -1
                }
                if "test_runs" not in WORKFLOW_STATE["testing_data"]:
                    WORKFLOW_STATE["testing_data"]["test_runs"] = []
                WORKFLOW_STATE["testing_data"]["test_runs"].insert(0, test_run_entry)
                self.wfile.write(json.dumps({
                    'status': 'success',
                    'test_run': test_run_entry,
                    'state': WORKFLOW_STATE
                }).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
            return
            
        elif self.path == '/api/testing/baseline':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                baseline = payload.get('baseline', [])
                WORKFLOW_STATE["testing_data"]["regression_baseline"] = baseline
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'state': WORKFLOW_STATE}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
            return
            
        elif self.path == '/api/testing/update':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                if "env_vars" in payload:
                    WORKFLOW_STATE["testing_data"]["env_vars"] = payload["env_vars"]
                if "test_steps" in payload:
                    WORKFLOW_STATE["testing_data"]["test_steps"] = payload["test_steps"]
                if "remediation_instructions" in payload:
                    WORKFLOW_STATE["testing_data"]["remediation_instructions"] = payload["remediation_instructions"]
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'state': WORKFLOW_STATE}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
            return
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
