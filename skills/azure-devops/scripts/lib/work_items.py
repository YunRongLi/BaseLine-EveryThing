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
class WorkItemComment:
    id: int
    author: str
    published_date: str
    text: str


@dataclass
class RelatedWorkItem:
    id: int
    relation_name: str
    title: str = ""
    work_item_type: str = ""
    state: str = ""
    web_url: str = ""


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
    comments: List[WorkItemComment] = field(default_factory=list)
    related_items: List[RelatedWorkItem] = field(default_factory=list)
    raw_fields: Dict[str, Any] = field(default_factory=dict)
    web_url: str = ""


class WorkItemService:
    """
    High-level service for interacting with Azure DevOps Work Items and attachments.
    """

    def __init__(self, client: AzureDevOpsClient):
        self.client = client

    def get_comments(self, work_item_id: int, top: int = 50) -> List[WorkItemComment]:
        """
        Retrieves discussion comments for a work item.
        """
        endpoint = f"wit/workitems/{work_item_id}/comments"
        params = {"api-version": "7.0-preview.3", "$top": top, "order": "asc"}
        try:
            data = self.client.get(endpoint, params=params)
        except Exception:
            return []

        raw_comments = data.get("comments", []) if isinstance(data, dict) else []
        result: List[WorkItemComment] = []
        for c in raw_comments:
            cid = c.get("id", 0)
            text = c.get("text", "")
            created_by = c.get("createdBy", {})
            author = (
                created_by.get("displayName")
                or created_by.get("uniqueName")
                or "Unknown"
            )
            created_date = c.get("createdDate", "")
            result.append(WorkItemComment(id=cid, author=author, published_date=created_date, text=text))
        return result

    def get_work_item(
        self,
        work_item_id: int,
        include_comments: bool = True,
        include_relations: bool = True,
    ) -> WorkItem:
        """
        Retrieves complete work item details including attachments, relations, and comments.
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

        # Parse relations to discover attached files and related work items
        attachments: List[WorkItemAttachment] = []
        related_refs: List[Dict[str, Any]] = []
        relations = data.get("relations", []) or []
        for rel in relations:
            rel_type = rel.get("rel", "")
            url = rel.get("url", "")
            attributes = rel.get("attributes", {})
            if rel_type == "AttachedFile":
                name = attributes.get("name", "attachment")
                attachments.append(WorkItemAttachment(url=url, name=name, attributes=attributes))
            elif "workItems" in url or "workitems" in url:
                target_id_str = url.rstrip("/").split("/")[-1]
                if target_id_str.isdigit():
                    rel_name = attributes.get("name") or rel_type.split(".")[-1]
                    related_refs.append({
                        "id": int(target_id_str),
                        "name": rel_name,
                        "url": url,
                    })

        # Batch resolve related work items metadata
        related_items: List[RelatedWorkItem] = []
        if include_relations and related_refs:
            ids_to_fetch = [r["id"] for r in related_refs]
            id_info_map: Dict[int, Dict[str, str]] = {}
            chunk_size = 50
            for i in range(0, len(ids_to_fetch), chunk_size):
                chunk = ids_to_fetch[i : i + chunk_size]
                ids_str = ",".join(str(wid) for wid in chunk)
                try:
                    res = self.client.get(
                        "wit/workitems",
                        params={
                            "ids": ids_str,
                            "fields": "System.Id,System.Title,System.WorkItemType,System.State",
                            "$expand": "none",
                        },
                        scoped_to_project=False,
                    )
                    items_data = res.get("value", []) if isinstance(res, dict) else []
                    for item_d in items_data:
                        wid = item_d.get("id")
                        f = item_d.get("fields", {})
                        w_url = item_d.get("_links", {}).get("html", {}).get("href", "")
                        id_info_map[wid] = {
                            "title": f.get("System.Title", f"Work Item #{wid}"),
                            "type": f.get("System.WorkItemType", "Unknown"),
                            "state": f.get("System.State", "Unknown"),
                            "url": w_url or f"{self.client.organization}/_workitems/edit/{wid}",
                        }
                except Exception:
                    pass

            for ref in related_refs:
                wid = ref["id"]
                info = id_info_map.get(wid, {})
                rtitle = info.get("title", f"Work Item #{wid}")
                rtype = info.get("type", "Unknown")
                rstate = info.get("state", "Unknown")
                rurl = info.get("url") or f"{self.client.organization}/_workitems/edit/{wid}"
                related_items.append(
                    RelatedWorkItem(
                        id=wid,
                        relation_name=ref["name"],
                        title=rtitle,
                        work_item_type=rtype,
                        state=rstate,
                        web_url=rurl,
                    )
                )

        comments = self.get_comments(work_item_id) if include_comments else []
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
            comments=comments,
            related_items=related_items,
            raw_fields=fields,
            web_url=web_url,
        )

    def list_my_work_items(
        self,
        project: Optional[str] = None,
        item_type: Optional[str] = None,
        top: int = 25,
    ) -> List[WorkItem]:
        """
        Queries active work items assigned to the authenticated user using WIQL.
        """
        conditions = [
            "[System.AssignedTo] = @Me",
            "[System.State] NOT IN ('Closed', 'Resolved', 'Cut', 'Completed', 'Done')",
        ]
        if item_type:
            sanitized_type = item_type.replace("'", "''")
            conditions.append(f"[System.WorkItemType] = '{sanitized_type}'")

        where_clause = " AND ".join(conditions)
        wiql = (
            f"SELECT [System.Id] FROM WorkItems "
            f"WHERE {where_clause} "
            f"ORDER BY [System.ChangedDate] DESC"
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

