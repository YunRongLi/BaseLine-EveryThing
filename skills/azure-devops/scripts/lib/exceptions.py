"""
Custom exception hierarchy for Azure DevOps client.
"""

class AdoError(Exception):
    """Base exception for all Azure DevOps client errors."""
    pass


class AdoAuthError(AdoError):
    """Raised when authentication fails or session expires."""
    pass


class AdoNotFoundError(AdoError):
    """Raised when requested work item, project, or resource is not found."""
    pass


class AdoPermissionError(AdoError):
    """Raised when current user does not have permission for the resource."""
    pass


class AdoApiError(AdoError):
    """Raised when Azure DevOps REST API returns an unexpected error."""
    def __init__(self, message: str, status_code: int = 0, response_text: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text

