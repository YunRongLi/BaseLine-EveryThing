import os, sys, asyncio
from http.server import HTTPServer
from handler import AgentHTTPRequestHandler
from config import load_env, check_api_key

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
