import urllib.request
import json
import os
import time

def find_active_port(start_port=8000, max_port=8005):
    for port in range(start_port, max_port + 1):
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/state")
            with urllib.request.urlopen(req, timeout=1) as response:
                if response.status == 200:
                    return port
        except Exception:
            continue
    return None

def test_api():
    print("Starting integration test for modular JSON workflow...")
    
    port = find_active_port()
    if not port:
        print("Failed to find active local server on ports 8000-8005.")
        print("Please make sure serve_html.py is running.")
        return
        
    print(f"Connected to local server on port {port}.")
    base_url = f"http://127.0.0.1:{port}"

    # 1. Connect to local server
    url = f"{base_url}/api/models"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            print(f"Models API Success! Available models: {res_data.get('models')}")
    except Exception as e:
        print(f"Failed to connect to local server: {e}")
        return

    # 2. Check initial state
    print("\nChecking initial state...")
    try:
        req = urllib.request.Request(f"{base_url}/api/state")
        with urllib.request.urlopen(req) as response:
            state_res = json.loads(response.read().decode('utf-8'))
            state = state_res.get("state", {})
            print(f"Current stage: {state.get('current_stage')}")
            if state.get("current_stage") != "create":
                print("Warning: State is not in 'create' stage. Resetting state...")
                reset_req = urllib.request.Request(f"{base_url}/api/state/reset", data=b"{}")
                urllib.request.urlopen(reset_req)
    except Exception as e:
        print(f"Error checking/resetting state: {e}")
        return

    # 3. Simulate task-create
    print("\nSimulating 'task-create' command...")
    payload = {
        "command": "task-create",
        "data": {
            "title": "Implement CLI file-indexer",
            "category": "Feature",
            "goal": "Build a fast, Python-based CLI tool to recursively scan a folder and build a JSON catalog.",
            "context": "Follow PARA and ACE framework.",
            "model": "gemini-2.5-flash",
            "language": "en"
        }
    }
    
    agent_url = f"{base_url}/api/agent"
    headers = {"Content-Type": "application/json"}
    
    try:
        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(agent_url, data=data_bytes, headers=headers)
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            print("API response received!")
    except Exception as e:
        print(f"Error calling /api/agent (task-create): {e}")
        return

    # 4. Verify state after task-create
    print("\nVerifying state transition to 'spec'...")
    try:
        req = urllib.request.Request(f"{base_url}/api/state")
        with urllib.request.urlopen(req) as response:
            state_res = json.loads(response.read().decode('utf-8'))
            state = state_res.get("state", {})
            print(f"Current stage: {state.get('current_stage')}")
            if state.get("current_stage") == "spec" and len(state.get("spec_data", {}).get("sections", [])) > 0:
                print("SUCCESS: Correctly transitioned to 'spec' stage and loaded sections!")
            else:
                print("FAILURE: State is incorrect or missing specification data.")
                print(json.dumps(state, indent=2))
                return
    except Exception as e:
        print(f"Error verifying state: {e}")
        return

    print("\nIntegration test task-create succeeded!")

if __name__ == "__main__":
    test_api()
