"""
Configuration management for Azure DevOps skill.
Supports local (.ado.json / .obmc-tool.json), user global
(~/.config/azure-devops/config.json and fallback ~/.config/obmc-dev-tool/config.json),
and environment variables.
"""

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional


@dataclass
class ToolConfig:
    organization: str = ""
    project: str = ""
    projects: List[str] = field(default_factory=list)
    author: str = ""
    download_dir: str = "./downloads"
    output_dir: str = "./output"

    @classmethod
    def load(cls) -> "ToolConfig":
        config = cls()

        # 1. Fallback legacy config file
        legacy_path = Path.home() / ".config" / "obmc-dev-tool" / "config.json"
        if legacy_path.exists():
            config._merge_from_file(legacy_path)

        # 2. Skill global config file (~/.config/azure-devops/config.json)
        global_path = Path.home() / ".config" / "azure-devops" / "config.json"
        if global_path.exists():
            config._merge_from_file(global_path)

        # 3. Local workspace config file (overrides global)
        for local_file in [".obmc-tool.json", ".ado.json"]:
            local_path = Path.cwd() / local_file
            if local_path.exists():
                config._merge_from_file(local_path)

        # 4. Environment variables (highest priority)
        env_org = os.environ.get("AZURE_DEVOPS_ORG") or os.environ.get("ADO_ORGANIZATION")
        if env_org:
            config.organization = env_org

        env_proj = os.environ.get("AZURE_DEVOPS_PROJECT") or os.environ.get("ADO_PROJECT")
        if env_proj:
            config.project = env_proj

        env_projs = os.environ.get("AZURE_DEVOPS_PROJECTS") or os.environ.get("ADO_PROJECTS")
        if env_projs:
            config.projects = [p.strip() for p in env_projs.split(",") if p.strip()]

        env_author = os.environ.get("AZURE_DEVOPS_AUTHOR") or os.environ.get("ADO_AUTHOR") or os.environ.get("OBMC_AUTHOR")
        if env_author:
            config.author = env_author.strip()

        config._sync_projects()
        return config

    def get_author(self) -> str:
        """
        Returns configured author, or falls back to local git config user.name / user.email.
        """
        if self.author:
            return self.author.strip()
        try:
            res_name = subprocess.run(
                ["git", "config", "user.name"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res_name.returncode == 0 and res_name.stdout.strip():
                return res_name.stdout.strip()
            res_email = subprocess.run(
                ["git", "config", "user.email"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res_email.returncode == 0 and res_email.stdout.strip():
                return res_email.stdout.strip()
        except Exception:
            pass
        return ""

    def _sync_projects(self) -> None:
        """
        Synchronizes `project` (active/default project) and `projects` (configured list).
        """
        cleaned_projects: List[str] = []
        for p in self.projects:
            p_clean = p.strip() if isinstance(p, str) else str(p).strip()
            if p_clean and p_clean not in cleaned_projects:
                cleaned_projects.append(p_clean)
        self.projects = cleaned_projects

        if self.project:
            self.project = self.project.strip()
            if self.project and self.project not in self.projects:
                self.projects.insert(0, self.project)
        elif self.projects:
            self.project = self.projects[0]

    def _merge_from_file(self, path: Path) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
                for k, v in data.items():
                    if hasattr(self, k) and v is not None:
                        if k == "projects":
                            if isinstance(v, str):
                                self.projects = [p.strip() for p in v.split(",") if p.strip()]
                            elif isinstance(v, list):
                                self.projects = [str(p).strip() for p in v if str(p).strip()]
                        else:
                            setattr(self, k, v)
            self._sync_projects()
        except Exception:
            pass

    def save_global(self) -> Path:
        global_path = Path.home() / ".config" / "azure-devops" / "config.json"
        global_path.parent.mkdir(parents=True, exist_ok=True)
        with open(global_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)
        return global_path

    def save_local(self) -> Path:
        local_path = Path.cwd() / ".ado.json"
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)
        return local_path

