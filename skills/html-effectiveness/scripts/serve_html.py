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
from http.server import HTTPServer, SimpleHTTPRequestHandler

# OpenCode server runs on a fixed address with no authentication required.
_OC_BASE = "http://127.0.0.1:4096"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_TEMPLATES_DIR = os.path.join(_SCRIPT_DIR, "..", "templates")
_STATIC_DIR = os.path.join(_SCRIPT_DIR, "..", "static")
_STATE_FILE = os.path.join(_SCRIPT_DIR, "..", "workflow_state.json")

_DEFAULT_STATE = {
    "current_stage": "create",
    "create_data": {"title": "", "category": "Feature", "goal": "", "context": ""},
    "spec_data": {"sections": [], "open_questions": []},
    "develop_data": {"workflow_steps": [], "file_tree": [], "code_snippets": [], "open_questions": []},
    "testing_data": {"test_steps": [], "env_vars": {}, "test_runs": [], "remediation_instructions": "", "regression_baseline": []},
    "completed_data": {"summary_items": [], "created_files": [], "verification_results": []},
    "references": [],
}

# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def _load_state():
    if os.path.exists(_STATE_FILE):
        try:
            with open(_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return dict(_DEFAULT_STATE)


def _save_state(state):
    try:
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f"[serve_html] State save error: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
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
        # Suppress polling noise
        if args and isinstance(args[0], str) and "api/opencode" in args[0]:
            return
        sys.stdout.write("%s - - [%s] %s\n" % (
            self.address_string(), self.log_date_time_string(), fmt % args))

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
    # CORS pre-flight
    # ------------------------------------------------------------------

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    # ------------------------------------------------------------------
    # OpenCode proxy
    # ------------------------------------------------------------------

    def _proxy(self, method, parsed, body=b""):
        # Strip /api/opencode prefix to get the native OpenCode path
        native_path = parsed.path[len("/api/opencode"):]
        if not native_path:
            native_path = "/"

        oc_url = f"{_OC_BASE}{native_path}"
        if parsed.query:
            oc_url += f"?{parsed.query}"

        req = urllib.request.Request(oc_url, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")

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
            self.send_response(exc.code)
            self._cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as exc:
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
