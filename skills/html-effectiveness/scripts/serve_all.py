#!/usr/bin/env python3
import os
import sys
import subprocess
import threading
import signal
import time

def log_stream(stream, prefix):
    """Read lines from stream and log them with a prefix."""
    try:
        for line in iter(stream.readline, b""):
            line_str = line.decode("utf-8", errors="replace").rstrip()
            print(f"[{prefix}] {line_str}")
            sys.stdout.flush()
    except Exception as e:
        print(f"[manager] Error logging stream for {prefix}: {e}", file=sys.stderr)
        sys.stderr.flush()

def forward_stdin(target_stdin):
    """Forward stdin from parent to child process to support EOF clean shutdown."""
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            target_stdin.write(line.encode("utf-8"))
            target_stdin.flush()
    except Exception:
        pass
    finally:
        try:
            target_stdin.close()
        except Exception:
            pass

def main():
    # Find absolute path of serve_html.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    serve_html_path = os.path.join(script_dir, "serve_html.py")

    # Locate opencode executable
    opencode_path = os.path.expanduser("~/.local/bin/opencode")
    if not os.path.exists(opencode_path):
        import shutil
        opencode_path = shutil.which("opencode") or "opencode"

    print(f"[manager] Starting unified services...")
    print(f"[manager] OpenCode executable: {opencode_path}")
    print(f"[manager] HTML Backend script: {serve_html_path}")
    sys.stdout.flush()

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    # Start opencode serve
    print("[manager] Spawning opencode serve --port 4096 --hostname 127.0.0.1")
    sys.stdout.flush()
    try:
        opencode_proc = subprocess.Popen(
            [opencode_path, "serve", "--port", "4096", "--hostname", "127.0.0.1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env
        )
    except Exception as e:
        print(f"[manager] Failed to start opencode process: {e}", file=sys.stderr)
        sys.exit(1)

    # Start serve_html
    print("[manager] Spawning serve_html.py")
    sys.stdout.flush()
    try:
        serve_html_proc = subprocess.Popen(
            [sys.executable, "-u", serve_html_path] + sys.argv[1:],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env
        )
    except Exception as e:
        print(f"[manager] Failed to start serve_html process: {e}", file=sys.stderr)
        opencode_proc.terminate()
        sys.exit(1)

    # Threads for logging
    opencode_log_thread = threading.Thread(
        target=log_stream, args=(opencode_proc.stdout, "opencode"), daemon=True
    )
    html_log_thread = threading.Thread(
        target=log_stream, args=(serve_html_proc.stdout, "html-backend"), daemon=True
    )

    opencode_log_thread.start()
    html_log_thread.start()

    # Forward stdin only if running interactively (TTY) to support daemon/systemd execution.
    if sys.stdin and sys.stdin.isatty():
        stdin_thread = threading.Thread(
            target=forward_stdin, args=(serve_html_proc.stdin,), daemon=True
        )
        stdin_thread.start()
    else:
        # In non-interactive mode, do not spawn forwarder thread and do not close child stdin pipe.
        print("[manager] Running in non-interactive mode. Keeping child stdin pipe open.")
        sys.stdout.flush()

    shutdown_event = threading.Event()

    def handle_signal(signum, frame):
        print(f"[manager] Received signal {signum}, initiating clean shutdown...")
        sys.stdout.flush()
        shutdown_event.set()

    # Register signals for clean termination
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Monitor subprocesses
    try:
        while not shutdown_event.is_set():
            # Check if either process terminated
            opencode_code = opencode_proc.poll()
            html_code = serve_html_proc.poll()

            if opencode_code is not None:
                print(f"[manager] OpenCode process exited with code {opencode_code}")
                shutdown_event.set()
                break

            if html_code is not None:
                print(f"[manager] HTML Backend process exited with code {html_code}")
                shutdown_event.set()
                break

            time.sleep(0.5)
    except KeyboardInterrupt:
        pass

    # Cleanup processes
    print("[manager] Terminating subprocesses...")
    sys.stdout.flush()

    # Terminate opencode
    if opencode_proc.poll() is None:
        opencode_proc.terminate()
    # Terminate serve_html
    if serve_html_proc.poll() is None:
        serve_html_proc.terminate()

    # Wait for processes to exit
    try:
        opencode_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        print("[manager] OpenCode did not terminate, killing it...")
        opencode_proc.kill()

    try:
        serve_html_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        print("[manager] HTML Backend did not terminate, killing it...")
        serve_html_proc.kill()

    print("[manager] Cleanup complete. Exiting.")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
