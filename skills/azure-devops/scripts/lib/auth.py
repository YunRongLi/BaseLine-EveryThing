"""
Azure DevOps Authentication Provider using Azure CLI (az login).
Notice: Personal Access Token (PAT) is strictly prohibited by security policy.
"""

import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

try:
    from .exceptions import AdoAuthError
except ImportError:
    from exceptions import AdoAuthError

AzureCliAuthError = AdoAuthError

UUID_OR_TENANT_REGEX = re.compile(r"^[a-zA-Z0-9_\.\-]+$")


class AzureCliAuthProvider:
    """
    Acquires short-lived OAuth 2.0 Bearer tokens via 'az account get-access-token'.
    Caches token in-memory and automatically refreshes prior to expiration.
    Supports isolated Azure CLI contexts, tenants, and custom resource identifiers.
    """

    def __init__(
        self,
        azure_config_dir: Optional[str] = None,
        tenant: Optional[str] = None,
        resource_id: Optional[str] = None,
        token_margin_seconds: int = 300,
    ):
        self.azure_config_dir = (
            os.path.abspath(os.path.expanduser(azure_config_dir))
            if azure_config_dir
            else None
        )
        self.tenant = tenant.strip() if tenant else None
        self.resource_id = (
            resource_id.strip()
            if resource_id
            else os.environ.get("ADO_RESOURCE_ID", "").strip()
        )
        self._token_margin_seconds = token_margin_seconds
        # In-memory token cache keyed by (azure_config_dir, tenant, resource_id)
        self._cache: Dict[Tuple[Optional[str], Optional[str], str], Dict[str, Any]] = {}

    def _ensure_az_available(self) -> None:
        if not shutil.which("az"):
            raise AdoAuthError(
                "Azure CLI ('az') executable not found in PATH.\n"
                "Please install Azure CLI and authenticate with 'az login'."
            )

    def _validate_inputs(self) -> None:
        if not self.resource_id:
            raise AdoAuthError(
                "Azure DevOps application resource identifier is not configured.\n"
                "Please configure via 'ado config --set resource_id=<ID>' or set ADO_RESOURCE_ID env var."
            )
        if self.tenant and not UUID_OR_TENANT_REGEX.match(self.tenant):
            raise AdoAuthError(f"Invalid tenant format: '{self.tenant}'.")
        if not UUID_OR_TENANT_REGEX.match(self.resource_id):
            raise AdoAuthError("Invalid resource_id format.")

    def get_token(self, force_refresh: bool = False) -> str:
        """
        Retrieves a valid Azure DevOps Bearer token.
        Uses in-memory cache if token has more than token_margin_seconds validity remaining.
        """
        self._validate_inputs()
        cache_key = (self.azure_config_dir, self.tenant, self.resource_id)
        now = time.time()

        cached_entry = self._cache.get(cache_key)
        if not force_refresh and cached_entry:
            expires_at = cached_entry.get("expires_at", 0.0)
            token = cached_entry.get("token", "")
            if token and now < (expires_at - self._token_margin_seconds):
                return token

        self._ensure_az_available()

        cmd = [
            "az",
            "account",
            "get-access-token",
            "--resource",
            self.resource_id,
            "--output",
            "json",
        ]
        if self.tenant:
            cmd.extend(["--tenant", self.tenant])

        env = os.environ.copy()
        if self.azure_config_dir:
            env["AZURE_CONFIG_DIR"] = self.azure_config_dir

        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True,
                timeout=25,
            )
        except subprocess.TimeoutExpired:
            raise AdoAuthError("Azure CLI command timed out while acquiring access token.")
        except subprocess.CalledProcessError as e:
            err = (e.stderr or e.stdout or "").strip()
            raise AdoAuthError(
                "Failed to acquire Azure DevOps access token via Azure CLI.\n"
                f"Command returned exit code {e.returncode}.\n"
                "Please run 'az login' in your terminal to establish an active session.\n"
                f"Details: {err}"
            )
        except Exception as e:
            raise AdoAuthError(f"Unexpected error executing Azure CLI: {str(e)}")

        try:
            payload = json.loads(result.stdout)
            token = payload.get("accessToken")
            if not token:
                raise AdoAuthError("Azure CLI returned JSON missing 'accessToken' field.")

            expires_on_str = payload.get("expiresOn", "")
            expires_at = self._parse_expires_on(expires_on_str, now)

            self._cache[cache_key] = {
                "token": token,
                "expires_at": expires_at,
            }
            return token

        except json.JSONDecodeError as e:
            raise AdoAuthError(f"Failed to parse JSON output from Azure CLI: {str(e)}")

    def _parse_expires_on(self, expires_on_str: str, current_timestamp: float) -> float:
        """Parses expiresOn timestamp string or falls back to a 45-minute default TTL."""
        if not expires_on_str:
            return current_timestamp + 2700

        try:
            cleaned = expires_on_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            return current_timestamp + 2700

    def get_auth_headers(self) -> Dict[str, str]:
        """Returns standard HTTP Authorization header containing Bearer token."""
        token = self.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
