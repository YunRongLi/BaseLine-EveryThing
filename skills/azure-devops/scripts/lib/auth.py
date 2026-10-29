"""
Azure DevOps Authentication Provider using Azure CLI (az login).
Notice: Personal Access Token (PAT) is strictly prohibited by security policy.
"""

import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from typing import Dict, Optional

try:
    from .exceptions import AdoAuthError
except ImportError:
    from exceptions import AdoAuthError

AzureCliAuthError = AdoAuthError


class AzureCliAuthProvider:
    """
    Acquires short-lived OAuth 2.0 Bearer tokens via 'az account get-access-token'.
    Caches token in-memory and automatically refreshes prior to expiration.
    """

    # Official Azure DevOps Well-Known Resource ID
    ADO_RESOURCE_ID = "499b84ac-1321-427f-aa17-267ca6975798"

    def __init__(self, token_margin_seconds: int = 300):
        self._cached_token: Optional[str] = None
        self._expires_at: float = 0.0
        self._token_margin_seconds = token_margin_seconds

    def _ensure_az_available(self) -> None:
        if not shutil.which("az"):
            raise AdoAuthError(
                "Azure CLI ('az') executable not found in PATH.\n"
                "Please install Azure CLI and authenticate with 'az login'."
            )

    def get_token(self, force_refresh: bool = False) -> str:
        """
        Retrieves a valid Azure DevOps Bearer token.
        Uses in-memory cache if token has more than token_margin_seconds validity remaining.
        """
        now = time.time()
        if not force_refresh and self._cached_token and now < (self._expires_at - self._token_margin_seconds):
            return self._cached_token

        self._ensure_az_available()

        cmd = [
            "az", "account", "get-access-token",
            "--resource", self.ADO_RESOURCE_ID,
            "--output", "json"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            err = (e.stderr or e.stdout or "").strip()
            raise AdoAuthError(
                "Failed to acquire Azure DevOps access token via Azure CLI.\n"
                f"Command returned exit code {e.returncode}.\n"
                "Please run 'az login' in your terminal to establish an active session.\n"
                f"Details: {err}"
            )
        except Exception as e:
            raise AdoAuthError(f"Unexpected error running Azure CLI: {str(e)}")

        try:
            payload = json.loads(result.stdout)
            token = payload.get("accessToken")
            if not token:
                raise AdoAuthError("Azure CLI returned JSON missing 'accessToken' field.")
            self._cached_token = token

            expires_on_str = payload.get("expiresOn", "")
            self._expires_at = self._parse_expires_on(expires_on_str, now)
            return self._cached_token

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

