"""
Azure DevOps library module.
"""

from .auth import AzureCliAuthProvider, AzureCliAuthError
from .client import AzureDevOpsClient
from .config import ToolConfig
from .exceptions import (
    AdoError,
    AdoAuthError,
    AdoNotFoundError,
    AdoPermissionError,
    AdoApiError,
)
from .work_items import WorkItemService, WorkItem, WorkItemAttachment
from .pull_requests import PullRequestService, PullRequest, PRThread, PRComment
from .formatter import (
    PRTerminalFormatter,
    PRAgentMarkdownReporter,
    WITerminalFormatter,
    WIAgentMarkdownReporter,
)

__all__ = [
    "AzureCliAuthProvider",
    "AzureCliAuthError",
    "AzureDevOpsClient",
    "ToolConfig",
    "AdoError",
    "AdoAuthError",
    "AdoNotFoundError",
    "AdoPermissionError",
    "AdoApiError",
    "WorkItemService",
    "WorkItem",
    "WorkItemAttachment",
    "PullRequestService",
    "PullRequest",
    "PRThread",
    "PRComment",
    "PRTerminalFormatter",
    "PRAgentMarkdownReporter",
    "WITerminalFormatter",
    "WIAgentMarkdownReporter",
]

