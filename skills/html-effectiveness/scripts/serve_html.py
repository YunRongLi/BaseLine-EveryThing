"""
Lightweight static server and OpenCode API proxy for the html-effectiveness skill.

Responsibilities:
  1. Proxy /api/opencode/* requests to the local OpenCode server at 127.0.0.1:4096.
  2. Persist workflow UI state to a local workflow_state.json file (/api/state GET/POST).
  3. Serve all static HTML/JS template files from the templates directory.
"""

import os
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

# OpenCode server runs on a fixed address with no authentication required.
_OC_BASE = "http://127.0.0.1:4096"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_TEMPLATES_DIR = os.path.join(_SCRIPT_DIR, "..", "templates")
_STATIC_DIR = os.path.join(_SCRIPT_DIR, "..", "static")
_STATE_FILE = os.path.join(os.getcwd(), ".workflow", "workflow_state.json")

_DEFAULT_STATE = {
    "current_stage": "create",
    "create_data": {"title": "", "category": "Feature", "goal": "", "context": ""},
    "spec_data": {"sections": [], "open_questions": {}},
    "develop_data": {"workflow_steps": [], "file_tree": [], "code_snippets": [], "open_questions": {}},
    "testing_data": {"test_steps": [], "env_vars": {}, "test_runs": [], "remediation_instructions": "", "regression_baseline": []},
    "completed_data": {"summary_items": [], "created_files": [], "verification_results": []},
    "references": [],
}

# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

_state_lock = threading.Lock()
_in_memory_state = dict(_DEFAULT_STATE)

def _load_state():
    with _state_lock:
        return dict(_in_memory_state)


def _save_state(state):
    global _in_memory_state
    with _state_lock:
        _in_memory_state = dict(state)


_direct_sessions = {}
_direct_sessions_lock = threading.Lock()

def _call_gemini_direct_python(api_key, model, contents):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    req = urllib.request.Request(url, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-goog-api-key", api_key)
    # Force Gemini to return strictly valid JSON
    req.data = json.dumps({
        "contents": contents,
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }).encode("utf-8")
    
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))

def _handle_direct_message_post(session_id, body_dict, api_key):
    user_parts = body_dict.get("parts", [])
    user_text = "".join(p.get("text", "") for p in user_parts if p.get("type") == "text")
    
    with _direct_sessions_lock:
        if session_id not in _direct_sessions:
            _direct_sessions[session_id] = []
        
        user_msg = {
            "info": {
                "role": "user",
                "time": {"created": "2026-05-28T12:00:00Z"}
            },
            "parts": [{"type": "text", "text": user_text}]
        }
        _direct_sessions[session_id].append(user_msg)
        
        asst_msg = {
            "info": {
                "role": "assistant",
                "time": {"created": "2026-05-28T12:00:00Z", "completed": None}
            },
            "parts": [{"type": "text", "text": ""}]
        }
        _direct_sessions[session_id].append(asst_msg)
        
        contents = []
        for msg in _direct_sessions[session_id][:-1]:
            role = "model" if msg["info"]["role"] == "assistant" else "user"
            parts = [{"text": p["text"]} for p in msg["parts"] if p["type"] == "text"]
            if parts:
                contents.append({"role": role, "parts": parts})
                
    def worker():
        try:
            model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            print(f"[serve_html] [Gemini Mode] Calling direct Gemini endpoint ({model})...")
            sys.stdout.flush()
            resp_data = _call_gemini_direct_python(api_key, model, contents)
            candidates = resp_data.get("candidates", [])
            if candidates and candidates[0].get("content"):
                resp_parts = candidates[0]["content"].get("parts", [])
                text_response = "".join(p.get("text", "") for p in resp_parts if "text" in p)
                print(f"[serve_html] [Gemini Mode] Successfully received response from Gemini API ({len(text_response)} chars)")
                sys.stdout.flush()
            else:
                text_response = f"ERROR: Invalid response from Gemini API: {resp_data}"
                print(f"[serve_html] [Gemini Mode] Invalid response from Gemini API: {resp_data}", file=sys.stderr)
                sys.stderr.flush()
        except urllib.error.HTTPError as exc:
            try:
                err_content = exc.read().decode("utf-8")
                try:
                    err_json = json.loads(err_content)
                    if "error" in err_json and "message" in err_json["error"]:
                        err_msg = err_json["error"]["message"]
                        text_response = f"ERROR: Gemini API call failed: {err_msg} (HTTP {exc.code})"
                    else:
                        text_response = f"ERROR: Gemini API call failed: {err_content} (HTTP {exc.code})"
                except Exception:
                    text_response = f"ERROR: Gemini API call failed: {err_content} (HTTP {exc.code})"
            except Exception:
                text_response = f"ERROR: Gemini API call failed: {exc}"
            print(f"[serve_html] [Gemini Mode] HTTPError occurred: {text_response}", file=sys.stderr)
            sys.stderr.flush()
        except Exception as exc:
            text_response = f"ERROR: Gemini API call failed: {exc}"
            print(f"[serve_html] [Gemini Mode] Exception occurred: {exc}", file=sys.stderr)
            sys.stderr.flush()
            
        with _direct_sessions_lock:
            if session_id in _direct_sessions:
                for msg in reversed(_direct_sessions[session_id]):
                    if msg["info"]["role"] == "assistant" and msg["info"]["time"]["completed"] is None:
                        msg["parts"] = [{"type": "text", "text": text_response}]
                        msg["info"]["time"]["completed"] = "2026-05-28T12:00:00Z"
                        msg["info"]["finish"] = True
                        break
                        
    threading.Thread(target=worker, daemon=True).start()

# HTTP handler
# ---------------------------------------------------------------------------

class SkillHTTPHandler(SimpleHTTPRequestHandler):

    _ROUTES = {
        "":                  "task_explore.html",
        "index.html":        "task_explore.html",
        "explore":           "task_explore.html",
        "task-explore":      "task_explore.html",
        "task_explore":      "task_explore.html",
        "task_explore.html": "task_explore.html",
        "create":            "task_create.html",
        "task-create":       "task_create.html",
        "task_create":       "task_create.html",
        "task_create.html":  "task_create.html",
        "spec":              "task_spec.html",
        "task-spec":         "task_spec.html",
        "task_spec":         "task_spec.html",
        "task_spec.html":    "task_spec.html",
        "develop":           "task_develop.html",
        "task-develop":      "task_develop.html",
        "task_develop":      "task_develop.html",
        "task_develop.html": "task_develop.html",
        "testing":           "task_testing.html",
        "task-testing":      "task_testing.html",
        "task_testing":      "task_testing.html",
        "task_testing.html": "task_testing.html",
        "workflow":          "task_workflow.html",
        "task_workflow":     "task_workflow.html",
        "task_workflow.html":"task_workflow.html",
        "sessions.js":           "sessions.js",
        "opencode_client.js":    "opencode_client.js",
        "keyboard_shortcuts.js": "keyboard_shortcuts.js",
        "terminal_input.js":     "terminal_input.js",
    }

    def translate_path(self, path):
        parsed = urllib.parse.urlparse(path)
        clean = parsed.path.lstrip("/")
        filename = self._ROUTES.get(clean)
        if filename:
            if filename.endswith(".js"):
                return os.path.abspath(os.path.join(_STATIC_DIR, "js", filename))
            return os.path.abspath(os.path.join(_TEMPLATES_DIR, filename))
        return super().translate_path(path)

    def log_message(self, fmt, *args):
        # Suppress GET polling noise for sessions and messages to keep logs clean,
        # but allow POST, PUT, DELETE, and other active requests to be logged.
        if args and len(args) > 0 and isinstance(args[0], str):
            request_line = args[0]
            if "GET /api/opencode/session" in request_line:
                return
        sys.stdout.write("%s - - [%s] %s\n" % (
            self.address_string(), self.log_date_time_string(), fmt % args))
        sys.stdout.flush()

    def end_headers(self):
        # Prevent browser caching of client JS files to ensure the latest changes are loaded
        if self.path.endswith(".js") or "opencode_client.js" in self.path:
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        clean = parsed.path.lstrip("/")

        if clean == "api/state":
            self._send_json({"status": "success", "state": _load_state()})
        elif clean.startswith("api/opencode/"):
            self._proxy("GET", parsed)
        else:
            super().do_GET()

    # ------------------------------------------------------------------
    # POST
    # ------------------------------------------------------------------

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        clean = parsed.path.lstrip("/")
        body = self._read_body()

        if clean == "api/state":
            self._handle_post_state(body)
        elif clean.startswith("api/opencode/"):
            self._proxy("POST", parsed, body)
        else:
            self._send_json({"status": "error", "message": f"Unknown route: {clean}"}, code=404)

    def _handle_post_state(self, body):
        try:
            payload = json.loads(body)
            state = _load_state()
            state.update(payload.get("state", {}))
            _save_state(state)
            self._send_json({"status": "success"})
        except Exception as exc:
            self._send_json({"status": "error", "message": str(exc)}, code=400)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        clean = parsed.path.lstrip("/")
        body = self._read_body()

        if clean.startswith("api/opencode/"):
            self._proxy("DELETE", parsed, body)
        else:
            self._send_json({"status": "error", "message": f"Unknown route: {clean}"}, code=404)

    # ------------------------------------------------------------------
    # PUT
    # ------------------------------------------------------------------

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        clean = parsed.path.lstrip("/")
        body = self._read_body()

        if clean.startswith("api/opencode/"):
            self._proxy("PUT", parsed, body)
        else:
            self._send_json({"status": "error", "message": f"Unknown route: {clean}"}, code=404)

    # ------------------------------------------------------------------
    # PATCH
    # ------------------------------------------------------------------

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        clean = parsed.path.lstrip("/")
        body = self._read_body()

        if clean.startswith("api/opencode/"):
            self._proxy("PATCH", parsed, body)
        else:
            self._send_json({"status": "error", "message": f"Unknown route: {clean}"}, code=404)

    # ------------------------------------------------------------------
    # CORS pre-flight
    # ------------------------------------------------------------------

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    # ------------------------------------------------------------------
    # OpenCode proxy
    # ------------------------------------------------------------------

    def _handle_direct_mock(self, method, parsed, body):
        import uuid
        native_path = parsed.path[len("/api/opencode"):]
        if not native_path:
            native_path = "/"
            
        api_key = self.headers.get("X-goog-api-key") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            self._send_json({
                "status": "error",
                "message": "Gemini API Key is missing. Please configure GEMINI_API_KEY in the server environment or headers."
            }, code=400)
            return

        if native_path == "/session":
            if method == "POST":
                try:
                    payload = json.loads(body) if body else {}
                except Exception:
                    payload = {}
                title = payload.get("title", "Task Workflow")
                s_id = str(uuid.uuid4())
                with _direct_sessions_lock:
                    _direct_sessions[s_id] = []
                self._send_json({"id": s_id, "title": title})
            elif method == "GET":
                with _direct_sessions_lock:
                    s_list = [{"id": k, "title": "Task Workflow"} for k in _direct_sessions.keys()]
                self._send_json(s_list)
            else:
                self._send_json({"status": "error", "message": f"Method {method} not allowed"}, code=405)
                
        elif native_path.startswith("/session/") and len(native_path.split("/")) == 3:
            s_id = native_path.split("/")[-1]
            if method == "DELETE":
                with _direct_sessions_lock:
                    if s_id in _direct_sessions:
                        del _direct_sessions[s_id]
                self._send_json({"status": "success"})
            else:
                self._send_json({"status": "error", "message": f"Method {method} not allowed"}, code=405)
                
        elif native_path.startswith("/session/") and native_path.endswith("/message"):
            parts = native_path.split("/")
            if len(parts) == 4 and parts[3] == "message":
                s_id = parts[2]
                if method == "GET":
                    with _direct_sessions_lock:
                        msgs = list(_direct_sessions.get(s_id, []))
                    self._send_json(msgs)
                elif method == "POST":
                    try:
                        payload = json.loads(body) if body else {}
                    except Exception as e:
                        self._send_json({"status": "error", "message": f"Invalid JSON: {e}"}, code=400)
                        return
                    _handle_direct_message_post(s_id, payload, api_key)
                    self._send_json({"status": "success", "info": {"role": "user"}})
                else:
                    self._send_json({"status": "error", "message": f"Method {method} not allowed"}, code=405)
            else:
                self._send_json({"status": "error", "message": f"Endpoint not found: {native_path}"}, code=404)
        else:
            self._send_json({"status": "error", "message": f"Endpoint not found: {native_path}"}, code=404)

    def _proxy(self, method, parsed, body=b""):
        opencode_url = self.headers.get("X-opencode-url")
        api_key = self.headers.get("X-goog-api-key") or os.environ.get("GEMINI_API_KEY")
        selected_provider = self.headers.get("X-selected-provider-model")

        use_gemini_mock = False
        if selected_provider:
            if selected_provider.startswith("gemini-"):
                use_gemini_mock = True
        elif api_key:
            use_gemini_mock = True

        mode_str = "Gemini Direct Mock" if (use_gemini_mock and api_key) else "OpenCode Server"
        print(f"[serve_html] Proxy routing: {method} {parsed.path} -> mode={mode_str}")
        sys.stdout.flush()

        if use_gemini_mock and api_key:
            if selected_provider and selected_provider.startswith("gemini-"):
                os.environ["GEMINI_MODEL"] = selected_provider
            self._handle_direct_mock(method, parsed, body)
            return

        # Strip /api/opencode prefix to get the native OpenCode path
        native_path = parsed.path[len("/api/opencode"):]
        if not native_path:
            native_path = "/"

        oc_base_url = opencode_url or _OC_BASE
        oc_url = f"{oc_base_url.rstrip('/')}{native_path}"
        if parsed.query:
            oc_url += f"?{parsed.query}"

        print(f"[serve_html] Proxying to OpenCode endpoint: {oc_url}")
        sys.stdout.flush()

        req = urllib.request.Request(oc_url, method=method)
        # Forward headers from incoming request, excluding accept-encoding to prevent compression issues:
        for header, value in self.headers.items():
            if header.lower() not in ("host", "content-length", "content-type", "accept", "accept-encoding"):
                req.add_header(header, value)
                
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        req.add_header("Accept-Encoding", "identity")

        if method in ("POST", "PUT", "PATCH") and body:
            req.data = body if isinstance(body, bytes) else body.encode("utf-8")

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                self._cors_headers()
                self.send_header("Content-Type",
                                 resp.headers.get("Content-Type", "application/json"))
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as exc:
            err_body = exc.read()
            print(f"[serve_html] OpenCode backend returned HTTPError {exc.code}: {err_body.decode('utf-8', errors='ignore')}", file=sys.stderr)
            sys.stderr.flush()
            self.send_response(exc.code)
            self._cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(err_body)
        except urllib.error.URLError as exc:
            print(f"[serve_html] OpenCode backend URLError: {exc.reason}", file=sys.stderr)
            sys.stderr.flush()
            self._send_json({
                "status": "error",
                "message": f"Cannot connect to OpenCode backend server: {exc.reason}. Verify that OpenCode is running on port 4096."
            }, code=503)
        except Exception as exc:
            print(f"[serve_html] OpenCode backend proxy exception: {exc}", file=sys.stderr)
            sys.stderr.flush()
            self._send_json({"status": "error", "message": f"Proxy error: {exc}"}, code=502)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length > 0 else b""

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Session-Id")

    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

class _ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True


def _find_free_port(start=8000):
    import socket
    port = start
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1
    raise RuntimeError("No free port available")


def _eof_watcher(server):
    """Shut down cleanly when the parent agent process closes stdin."""
    try:
        while True:
            if not sys.stdin.readline():
                break
    except (IOError, ValueError, KeyboardInterrupt):
        pass
    finally:
        server.shutdown()


def main():
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
        if os.path.isdir(target_dir):
            os.chdir(target_dir)

    port = _find_free_port()
    server = _ReusableHTTPServer(("127.0.0.1", port), SkillHTTPHandler)

    print(f"Server started at http://localhost:{port}")
    print(f"OpenCode proxy target: {_OC_BASE}")
    sys.stdout.flush()

    import threading
    threading.Thread(target=_eof_watcher, args=(server,), daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
