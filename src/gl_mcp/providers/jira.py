"""JIRA provider for MCP tools."""

import logging
from typing import Any

import httpx

from gl_mcp.config import get_settings
from gl_mcp.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class JiraProvider(BaseProvider):
    """Provider for JIRA integration tools."""

    name = "jira"
    required_role = "gl-admin"

    def __init__(self):
        super().__init__()
        self._client: httpx.AsyncClient | None = None
        self._base_url: str = ""
        self._auth: tuple[str, str] | None = None

    async def load_credentials(self) -> bool:
        """Load JIRA credentials from settings."""
        settings = get_settings()

        if not settings.jira_url or not settings.jira_username or not settings.jira_api_token:
            logger.warning("JIRA credentials not configured")
            return False

        self._base_url = settings.jira_url.rstrip("/")
        self._auth = (settings.jira_username, settings.jira_api_token)

        # Test connection
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._base_url}/rest/api/3/myself",
                    auth=self._auth,
                    timeout=10.0,
                )
                if response.status_code == 200:
                    user = response.json()
                    logger.info(f"JIRA connected as: {user.get('displayName', 'unknown')}")
                    return True
                else:
                    logger.warning(f"JIRA auth failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.exception(f"JIRA connection error: {e}")
            return False

    def register_tools(self) -> None:
        """Register JIRA tools."""
        self.register_tool(
            name="search_issues",
            description="Search JIRA issues using JQL query",
            input_schema={
                "type": "object",
                "properties": {
                    "jql": {
                        "type": "string",
                        "description": "JQL query string (e.g., 'project = GL AND status = \"To Do\"')",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 20)",
                        "default": 20,
                    },
                },
                "required": ["jql"],
            },
            handler=self._search_issues,
        )

        self.register_tool(
            name="get_issue",
            description="Get details of a specific JIRA issue",
            input_schema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Issue key (e.g., 'GL-123')",
                    },
                },
                "required": ["issue_key"],
            },
            handler=self._get_issue,
        )

        self.register_tool(
            name="create_issue",
            description="Create a new JIRA issue",
            input_schema={
                "type": "object",
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Project key (e.g., 'GL')",
                    },
                    "summary": {
                        "type": "string",
                        "description": "Issue summary/title",
                    },
                    "description": {
                        "type": "string",
                        "description": "Issue description (plain text)",
                    },
                    "issue_type": {
                        "type": "string",
                        "description": "Issue type (e.g., 'Task', 'Bug')",
                        "default": "Task",
                    },
                },
                "required": ["project", "summary"],
            },
            handler=self._create_issue,
        )

        self.register_tool(
            name="add_comment",
            description="Add a comment to a JIRA issue",
            input_schema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Issue key (e.g., 'GL-123')",
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment text",
                    },
                },
                "required": ["issue_key", "comment"],
            },
            handler=self._add_comment,
        )

        self.register_tool(
            name="transition_issue",
            description="Transition a JIRA issue to a new status",
            input_schema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "Issue key (e.g., 'GL-123')",
                    },
                    "transition_name": {
                        "type": "string",
                        "description": "Transition name (e.g., 'Done', 'In Progress')",
                    },
                },
                "required": ["issue_key", "transition_name"],
            },
            handler=self._transition_issue,
        )

    async def _request(
        self, method: str, endpoint: str, json_data: dict | None = None
    ) -> dict[str, Any]:
        """Make an authenticated request to JIRA API."""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=f"{self._base_url}{endpoint}",
                auth=self._auth,
                json=json_data,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json() if response.content else {}

    async def _search_issues(self, jql: str, max_results: int = 20) -> str:
        """Search JIRA issues."""
        result = await self._request(
            "POST",
            "/rest/api/3/search/jql",
            {"jql": jql, "maxResults": max_results, "fields": ["key", "summary", "status", "priority", "created"]},
        )

        issues = result.get("issues", [])
        if not issues:
            return "No issues found matching the query."

        lines = [f"Found {len(issues)} issues:\n"]
        for issue in issues:
            key = issue["key"]
            fields = issue["fields"]
            summary = fields.get("summary", "No summary")
            status = fields.get("status", {}).get("name", "Unknown")
            lines.append(f"- {key}: {summary} [{status}]")

        return "\n".join(lines)

    async def _get_issue(self, issue_key: str) -> str:
        """Get a specific JIRA issue."""
        result = await self._request("GET", f"/rest/api/3/issue/{issue_key}")

        fields = result.get("fields", {})
        summary = fields.get("summary", "No summary")
        status = fields.get("status", {}).get("name", "Unknown")
        priority = fields.get("priority", {}).get("name", "None")
        issue_type = fields.get("issuetype", {}).get("name", "Unknown")

        # Extract description text
        description = "No description"
        desc_content = fields.get("description")
        if desc_content and isinstance(desc_content, dict):
            description = self._extract_text_from_adf(desc_content)

        return f"""**{issue_key}: {summary}**

**Type:** {issue_type}
**Status:** {status}
**Priority:** {priority}

**Description:**
{description}
"""

    async def _create_issue(
        self,
        project: str,
        summary: str,
        description: str = "",
        issue_type: str = "Task",
    ) -> str:
        """Create a new JIRA issue."""
        # Build ADF description
        adf_description = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}] if description else [],
                }
            ],
        }

        result = await self._request(
            "POST",
            "/rest/api/3/issue",
            {
                "fields": {
                    "project": {"key": project},
                    "summary": summary,
                    "description": adf_description,
                    "issuetype": {"name": issue_type},
                }
            },
        )

        issue_key = result.get("key", "Unknown")
        return f"Created issue: {issue_key}"

    async def _add_comment(self, issue_key: str, comment: str) -> str:
        """Add a comment to a JIRA issue."""
        adf_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": comment}]}
            ],
        }

        await self._request(
            "POST",
            f"/rest/api/3/issue/{issue_key}/comment",
            {"body": adf_body},
        )

        return f"Added comment to {issue_key}"

    async def _transition_issue(self, issue_key: str, transition_name: str) -> str:
        """Transition a JIRA issue."""
        # Get available transitions
        result = await self._request("GET", f"/rest/api/3/issue/{issue_key}/transitions")

        transitions = result.get("transitions", [])
        transition_id = None

        for t in transitions:
            if t["name"].lower() == transition_name.lower():
                transition_id = t["id"]
                break

        if not transition_id:
            available = [t["name"] for t in transitions]
            return f"Transition '{transition_name}' not found. Available: {', '.join(available)}"

        await self._request(
            "POST",
            f"/rest/api/3/issue/{issue_key}/transitions",
            {"transition": {"id": transition_id}},
        )

        return f"Transitioned {issue_key} to '{transition_name}'"

    def _extract_text_from_adf(self, adf: dict) -> str:
        """Extract plain text from Atlassian Document Format."""
        texts = []

        def extract(node):
            if isinstance(node, dict):
                if node.get("type") == "text":
                    texts.append(node.get("text", ""))
                for child in node.get("content", []):
                    extract(child)
            elif isinstance(node, list):
                for item in node:
                    extract(item)

        extract(adf)
        return " ".join(texts) if texts else "No description"
