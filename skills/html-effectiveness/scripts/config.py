import os

def load_env():
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                raw = line.strip()
                if raw and not raw.startswith('#') and '=' in raw:
                    key, val = raw.split('=', 1)
                    key = key.strip()
                    if key.startswith("VLLM_"):
                        value = val.strip().strip('"').strip("'")
                        os.environ[key] = value


def persist_env(entries, env_path='.env'):
    env_path = os.path.abspath(env_path)
    existing_lines = []
    processed_keys = set()
    
    # Only VLLM variables are allowed to be saved to the .env file.
    # Other API keys (GEMINI, ANTHROPIC) are applied to the active session only.
    file_entries = {k: v for k, v in entries.items() if k.startswith("VLLM_")}

    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.rstrip('\n')
                if stripped.strip() and not stripped.strip().startswith('#') and '=' in stripped:
                    key, _ = stripped.split('=', 1)
                    key = key.strip()
                    
                    # Remove any leaked API keys from existing .env to ensure security
                    if not key.startswith("VLLM_") and (key.startswith("GEMINI_") or key.startswith("ANTHROPIC_")):
                        continue

                    if key in file_entries:
                        value = file_entries[key]
                        processed_keys.add(key)
                        if value is None or value == '':
                            continue
                        existing_lines.append(f"{key}={value}")
                        continue
                existing_lines.append(stripped)

    for key, value in file_entries.items():
        if key in processed_keys:
            continue
        if value is None or value == '':
            continue
        existing_lines.append(f"{key}={value}")

    with open(env_path, 'w', encoding='utf-8') as f:
        for line in existing_lines:
            f.write(f"{line}\n")

    # Update os.environ with ALL entries (both file-saved and session-only)
    for key, value in entries.items():
        if value is None or value == '':
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def get_vllm_url():
    return os.environ.get("VLLM_API_URL", "").strip()

def check_vllm_url():
    return bool(get_vllm_url())

def check_api_key_gemini():
    return "GEMINI_API_KEY" in os.environ

def check_api_key_anthropic():
    return "ANTHROPIC_ADMIN_API_KEY" in os.environ or "ANTHROPIC_API_KEY" in os.environ

def check_api_key():
    return check_api_key_gemini() or check_api_key_anthropic() or check_vllm_url()

# Global Memory state for the workflow (completely structured JSON)
