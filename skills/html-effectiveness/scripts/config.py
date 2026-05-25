import os

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
