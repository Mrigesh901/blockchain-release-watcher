"""
Jira integration service.
Creates and assigns Jira tickets for binary upgrade notifications.
"""
import json
import os
import base64
import requests
from typing import Dict, Any, Optional

from app.config import Config


class JiraService:
    """Service for creating Jira tickets for protocol upgrade notifications."""

    PRIORITY_MAP = {
        "CRITICAL": "Highest",
        "HIGH": "High",
        "MEDIUM": "Medium",
        "LOW": "Low",
    }

    def __init__(self):
        """Initialize Jira service using configuration."""
        self.base_url = Config.JIRA_BASE_URL.rstrip("/")
        self.project_key = Config.JIRA_PROJECT_KEY
        self.issue_type = Config.JIRA_ISSUE_TYPE
        self.enabled = bool(
            self.base_url
            and Config.JIRA_USER_EMAIL
            and Config.JIRA_API_TOKEN
            and self.project_key
        )

        if self.enabled:
            credentials = f"{Config.JIRA_USER_EMAIL}:{Config.JIRA_API_TOKEN}"
            encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
            self._headers = {
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

        # Load protocol → owner mapping
        self._owners: Dict[str, Dict[str, str]] = self._load_owners()

        # Cache: email → Jira accountId (avoid repeated API lookups)
        self._account_id_cache: Dict[str, Optional[str]] = {}

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _load_owners(self) -> Dict[str, Dict[str, str]]:
        """Load protocol owners from config/protocol_owners.json."""
        owners_path = os.path.join(
            os.path.dirname(__file__),   # app/services/
            "..", "..",                  # project root
            "config",
            "protocol_owners.json",
        )
        owners_path = os.path.normpath(owners_path)

        if not os.path.exists(owners_path):
            print(f"  [Jira] WARNING: protocol_owners.json not found at {owners_path}")
            return {}

        try:
            with open(owners_path, "r") as f:
                data = json.load(f)
            # Remove metadata key if present
            data.pop("_comment", None)
            return data
        except Exception as exc:
            print(f"  [Jira] ERROR loading protocol_owners.json: {exc}")
            return {}

    # ------------------------------------------------------------------
    # User lookup
    # ------------------------------------------------------------------

    def _get_account_id(self, email: str) -> Optional[str]:
        """
        Resolve a Jira accountId from an email address.

        Results are cached to minimise API calls.
        Returns None if the user cannot be found.
        """
        if email in self._account_id_cache:
            return self._account_id_cache[email]

        url = f"{self.base_url}/rest/api/3/user/search"
        try:
            response = requests.get(
                url,
                headers=self._headers,
                params={"query": email},
                timeout=10,
            )
            if response.status_code == 200:
                users = response.json()
                if users:
                    account_id = users[0]["accountId"]
                    self._account_id_cache[email] = account_id
                    return account_id
            print(
                f"  [Jira] Could not find Jira user for {email} "
                f"(status {response.status_code})"
            )
        except Exception as exc:
            print(f"  [Jira] Error looking up user {email}: {exc}")

        self._account_id_cache[email] = None
        return None

    # ------------------------------------------------------------------
    # Description builder (Atlassian Document Format v3)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_adf_description(
        repo_name: str,
        old_version: str,
        new_version: str,
        analysis: Dict[str, Any],
        repo_url: str,
        protocol_name: str,
    ) -> Dict[str, Any]:
        """Build an Atlassian Document Format description for the Jira issue."""

        severity = analysis.get("severity", "MEDIUM")
        mandatory = analysis.get("mandatory_upgrade", False)
        summary_text = analysis.get("summary", "No summary available.")
        reasoning_text = analysis.get("reasoning", "No reasoning provided.")

        def paragraph(*texts) -> Dict:
            return {
                "type": "paragraph",
                "content": [{"type": "text", "text": t} for t in texts],
            }

        def heading(level: int, text: str) -> Dict:
            return {
                "type": "heading",
                "attrs": {"level": level},
                "content": [{"type": "text", "text": text}],
            }

        def bullet_item(text: str) -> Dict:
            return {
                "type": "listItem",
                "content": [paragraph(text)],
            }

        content = [
            heading(2, f"Binary Upgrade Notification: {protocol_name}"),
            {
                "type": "table",
                "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
                "content": [
                    {
                        "type": "tableRow",
                        "content": [
                            {
                                "type": "tableHeader",
                                "content": [paragraph("Field")],
                            },
                            {
                                "type": "tableHeader",
                                "content": [paragraph("Value")],
                            },
                        ],
                    },
                    {
                        "type": "tableRow",
                        "content": [
                            {"type": "tableCell", "content": [paragraph("Repository")]},
                            {"type": "tableCell", "content": [paragraph(repo_name)]},
                        ],
                    },
                    {
                        "type": "tableRow",
                        "content": [
                            {"type": "tableCell", "content": [paragraph("Previous Version")]},
                            {"type": "tableCell", "content": [paragraph(str(old_version))]},
                        ],
                    },
                    {
                        "type": "tableRow",
                        "content": [
                            {"type": "tableCell", "content": [paragraph("New Version")]},
                            {"type": "tableCell", "content": [paragraph(str(new_version))]},
                        ],
                    },
                    {
                        "type": "tableRow",
                        "content": [
                            {"type": "tableCell", "content": [paragraph("Severity")]},
                            {"type": "tableCell", "content": [paragraph(severity)]},
                        ],
                    },
                    {
                        "type": "tableRow",
                        "content": [
                            {"type": "tableCell", "content": [paragraph("Mandatory Upgrade")]},
                            {"type": "tableCell", "content": [paragraph("YES" if mandatory else "NO")]},
                        ],
                    },
                ],
            },
            heading(3, "AI Analysis Summary"),
            paragraph(summary_text),
            heading(3, "Reasoning"),
            paragraph(reasoning_text),
            heading(3, "Action Items"),
            {
                "type": "bulletList",
                "content": [
                    bullet_item("Review the release notes and changelog"),
                    bullet_item("Test the new binary in a staging environment"),
                    bullet_item("Plan and execute upgrade in production"),
                    bullet_item(
                        "Verify consensus / network compatibility after upgrade"
                    ),
                ],
            },
        ]

        if repo_url:
            content.append(
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Repository: "},
                        {
                            "type": "text",
                            "text": repo_url,
                            "marks": [{"type": "link", "attrs": {"href": repo_url}}],
                        },
                    ],
                }
            )

        return {"version": 1, "type": "doc", "content": content}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_owner_info(self, repo_name: str) -> Optional[Dict[str, str]]:
        """Return owner info dict for a repo, or None if not configured."""
        # Try exact match first
        owner = self._owners.get(repo_name)
        if owner:
            return owner

        # Strip platform prefix (github:/gitlab:) and try again
        clean = repo_name
        for prefix in ("github:", "gitlab:"):
            if repo_name.startswith(prefix):
                clean = repo_name[len(prefix):]
                break
        return self._owners.get(clean)

    def create_upgrade_ticket(
        self,
        repo_name: str,
        old_version: str,
        new_version: str,
        analysis: Dict[str, Any],
        repo_url: str = "",
    ) -> Dict[str, Any]:
        """
        Create a Jira ticket for a detected binary upgrade.

        Args:
            repo_name: Repository name (owner/repo or platform:owner/repo).
            old_version: Previous version string.
            new_version: New version string.
            analysis: AI analysis dict (severity, summary, reasoning, mandatory_upgrade).
            repo_url: URL to the repository/release.

        Returns:
            Dict with keys: success (bool), issue_key (str|None), issue_url (str|None),
            assigned_to (str|None), error (str|None).
        """
        if not self.enabled:
            return {"success": False, "error": "Jira integration not configured"}

        severity = analysis.get("severity", "MEDIUM")
        mandatory = analysis.get("mandatory_upgrade", False)
        priority_name = self.PRIORITY_MAP.get(severity, "Medium")

        # Resolve owner info
        owner_info = self.get_owner_info(repo_name)
        protocol_name = (owner_info or {}).get("protocol_name", repo_name)

        # Build issue summary
        mandatory_flag = " [MANDATORY]" if mandatory else ""
        summary = (
            f"[{severity}]{mandatory_flag} Binary upgrade: {protocol_name} "
            f"{old_version} → {new_version}"
        )

        # Build payload
        payload: Dict[str, Any] = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": self._build_adf_description(
                    repo_name=repo_name,
                    old_version=old_version,
                    new_version=new_version,
                    analysis=analysis,
                    repo_url=repo_url,
                    protocol_name=protocol_name,
                ),
                "issuetype": {"name": self.issue_type},
                "priority": {"name": priority_name},
            }
        }

        # Resolve Jira assignee from owner email
        assigned_to: Optional[str] = None
        if owner_info and owner_info.get("owner_email"):
            owner_email = owner_info["owner_email"]
            account_id = self._get_account_id(owner_email)
            if account_id:
                payload["fields"]["assignee"] = {"accountId": account_id}
                assigned_to = owner_email
            else:
                print(
                    f"  [Jira] Assignee not found for {owner_email} — "
                    f"ticket will be unassigned"
                )

        # Create the issue
        try:
            response = requests.post(
                f"{self.base_url}/rest/api/3/issue",
                headers=self._headers,
                json=payload,
                timeout=15,
            )

            if response.status_code in (200, 201):
                data = response.json()
                issue_key = data.get("key")
                issue_url = f"{self.base_url}/browse/{issue_key}"
                print(f"  [Jira] ✓ Created issue {issue_key} — {issue_url}")
                return {
                    "success": True,
                    "issue_key": issue_key,
                    "issue_url": issue_url,
                    "assigned_to": assigned_to,
                    "error": None,
                }
            else:
                error_msg = (
                    f"Jira API error {response.status_code}: {response.text[:300]}"
                )
                print(f"  [Jira] ✗ {error_msg}")
                return {"success": False, "issue_key": None, "issue_url": None,
                        "assigned_to": None, "error": error_msg}

        except Exception as exc:
            error_msg = f"Jira request failed: {exc}"
            print(f"  [Jira] ✗ {error_msg}")
            return {"success": False, "issue_key": None, "issue_url": None,
                    "assigned_to": None, "error": error_msg}
