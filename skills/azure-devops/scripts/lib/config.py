"""
Configuration management for Azure DevOps skill.
Supports named profiles, multi-domain environments, local (.ado.json),
user global (~/.config/azure-devops/config.json), and environment variables.
"""

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Dict, List, Optional

PROFILE_NAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+$")


@dataclass
class ProfileConfig:
    organization: str = ""
    azure_config_dir: str = ""
    tenant: str = ""
    resource_id: str = ""
    project: str = ""
    projects: List[str] = field(default_factory=list)

    def matches_project(self, target_project: str) -> bool:
        if not target_project:
            return False
        p = target_project.strip().lower()
        if self.project and self.project.strip().lower() == p:
            return True
        return any(proj.strip().lower() == p for proj in self.projects)

    def matches_azure_config_dir(self, target_dir: str) -> bool:
        if not target_dir or not self.azure_config_dir:
            return False
        try:
            cfg_path = os.path.abspath(os.path.expanduser(self.azure_config_dir)).rstrip("/")
            tgt_path = os.path.abspath(os.path.expanduser(target_dir)).rstrip("/")
            return cfg_path == tgt_path
        except Exception:
            return False


@dataclass
class ToolConfig:
    active_profile: str = "default"
    profiles: Dict[str, ProfileConfig] = field(default_factory=dict)
    organization: str = ""
    azure_config_dir: str = ""
    tenant: str = ""
    resource_id: str = ""
    project: str = ""
    projects: List[str] = field(default_factory=list)
    author: str = ""
    download_dir: str = "./downloads"
    output_dir: str = "./output"

    @classmethod
    def load(cls) -> "ToolConfig":
        config = cls()

        # 1. Skill global config file (~/.config/azure-devops/config.json)
        global_path = Path.home() / ".config" / "azure-devops" / "config.json"
        if global_path.exists():
            config._merge_from_file(global_path)

        # 2. Local workspace config file (overrides global)
        local_path = Path.cwd() / ".ado.json"
        if local_path.exists():
            config._merge_from_file(local_path)

        # 3. Environment variables (highest priority)
        env_profile = os.environ.get("ADO_PROFILE") or os.environ.get("AZURE_DEVOPS_PROFILE")
        if env_profile and PROFILE_NAME_REGEX.match(env_profile):
            config.active_profile = env_profile

        env_org = os.environ.get("AZURE_DEVOPS_ORG") or os.environ.get("ADO_ORGANIZATION")
        if env_org:
            config.organization = env_org

        env_proj = os.environ.get("AZURE_DEVOPS_PROJECT") or os.environ.get("ADO_PROJECT")
        if env_proj:
            config.project = env_proj

        env_projs = os.environ.get("AZURE_DEVOPS_PROJECTS") or os.environ.get("ADO_PROJECTS")
        if env_projs:
            config.projects = [p.strip() for p in env_projs.split(",") if p.strip()]

        env_author = os.environ.get("AZURE_DEVOPS_AUTHOR") or os.environ.get("ADO_AUTHOR")
        if env_author:
            config.author = env_author.strip()

        env_cfg_dir = os.environ.get("AZURE_CONFIG_DIR")
        if env_cfg_dir:
            config.azure_config_dir = env_cfg_dir

        config._sync_projects()
        return config

    def get_active_profile(
        self,
        profile_override: Optional[str] = None,
        project_override: Optional[str] = None,
    ) -> ProfileConfig:
        """
        Resolves active profile by priority:
        1. Explicit profile override argument
        2. Explicit project override matching a profile's project list
        3. Active AZURE_CONFIG_DIR environment matching a profile's config dir
        4. Configured active_profile
        5. Fallback synthesized from top-level config attributes
        """
        # 1. Profile override
        if profile_override:
            if profile_override in self.profiles:
                return self.profiles[profile_override]
            for p_name, p_cfg in self.profiles.items():
                if p_name.lower() == profile_override.lower():
                    return p_cfg

        # 2. Project override match
        if project_override:
            for p_name, p_cfg in self.profiles.items():
                if p_cfg.matches_project(project_override):
                    return p_cfg

        # 3. Current AZURE_CONFIG_DIR environment variable match
        env_az_dir = os.environ.get("AZURE_CONFIG_DIR")
        if env_az_dir:
            for p_name, p_cfg in self.profiles.items():
                if p_cfg.matches_azure_config_dir(env_az_dir):
                    return p_cfg

        # 4. Contextual auto-detection (git remote and workspace path heuristics)
        detected = self._detect_profile_from_git_and_path()
        if detected:
            return detected

        # 5. Configured active profile
        if self.active_profile in self.profiles:
            return self.profiles[self.active_profile]

        # 6. Fallback to first configured profile if active_profile is unset or 'default'
        if self.profiles and not self.organization:
            for p_cfg in self.profiles.values():
                if p_cfg.organization:
                    return p_cfg
            return next(iter(self.profiles.values()))

        # 7. Fallback synthesis from top-level config attributes
        return ProfileConfig(
            organization=self.organization,
            azure_config_dir=self.azure_config_dir,
            tenant=self.tenant,
            resource_id=self.resource_id,
            project=self.project,
            projects=list(self.projects),
        )

    def _detect_profile_from_git_and_path(self) -> Optional[ProfileConfig]:
        """
        Attempts to infer profile from current git remote URL or workspace directory name.
        """
        if not self.profiles:
            return None

        # Check git remote
        try:
            res = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res.returncode == 0 and res.stdout:
                out = res.stdout.lower()
                for p_name, p_cfg in self.profiles.items():
                    if p_cfg.organization:
                        clean_org = p_cfg.organization.lower().replace("https://", "").replace("http://", "").strip("/")
                        org_domain = clean_org.split(".")[0].split("/")[-1]
                        if org_domain and org_domain in out:
                            return p_cfg
                    for proj in p_cfg.projects:
                        if proj and proj.lower() in out:
                            return p_cfg
        except Exception:
            pass

        # Check path heuristics (e.g. /home/.../MSFTWS contains msft)
        try:
            cwd_str = str(Path.cwd()).lower()
            for p_name, p_cfg in self.profiles.items():
                if p_name.lower() in cwd_str:
                    return p_cfg
        except Exception:
            pass

        return None

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
        Synchronizes project and projects list.
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

        for p_cfg in self.profiles.values():
            if p_cfg.project and p_cfg.project not in p_cfg.projects:
                p_cfg.projects.insert(0, p_cfg.project)
            elif p_cfg.projects and not p_cfg.project:
                p_cfg.project = p_cfg.projects[0]

    def _merge_from_file(self, path: Path) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)

            if "profiles" in data and isinstance(data["profiles"], dict):
                for p_name, p_data in data["profiles"].items():
                    if isinstance(p_data, dict):
                        p_projs = p_data.get("projects", [])
                        if isinstance(p_projs, str):
                            p_projs = [p.strip() for p in p_projs.split(",") if p.strip()]
                        self.profiles[p_name] = ProfileConfig(
                            organization=p_data.get("organization", ""),
                            azure_config_dir=p_data.get("azure_config_dir", ""),
                            tenant=p_data.get("tenant", ""),
                            resource_id=p_data.get("resource_id", ""),
                            project=p_data.get("project", ""),
                            projects=p_projs,
                        )

            for k, v in data.items():
                if k == "profiles":
                    continue
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

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    def save_global(self) -> Path:
        global_path = Path.home() / ".config" / "azure-devops" / "config.json"
        global_path.parent.mkdir(parents=True, exist_ok=True)
        with open(global_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        try:
            os.chmod(global_path, 0o600)
        except OSError:
            pass
        return global_path

    def save_local(self) -> Path:
        local_path = Path.cwd() / ".ado.json"
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        try:
            os.chmod(local_path, 0o600)
        except OSError:
            pass
        return local_path
