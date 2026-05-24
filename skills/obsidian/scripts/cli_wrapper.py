import subprocess
import os
import sys
import time

class ObsidianCLIWrapper:
    def __init__(self, vault_path, obsidian_app_path=None):
        self.vault_path = vault_path
        self.obsidian_app_path = obsidian_app_path

    def _build_command_list(self, base_cmd_parts, args):
        """
        根據作業系統建立安全的命令列指令列表。
        """
        if sys.platform == 'win32':
            return ['cmd', '/c'] + base_cmd_parts + args
        else:
            return base_cmd_parts + args

    def run_obsidian_cli_tool_command(self, args):
        """
        安全執行 obsidian-cli 命令列工具（第三方工具），防止命令注入並相容多作業系統環境。
        """
        cmd_list = self._build_command_list(['obsidian-cli'], args)
        
        try:
            result = subprocess.run(
                cmd_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                encoding='utf-8'
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f'執行 obsidian-cli 失敗: {e.stderr.strip()}')
        except FileNotFoundError:
            raise RuntimeError('找不到 obsidian-cli。請確認它已安裝並在系統 PATH 中。')

    def run_official_obsidian_app_command(self, args):
        """
        安全執行官方 Obsidian 應用程式的命令列指令。
        """
        if not self.obsidian_app_path:
            raise ValueError("Obsidian 應用程式路徑未設定。")
        
        executable_path = self.obsidian_app_path
        # For macOS, need to point to the executable inside the app bundle
        if sys.platform == 'darwin' and '.app' in self.obsidian_app_path:
            executable_path = os.path.join(self.obsidian_app_path, 'Contents', 'MacOS', 'Obsidian')
            
        cmd_list = self._build_command_list([executable_path], args)

        try:
            result = subprocess.run(
                cmd_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                encoding='utf-8'
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f'執行官方 Obsidian 指令失敗: {e.stderr.strip()}')
        except FileNotFoundError:
            raise RuntimeError(f'找不到 Obsidian 應用程式在 "{executable_path}"。請確認路徑正確。')

    def start_obsidian_hidden(self):
        """
        以隱藏視窗模式啟動 Obsidian 應用程式，作為背景程序。
        """
        if not self.obsidian_app_path:
            raise ValueError("Obsidian 應用程式路徑未設定，無法啟動。")

        executable_path = self.obsidian_app_path
        args = []

        if sys.platform == 'win32':
            args = ['--hidden']
            print(f'嘗試以隱藏模式啟動 Obsidian (Windows): "{executable_path}" {args}')
            subprocess.Popen([executable_path] + args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
        elif sys.platform == 'darwin':
            executable_path = os.path.join(self.obsidian_app_path, 'Contents', 'MacOS', 'Obsidian')
            args = ['--hidden']
            print(f'嘗試以隱藏模式啟動 Obsidian (macOS): "{executable_path}" {args}')
            subprocess.Popen([executable_path] + args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
        else:
            print(f"此功能目前不支援此作業系統 ({sys.platform}) 或需要更多資訊來啟動 Obsidian 應用程式。")
            raise NotImplementedError(f"背景啟動 Obsidian 不支援 {sys.platform}")

    def get_vault_status(self, vault_name=None):
        """
        使用官方 Obsidian CLI 查詢指定 Vault 的狀態。
        """
        if not vault_name and self.vault_path:
            # Try to infer vault name from path if not provided
            vault_name = os.path.basename(self.vault_path)

        if not vault_name:
            raise ValueError("需要提供檔案庫名稱或在初始化時提供檔案庫路徑，才能查詢狀態。")
        
        # The user's example `obsidian vault="YourVaultName" info=path` implies 
        # passing these as direct arguments to the official Obsidian executable.
        args = [f'vault="{vault_name}"', 'info=path']
        print(f'嘗試使用官方 Obsidian 應用程式查詢 Vault 狀態：{vault_name}')
        return self.run_official_obsidian_app_command(args)

    def create_note(self, relative_path, content):
        """
        建立新筆記並寫入內容，使用 obsidian-cli 工具。
        路徑與內容作為獨立參數傳遞，防止命令注入。
        """
        # Ensure the target directory exists within the vault using os.path
        full_target_dir = os.path.join(self.vault_path, os.path.dirname(relative_path))
        if not os.path.exists(full_target_dir):
            os.makedirs(full_target_dir, exist_ok=True)

        args = ['create', '--path', relative_path, '--content', content]
        return self.run_obsidian_cli_tool_command(args)

    def append_to_note(self, relative_path, content):
        """
        在現有筆記末端追加內容，使用 obsidian-cli 工具。
        路徑與內容作為獨立參數傳遞，防止命令注入。
        """
        args = ['append', '--path', relative_path, '--content', content]
        return self.run_obsidian_cli_tool_command(args)
