import json
import os

CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def set_vault_path(path):
    config = load_config()
    config['vault_path'] = path
    save_config(config)
    print(f'檔案庫路徑已設定為: {path}')

def set_obsidian_app_path(path):
    config = load_config()
    config['obsidian_app_path'] = path
    save_config(config)
    print(f'Obsidian 應用程式路徑已設定為: {path}')
