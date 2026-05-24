import os
import sys
import time
from config import load_config, set_vault_path, set_obsidian_app_path
from cli_wrapper import ObsidianCLIWrapper
from classifier import NoteClassifier
from indexer import ContentMapIndexer

def setup_initial_config():
    config = load_config()
    if not config.get("vault_path"):
        vault_input = input("請輸入您的 Obsidian 檔案庫路徑: ")
        set_vault_path(vault_input)
    if not config.get("obsidian_app_path"):
        app_input = input("請輸入您的 Obsidian 應用程式執行檔路徑 (例如: /Applications/Obsidian.app 或 C:\\Users\\<使用者名稱>\\AppData\\Local\\Obsidian\\Obsidian.exe): ")
        set_obsidian_app_path(app_input)
    return load_config()

def main():
    current_config = setup_initial_config()
    vault_path = current_config.get("vault_path")
    obsidian_app_path = current_config.get("obsidian_app_path")
    
    if not vault_path or not obsidian_app_path:
        print("Obsidian 檔案庫或應用程式路徑未設定，請重新啟動並設定。")
        return

    cli = ObsidianCLIWrapper(vault_path, obsidian_app_path)
    classifier = NoteClassifier()
    indexer = ContentMapIndexer(vault_path)

    # 步驟一延伸：啟動 Obsidian 並驗證 Vault 狀態
    try:
        print("嘗試在背景啟動 Obsidian...")
        cli.start_obsidian_hidden()
        # 給 Obsidian 一點時間啟動
        time.sleep(5) 
        print("驗證 Obsidian 檔案庫狀態...")
        vault_info = cli.get_vault_status()
        print(f"Vault 狀態：{vault_info}")
    except Exception as e:
        print(f"背景啟動或驗證 Vault 失敗：{e}")
        # return # 決定這是否是足以停止程序的關鍵錯誤

    # 步驟二：執行檔案庫結構掃描與索引
    try:
        print("開始執行檔案庫結構掃描與索引...")
        indexer.index_vault()
        print("檔案庫索引完成。")
    except Exception as e:
        print(f"索引過程中發生錯誤: {e}")
        return

    raw_note = "今天與研發團隊討論新功能，確認下週交付原型。" # 範例隨手記內容
    instruction = "#action" # 範例歸檔提示

    category, title, formatted_content = classifier.classify_and_format(raw_note, instruction)
    
    target_folder = "00_Inbox"
    if category == "Action":
        target_folder = "Efforts/Projects"
    elif category == "Context":
        target_folder = "Atlas/Contexts"
    elif category == "Reference":
        target_folder = "Atlas/Resources"

    # 確保標題是有效的文件名，例如替換特殊字符
    sanitized_title = "_".join(c for c in title if c.isalnum() or c in [' ', '_']).rstrip().replace(' ', '_')
    file_name = f"{sanitized_title}.md"
    relative_path = os.path.join(target_folder, file_name)

    try:
        cli.create_note(relative_path, formatted_content)
        print(f"成功歸檔至: {relative_path}")
        
        # 步驟六：自動更新內容地圖
        # 透過索引器找到最相關的內容地圖
        related_moc_path = indexer.get_related_content_map(raw_note)
        if related_moc_path:
            update_link = f"\n- [[{title}]] : 新增的相關項目摘要"
            cli.append_to_note(related_moc_path, update_link)
            print(f"成功更新內容地圖: {related_moc_path}")
            indexer.incremental_update(f"[[{title}]]", related_moc_path) # 觸發增量更新與快取淘汰
        else:
            print("未找到相關內容地圖進行更新。")

    except Exception as e:
        print(f"處理過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()