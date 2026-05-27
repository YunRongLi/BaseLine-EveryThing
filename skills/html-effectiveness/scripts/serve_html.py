import os, sys, asyncio
from http.server import HTTPServer
from handler import AgentHTTPRequestHandler
from config import load_env, check_api_key

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

class DebugLogStream:

    def __init__(self, original_stream, is_stderr=False):
        self.original_stream = original_stream
        self.is_stderr = is_stderr

    def write(self, text):
        self.original_stream.write(text)
        self.original_stream.flush()
        
        cleaned = text.strip()
        if cleaned:
            # Dynamically import state to avoid circular dependencies
            from state import WORKFLOW_STATE
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            prefix = "[ERROR] " if self.is_stderr else ""
            if "debug_logs" not in WORKFLOW_STATE:
                WORKFLOW_STATE["debug_logs"] = ""
            WORKFLOW_STATE["debug_logs"] = f"[{timestamp}] {prefix}{cleaned}\n\n" + WORKFLOW_STATE["debug_logs"]

    def flush(self):
        self.original_stream.flush()

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
    
    # Redirect stdout and stderr to capture all logs for the web debug-console
    sys.stdout = DebugLogStream(sys.stdout, is_stderr=False)
    sys.stderr = DebugLogStream(sys.stderr, is_stderr=True)
    
    if not check_api_key():
        print("WARNING: No model backend is configured initially. Set GEMINI_API_KEY, ANTHROPIC_ADMIN_API_KEY, or VLLM_API_URL via the web interface or environment variables.")
    
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
        if os.path.isdir(target_dir):
            os.chdir(target_dir)
            
    port = find_free_port()
    server = ReusableHTTPServer(('127.0.0.1', port), AgentHTTPRequestHandler)

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
