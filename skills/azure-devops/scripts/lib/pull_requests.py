"""
Azure DevOps Pull Request Service.
Handles inspecting PR metadata, listing active PRs, fetching review threads,
posting review replies, and formatting PR context for AI agents.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from .client import AzureDevOpsClient
    from .exceptions import AdoError
except ImportError:
    from client import AzureDevOpsClient
    from exceptions import AdoError


@dataclass
class PRComment:
    id: int
    parent_id: int
    author_name: str
    author_email: str
    content: str
    published_date: str
    comment_type: str = "text"
    is_deleted: bool = False


@dataclass
class PRThread:
    id: int
    status: str
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    comments: List[PRComment] = field(default_factory=list)
    is_deleted: bool = False

    @property
    def is_active(self) -> bool:
        return self.status.lower() in ("active", "pending", "unknown")

    @property
    def human_comments(self) -> List[PRComment]:
        return [
            c for c in self.comments
            if not c.is_deleted and c.comment_type == "text" and c.content and c.content.strip()
        ]


@dataclass
class PullRequest:
    id: int
    title: str
    description: str
    status: str
    created_by: str
    created_by_id: str
    repository_id: str
    repository_name: str
    project_name: str
    source_branch: str
    target_branch: str
    web_url: str
    creation_date: str
    created_by_email: str = ""
    reviewers: List[Dict[str, Any]] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def matches_author(self, pattern: str) -> bool:
        if not pattern:
            return True
        p = pattern.strip().lower()
        if not p:
            return True

        if p in self.created_by.lower():
            return True
        if self.created_by_email and p in self.created_by_email.lower():
            return True
        if self.created_by_id and p == self.created_by_id.lower():
            return True

        src = self.source_branch.lower()
        if src.startswith(f"user/{p}/") or src.startswith(f"users/{p}/") or f"/{p}/" in src:
            return True

        for part in p.split():
            if len(part) >= 3 and (part in self.created_by.lower() or (self.created_by_email and part in self.created_by_email.lower())):
                return True

        return False


class PullRequestService:
    """
    High-level service for interacting with Azure DevOps Pull Requests.
    """

    def __init__(self, client: AzureDevOpsClient, repository_id: Optional[str] = None):
        self.client = client
        self.repository_id = repository_id

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves the authenticated user identity via connectionData.
        """
        try:
            data = self.client.get(
                "connectionData",
                scoped_to_project=False,
                params={"api-version": "7.0-preview"},
            )
            return data.get("authenticatedUser")
        except Exception:
            return None

    def get_pull_request(
        self,
        pr_id: int,
        repository_id: Optional[str] = None,
        project: Optional[str] = None,
    ) -> PullRequest:
        """
        Fetches pull request details by ID.
        """
        repo = repository_id or self.repository_id
        if repo:
            endpoint = f"git/repositories/{repo}/pullrequests/{pr_id}"
            data = self.client.get(endpoint, scoped_to_project=bool(project))
        else:
            endpoint = f"git/pullrequests/{pr_id}"
            data = self.client.get(endpoint, scoped_to_project=False)

        return self._parse_pull_request(data)

    def list_pull_requests(
        self,
        project: Optional[str] = None,
        creator_id: Optional[str] = None,
        status: str = "active",
        top: Optional[int] = None,
    ) -> List[PullRequest]:
        """
        Lists pull requests filtered by project, status, and creator.
        """
        endpoint = "git/pullrequests"
        params: Dict[str, Any] = {"searchCriteria.status": status}
        if creator_id:
            params["searchCriteria.creatorId"] = creator_id
        if top:
            params["$top"] = top

        original_project = self.client.project
        if project:
            self.client.project = project

        try:
            scoped = bool(self.client.project)
            data = self.client.get(endpoint, scoped_to_project=scoped, params=params)
        finally:
            self.client.project = original_project

        raw_list = data.get("value", []) if isinstance(data, dict) else []
        return [self._parse_pull_request(item) for item in raw_list]

    def get_threads(
        self,
        pr_id: int,
        repository_id: str,
        project: Optional[str] = None,
        active_only: bool = False,
    ) -> List[PRThread]:
        """
        Fetches comment threads on a pull request.
        """
        endpoint = f"git/repositories/{repository_id}/pullrequests/{pr_id}/threads"

        original_project = self.client.project
        if project:
            self.client.project = project

        try:
            data = self.client.get(endpoint, scoped_to_project=bool(self.client.project))
        finally:
            self.client.project = original_project

        threads_raw = data.get("value", []) if isinstance(data, dict) else []
        threads: List[PRThread] = []

        for tr in threads_raw:
            if tr.get("isDeleted"):
                continue

            status = tr.get("status", "unknown")
            thread_ctx = tr.get("threadContext") or {}
            file_path = thread_ctx.get("filePath")

            line_start = None
            line_end = None
            if "rightFileStart" in thread_ctx:
                line_start = thread_ctx["rightFileStart"].get("line")
            elif "leftFileStart" in thread_ctx:
                line_start = thread_ctx["leftFileStart"].get("line")

            if "rightFileEnd" in thread_ctx:
                line_end = thread_ctx["rightFileEnd"].get("line")
            elif "leftFileEnd" in thread_ctx:
                line_end = thread_ctx["leftFileEnd"].get("line")

            comments: List[PRComment] = []
            for c in tr.get("comments", []):
                author_dict = c.get("author", {})
                author_name = author_dict.get("displayName", "Unknown")
                author_email = author_dict.get("uniqueName", "")

                comment_obj = PRComment(
                    id=c.get("id", 0),
                    parent_id=c.get("parentCommentId", 0),
                    author_name=author_name,
                    author_email=author_email,
                    content=c.get("content", ""),
                    published_date=c.get("publishedDate", ""),
                    comment_type=c.get("commentType", "text"),
                    is_deleted=bool(c.get("isDeleted")),
                )
                comments.append(comment_obj)

            thread_obj = PRThread(
                id=tr.get("id", 0),
                status=status,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                comments=comments,
                is_deleted=bool(tr.get("isDeleted")),
            )

            if active_only and not thread_obj.is_active:
                continue

            threads.append(thread_obj)

        return threads

    def reply_to_thread(
        self,
        pr_id: int,
        repository_id: str,
        thread_id: int,
        comment_text: str,
        project: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Posts a reply comment to an existing PR review thread.
        """
        endpoint = f"git/repositories/{repository_id}/pullrequests/{pr_id}/threads/{thread_id}/comments"
        payload = {"content": comment_text, "parentCommentId": 1, "commentType": 1}

        original_project = self.client.project
        if project:
            self.client.project = project

        try:
            return self.client.post(endpoint, json_data=payload, scoped_to_project=bool(self.client.project))
        finally:
            self.client.project = original_project

    def _parse_pull_request(self, data: Dict[str, Any]) -> PullRequest:
        pr_id = data.get("pullRequestId", 0)
        title = data.get("title", f"Pull Request #{pr_id}")
        description = data.get("description", "")
        status = data.get("status", "unknown")

        created_by_raw = data.get("createdBy", {})
        created_by = created_by_raw.get("displayName", "Unknown")
        created_by_id = created_by_raw.get("id", "")
        created_by_email = created_by_raw.get("uniqueName", "")

        repo_raw = data.get("repository", {})
        repo_id = repo_raw.get("id", "")
        repo_name = repo_raw.get("name", "Unknown Repo")
        project_name = repo_raw.get("project", {}).get("name", "")

        source_ref = data.get("sourceRefName", "")
        target_ref = data.get("targetRefName", "")
        source_branch = source_ref.replace("refs/heads/", "") if source_ref.startswith("refs/heads/") else source_ref
        target_branch = target_ref.replace("refs/heads/", "") if target_ref.startswith("refs/heads/") else target_ref

        web_url = data.get("_links", {}).get("web", {}).get("href", "")
        if not web_url and repo_raw.get("webUrl"):
            web_url = f"{repo_raw['webUrl']}/pullrequest/{pr_id}"

        creation_date = data.get("creationDate", "")
        reviewers = data.get("reviewers", [])

        return PullRequest(
            id=pr_id,
            title=title,
            description=description,
            status=status,
            created_by=created_by,
            created_by_id=created_by_id,
            created_by_email=created_by_email,
            repository_id=repo_id,
            repository_name=repo_name,
            project_name=project_name,
            source_branch=source_branch,
            target_branch=target_branch,
            web_url=web_url,
            creation_date=creation_date,
            reviewers=reviewers,
            raw_data=data,
        )

