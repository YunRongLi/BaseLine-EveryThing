"""
Azure DevOps Pull Request Service.
Handles inspecting PR metadata, listing active PRs, fetching review threads,
posting review replies, and formatting PR context for AI agents.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

try:
    from .client import AzureDevOpsClient
    from .exceptions import AdoError
except ImportError:
    from client import AzureDevOpsClient
    from exceptions import AdoError


def format_vote(vote: int) -> str:
    if vote >= 10:
        return "Approved"
    elif vote == 5:
        return "Approved with suggestions"
    elif vote == 0:
        return "No vote"
    elif vote == -5:
        return "Waiting for author"
    elif vote <= -10:
        return "Rejected"
    return f"Vote {vote}"


VOTE_NAME_TO_INT: Dict[str, int] = {
    "approve": 10,
    "approved": 10,
    "suggestions": 5,
    "reset": 0,
    "none": 0,
    "wait": -5,
    "waiting": -5,
    "reject": -10,
    "rejected": -10,
}

THREAD_STATUS_MAP: Dict[str, int] = {
    "active": 1,
    "fixed": 2,
    "resolved": 2,
    "wontfix": 3,
    "closed": 4,
    "bydesign": 5,
    "pending": 6,
}


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
    author_id: str = ""

    @property
    def is_bot(self) -> bool:
        name = self.author_name.lower()
        email = self.author_email.lower()
        bot_keywords = ("agency", "stride", "bot", "service account", "build", "pipeline", "automation", "github-actions")
        return any(k in name for k in bot_keywords) or any(k in email for k in bot_keywords)

    @property
    def is_human(self) -> bool:
        return not self.is_bot


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

    @property
    def is_human_thread(self) -> bool:
        return any(c.is_human for c in self.human_comments)

    @property
    def is_bot_thread(self) -> bool:
        return not self.is_human_thread


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
    commits: List[Dict[str, Any]] = field(default_factory=list)
    changed_files: List[Dict[str, str]] = field(default_factory=list)
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

    def has_reviewer(self, pattern: str) -> bool:
        if not pattern:
            return True
        p = pattern.strip().lower()
        for rev in self.reviewers:
            display_name = str(rev.get("displayName", "")).lower()
            unique_name = str(rev.get("uniqueName", "")).lower()
            rev_id = str(rev.get("id", "")).lower()
            if p in display_name or p in unique_name or p == rev_id:
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

    def get_current_user_id(self) -> Optional[str]:
        """
        Returns the GUID identifier for the authenticated user.
        """
        user = self.get_current_user()
        return user.get("id") if user else None

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
        reviewer_id: Optional[str] = None,
        status: str = "active",
        top: Optional[int] = None,
    ) -> List[PullRequest]:
        """
        Lists pull requests filtered by project, status, creator, and/or reviewer.
        """
        endpoint = "git/pullrequests"
        params: Dict[str, Any] = {"searchCriteria.status": status}
        if creator_id:
            params["searchCriteria.creatorId"] = creator_id
        if reviewer_id:
            params["searchCriteria.reviewerId"] = reviewer_id
        if top:
            params["$top"] = top

        original_project = self.client.project
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
                    author_id=author_dict.get("id", ""),
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

    def get_commits(
        self,
        pr_id: int,
        repository_id: Optional[str] = None,
        project: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all commit entries associated with the PR.
        """
        repo = repository_id or self.repository_id
        if not repo:
            pr = self.get_pull_request(pr_id, project=project)
            repo = pr.repository_id
            project = project or pr.project_name

        endpoint = f"git/repositories/{repo}/pullrequests/{pr_id}/commits"
        original_project = self.client.project
        if project:
            self.client.project = project

        try:
            data = self.client.get(endpoint, scoped_to_project=bool(self.client.project))
        except Exception:
            return []
        finally:
            self.client.project = original_project

        raw_commits = data.get("value", []) if isinstance(data, dict) else []
        commits = []
        for c in raw_commits:
            cid = c.get("commitId", "")
            comment = c.get("comment", "")
            author = (
                c.get("author", {}).get("name")
                or c.get("committer", {}).get("name")
                or "Unknown"
            )
            commits.append({
                "id": cid[:8] if cid else "",
                "full_id": cid,
                "author": author,
                "message": comment.strip().splitlines()[0] if comment else "",
            })
        return commits

    def get_changed_files(
        self,
        pr_id: int,
        repository_id: Optional[str] = None,
        project: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Retrieves files changed in the latest PR iteration.
        """
        repo = repository_id or self.repository_id
        if not repo:
            pr = self.get_pull_request(pr_id, project=project)
            repo = pr.repository_id
            project = project or pr.project_name

        original_project = self.client.project
        if project:
            self.client.project = project

        try:
            it_endpoint = f"git/repositories/{repo}/pullrequests/{pr_id}/iterations"
            it_data = self.client.get(it_endpoint, scoped_to_project=bool(self.client.project))
            iterations = it_data.get("value", []) if isinstance(it_data, dict) else []
            if not iterations:
                return []
            latest_it = max(it.get("id", 1) for it in iterations)

            ch_endpoint = f"git/repositories/{repo}/pullrequests/{pr_id}/iterations/{latest_it}/changes"
            ch_data = self.client.get(ch_endpoint, scoped_to_project=bool(self.client.project))
            change_entries = ch_data.get("changeEntries", []) if isinstance(ch_data, dict) else []

            results = []
            for entry in change_entries:
                item = entry.get("item", {})
                path = item.get("path", "")
                change_type = entry.get("changeType", "edit")
                if path:
                    results.append({"path": path, "type": str(change_type).lower()})
            return results
        except Exception:
            return []
        finally:
            self.client.project = original_project

    def update_thread_status(
        self,
        pr_id: int,
        thread_id: int,
        status: str,
        repository_id: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Updates the status of an existing PR review thread (active, fixed, closed, wontfix).
        """
        repo = repository_id or self.repository_id
        if not repo:
            pr = self.get_pull_request(pr_id, project=project)
            repo = pr.repository_id
            project = project or pr.project_name

        status_key = status.strip().lower()
        status_code = THREAD_STATUS_MAP.get(status_key, 2)

        endpoint = f"git/repositories/{repo}/pullrequests/{pr_id}/threads/{thread_id}"
        payload = {"status": status_code}

        original_project = self.client.project
        if project:
            self.client.project = project

        try:
            return self.client.patch(endpoint, json_data=payload, scoped_to_project=bool(self.client.project))
        finally:
            self.client.project = original_project

    def create_thread(
        self,
        pr_id: int,
        comment_text: str,
        repository_id: Optional[str] = None,
        status: str = "active",
        file_path: Optional[str] = None,
        line: Optional[int] = None,
        end_line: Optional[int] = None,
        side: str = "right",
        project: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates a new PR comment thread, optionally anchored to a file and line range.
        """
        if side not in ("right", "left"):
            raise ValueError(f"Invalid side '{side}'. Must be 'right' or 'left'.")
        if line is not None and not file_path:
            raise ValueError("file_path is required when line is specified.")
        if end_line is not None and line is None:
            raise ValueError("line is required when end_line is specified.")
        if line is not None and line < 1:
            raise ValueError("line must be >= 1.")
        if end_line is not None and end_line < line:
            raise ValueError("end_line must be >= line.")

        repo = repository_id or self.repository_id
        if not repo:
            pr = self.get_pull_request(pr_id, project=project)
            repo = pr.repository_id
            project = project or pr.project_name

        original_project = self.client.project
        if project:
            self.client.project = project

        try:
            endpoint = f"git/repositories/{repo}/pullrequests/{pr_id}/threads"
            payload: Dict[str, Any] = {
                "comments": [
                    {
                        "parentCommentId": 0,
                        "content": comment_text,
                        "commentType": 1,
                    }
                ],
                "status": status,
            }

            if file_path:
                normalized_path = file_path if file_path.startswith("/") else f"/{file_path}"
                thread_context: Dict[str, Any] = {"filePath": normalized_path}
                if line is not None:
                    start_key = "rightFileStart" if side == "right" else "leftFileStart"
                    end_key = "rightFileEnd" if side == "right" else "leftFileEnd"
                    effective_end = end_line if end_line is not None else line
                    thread_context[start_key] = {"line": line, "offset": 1}
                    thread_context[end_key] = {"line": effective_end, "offset": 2147483647}
                payload["threadContext"] = thread_context

            return self.client.post(endpoint, json_data=payload, scoped_to_project=bool(self.client.project))
        finally:
            self.client.project = original_project

    def reply_to_thread(
        self,
        pr_id: int,
        thread_id: int,
        comment_text: str,
        repository_id: Optional[str] = None,
        parent_comment_id: Optional[int] = None,
        status: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Posts a reply comment to a thread and optionally updates thread status.
        Auto-resolves repository and parent comment ID if omitted.
        """
        repo = repository_id or self.repository_id
        if not repo:
            pr = self.get_pull_request(pr_id, project=project)
            repo = pr.repository_id
            project = project or pr.project_name

        original_project = self.client.project
        if project:
            self.client.project = project

        try:
            p_id = parent_comment_id
            if p_id is None:
                try:
                    thread_info = self.client.get(
                        f"git/repositories/{repo}/pullrequests/{pr_id}/threads/{thread_id}",
                        scoped_to_project=bool(self.client.project),
                    )
                    comments = thread_info.get("comments", [])
                    p_id = comments[0].get("id", 1) if comments else 1
                except Exception:
                    p_id = 1

            endpoint = f"git/repositories/{repo}/pullrequests/{pr_id}/threads/{thread_id}/comments"
            payload = {"content": comment_text, "parentCommentId": p_id, "commentType": 1}
            res = self.client.post(endpoint, json_data=payload, scoped_to_project=bool(self.client.project))

            if status:
                try:
                    self.update_thread_status(
                        pr_id=pr_id,
                        thread_id=thread_id,
                        status=status,
                        repository_id=repo,
                        project=project,
                    )
                except Exception:
                    pass

            return res
        finally:
            self.client.project = original_project

    def set_vote(
        self,
        pr_id: int,
        vote: Any,
        reviewer_id: Optional[str] = None,
        repository_id: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submits a review decision/vote on the PR.
        """
        repo = repository_id or self.repository_id
        if not repo:
            pr = self.get_pull_request(pr_id, project=project)
            repo = pr.repository_id
            project = project or pr.project_name

        rev_id = reviewer_id or self.get_current_user_id()
        if not rev_id:
            raise AdoError("Cannot determine authenticated reviewer identity for voting.")

        if isinstance(vote, str):
            vote_int = VOTE_NAME_TO_INT.get(vote.strip().lower(), 10)
        else:
            vote_int = int(vote)

        endpoint = f"git/repositories/{repo}/pullrequests/{pr_id}/reviewers/{rev_id}"
        payload = {"vote": vote_int}

        original_project = self.client.project
        if project:
            self.client.project = project

        try:
            return self.client.put(endpoint, json_data=payload, scoped_to_project=bool(self.client.project))
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

