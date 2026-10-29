"""
Base HTTP client for Azure DevOps REST API.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import requests

try:
    from .auth import AzureCliAuthProvider
    from .exceptions import (
        AdoApiError,
        AdoAuthError,
        AdoNotFoundError,
        AdoPermissionError,
    )
except ImportError:
    from auth import AzureCliAuthProvider
    from exceptions import (
        AdoApiError,
        AdoAuthError,
        AdoNotFoundError,
        AdoPermissionError,
    )


class AzureDevOpsClient:
    """
    HTTP Client handling authentication headers, URL building, and error mapping.
    """

    DEFAULT_API_VERSION = "7.0"

    def __init__(
        self,
        organization: str,
        project: Optional[str] = None,
        auth_provider: Optional[AzureCliAuthProvider] = None,
        timeout_seconds: int = 30,
    ):
        clean_org = organization.strip().rstrip("/")
        if not clean_org.startswith("http"):
            clean_org = f"https://dev.azure.com/{clean_org}"
        self.organization = clean_org
        self.project = project.strip() if project else None
        self.auth_provider = auth_provider or AzureCliAuthProvider()
        self.timeout = timeout_seconds
        self.session = requests.Session()

    def _build_url(self, endpoint: str, scoped_to_project: bool = True) -> str:
        """
        Builds the fully qualified REST API URL.
        Example:
        - scoped: https://dev.azure.com/org/project/_apis/wit/workitems/123
        - unscoped: https://dev.azure.com/org/_apis/projects
        """
        endpoint = endpoint.lstrip("/")
        if scoped_to_project and self.project:
            return f"{self.organization}/{self.project}/_apis/{endpoint}"
        return f"{self.organization}/_apis/{endpoint}"

    def _handle_response(self, response: requests.Response) -> Any:
        if 200 <= response.status_code < 300:
            if not response.content:
                return {}
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return response.json()
            return response.text

        if response.status_code == 401:
            raise AdoAuthError(
                "Azure DevOps returned 401 Unauthorized.\n"
                "Session may have expired. Try running 'az login' again."
            )
        elif response.status_code == 403:
            raise AdoPermissionError(
                f"Azure DevOps returned 403 Forbidden: current identity lacks access to resource.\n"
                f"Response: {response.text}"
            )
        elif response.status_code == 404:
            raise AdoNotFoundError(
                f"Azure DevOps resource not found (404).\nResponse: {response.text}"
            )
        else:
            raise AdoApiError(
                f"Azure DevOps API request failed with HTTP {response.status_code}",
                status_code=response.status_code,
                response_text=response.text,
            )

    def request(
        self,
        method: str,
        endpoint: str,
        scoped_to_project: bool = True,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        url = self._build_url(endpoint, scoped_to_project=scoped_to_project)
        req_params = {"api-version": self.DEFAULT_API_VERSION}
        if params:
            req_params.update(params)

        req_headers = self.auth_provider.get_auth_headers()
        if headers:
            req_headers.update(headers)

        response = self.session.request(
            method=method,
            url=url,
            params=req_params,
            json=json_data,
            headers=req_headers,
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def get(self, endpoint: str, **kwargs) -> Any:
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> Any:
        return self.request("POST", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs) -> Any:
        return self.request("PATCH", endpoint, **kwargs)

    def download_file(self, download_url: str, destination: Path) -> Path:
        """
        Downloads a binary or text attachment directly to disk using authenticated streaming.
        """
        headers = self.auth_provider.get_auth_headers()
        response = self.session.get(download_url, headers=headers, stream=True, timeout=self.timeout)
        if response.status_code != 200:
            self._handle_response(response)

        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
        return destination

