# Azure DevOps REST API Reference (Zero-PAT)

## Authentication Mechanism
Authentication is performed exclusively via Azure CLI OAuth 2.0 Bearer tokens.

- **Resource ID**: `499b84ac-1321-427f-aa17-267ca6975798`
- **CLI Command**: `az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --output json`
- **Headers**:
  ```http
  Authorization: Bearer <access_token>
  Content-Type: application/json
  Accept: application/json
  ```
- **Policy**: Personal Access Tokens (PAT) are strictly prohibited.

## Key REST API Endpoints

### 1. Connection & Identity
- **Endpoint**: `GET {org}/_apis/connectionData?api-version=7.0-preview`
- **Purpose**: Retrieves authenticated user identity, display name, and unique GUID (`authenticatedUser.id`).

### 2. Pull Requests
- **List PRs**: `GET {org}/{project}/_apis/git/pullrequests?searchCriteria.status=active&api-version=7.0`
- **List PRs by Creator**: `GET {org}/_apis/git/pullrequests?searchCriteria.creatorId={creator_id}&searchCriteria.status=active&api-version=7.0`
- **Get PR**: `GET {org}/_apis/git/pullrequests/{pr_id}?api-version=7.0`
- **Get PR Threads**: `GET {org}/{project}/_apis/git/repositories/{repositoryId}/pullrequests/{pr_id}/threads?api-version=7.0`
- **Post Reply to Thread**:
  - `POST {org}/{project}/_apis/git/repositories/{repositoryId}/pullrequests/{pr_id}/threads/{threadId}/comments?api-version=7.0`
  - Body:
    ```json
    {
      "content": "Addressed comment in commit ...",
      "parentCommentId": 1,
      "commentType": 1
    }
    ```

### 3. Work Items
- **Query Assigned to Me (WIQL)**:
  - `POST {org}/{project}/_apis/wit/wiql?api-version=7.0`
  - Body:
    ```json
    {
      "query": "SELECT [System.Id] FROM WorkItems WHERE [System.AssignedTo] = @Me AND [System.State] NOT IN ('Closed', 'Resolved', 'Cut', 'Completed', 'Done') ORDER BY [System.ChangedDate] DESC"
    }
    ```
- **Get Work Item Details**: `GET {org}/_apis/wit/workitems/{id}?$expand=all&api-version=7.0`
- **Add Work Item Comment**:
  - `POST {org}/_apis/wit/workitems/{id}/comments?api-version=7.0-preview.3`
  - Body:
    ```json
    {
      "text": "Triage analysis findings..."
    }
    ```
- **Download Attachment**:
  - Stream directly from attachment URL (`relation.rel == "AttachedFile"`), passing `Authorization: Bearer <token>` in headers.

