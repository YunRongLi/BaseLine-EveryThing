"""
Azure DevOps Work Items Service.
Handles fetching work item details, downloading attached logs, and submitting triage comments.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .client import AzureDevOpsClient
except ImportError:
    from client import AzureDevOpsClient


@dataclass
class WorkItemAttachment:
    url: str
    name: str
    attributes: Dict[str, Any] = field(default_factory=dict)

    @property
    def file_extension(self) -> str:
        return Path(self.name).suffix.lower()


@dataclass
class WorkItem:
    id: int
    title: str
    state: str
    work_item_type: str
    project: str = ""
    description: str = ""
    repro_steps: str = ""
    assigned_to: str = ""
    tags: List[str] = field(default_factory=list)
    attachments: List[WorkItemAttachment] = field(default_factory=list)
    raw_fields: Dict[str, Any] = field(default_factory=dict)
    web_url: str = ""


class WorkItemService:
    """
    High-level service for interacting with Azure DevOps Work Items and attachments.
    """

    def __init__(self, client: AzureDevOpsClient):
        self.client = client

    def get_work_item(self, work_item_id: int) -> WorkItem:
        """
        Retrieves complete work item details including attachments and relations.
        """
        endpoint = f"wit/workitems/{work_item_id}"
        data = self.client.get(endpoint, params={"$expand": "all"})

        fields = data.get("fields", {})
        title = fields.get("System.Title", f"Work Item #{work_item_id}")
        state = fields.get("System.State", "Unknown")
        work_item_type = fields.get("System.WorkItemType", "Unknown")
        project = fields.get("System.TeamProject", "")
        description = fields.get("System.Description", "")
        repro_steps = fields.get("Microsoft.VSTS.TCM.ReproSteps", "")

        assigned_raw = fields.get("System.AssignedTo", {})
        assigned_to = assigned_raw.get("displayName", "") if isinstance(assigned_raw, dict) else str(assigned_raw)

        tags_raw = fields.get("System.Tags", "")
        tags = [t.strip() for t in tags_raw.split(";") if t.strip()]

        # Parse relations to discover attached files
        attachments: List[WorkItemAttachment] = []
        relations = data.get("relations", [])
        for rel in relations:
            if rel.get("rel") == "AttachedFile":
                url = rel.get("url", "")
                attributes = rel.get("attributes", {})
                name = attributes.get("name", "attachment")
                attachments.append(WorkItemAttachment(url=url, name=name, attributes=attributes))

        web_url = data.get("_links", {}).get("html", {}).get("href", "")

        return WorkItem(
            id=work_item_id,
            title=title,
            state=state,
            work_item_type=work_item_type,
            project=project,
            description=description,
            repro_steps=repro_steps,
            assigned_to=assigned_to,
            tags=tags,
            attachments=attachments,
            raw_fields=fields,
            web_url=web_url,
        )

    def list_my_work_items(self, project: Optional[str] = None, top: int = 25) -> List[WorkItem]:
        """
        Queries active work items assigned to the authenticated user using WIQL.
        """
        wiql = (
            "SELECT [System.Id] FROM WorkItems "
            "WHERE [System.AssignedTo] = @Me "
            "AND [System.State] NOT IN ('Closed', 'Resolved', 'Cut', 'Completed', 'Done') "
            "ORDER BY [System.ChangedDate] DESC"
        )
        endpoint = "wit/wiql"
        original_project = self.client.project
        if project:
            self.client.project = project

        try:
            scoped = bool(self.client.project)
            result = self.client.post(endpoint, json_data={"query": wiql}, scoped_to_project=scoped)
        finally:
            self.client.project = original_project

        work_item_refs = result.get("workItems", [])[:top]
        items: List[WorkItem] = []
        for ref in work_item_refs:
            wid = ref.get("id")
            if wid:
                try:
                    items.append(self.get_work_item(wid))
                except Exception:
                    pass
        return items

    def download_attachments(
        self,
        work_item: WorkItem,
        destination_dir: Path,
        filter_extensions: Optional[List[str]] = None,
    ) -> List[Path]:
        """
        Downloads all or filtered attachments to destination_dir.
        Returns list of local file paths.
        """
        destination_dir.mkdir(parents=True, exist_ok=True)
        downloaded: List[Path] = []

        for att in work_item.attachments:
            if filter_extensions:
                ext = att.file_extension
                if ext not in filter_extensions:
                    continue

            safe_name = Path(att.name).name
            target_path = destination_dir / safe_name
            self.client.download_file(att.url, target_path)
            downloaded.append(target_path)

        return downloaded

    def download_attachment_url(self, url: str, destination_file: Path) -> Path:
        """
        Downloads a specific attachment by direct URL.
        """
        return self.client.download_file(url, destination_file)

    def add_comment(self, work_item_id: int, comment_text: str) -> Dict[str, Any]:
        """
        Posts a triage analysis or status comment to the work item.
        """
        endpoint = f"wit/workitems/{work_item_id}/comments"
        payload = {"text": comment_text}
        return self.client.post(endpoint, json_data=payload, params={"api-version": "7.0-preview.3"})

