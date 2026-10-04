#!/usr/bin/env python3
"""
Diagnostic tool to check Azure DevOps stories and custom fields.
Helps debug why stories are not being found.
"""

import sys
import base64
from pathlib import Path
from typing import Optional, Dict, List
import requests

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from config import load_env_file, get_required_config


class ADODiagnostics:
    """Diagnose Azure DevOps configuration"""

    def __init__(self, org_url: str, project_name: str, pat: str):
        self.org_url = org_url.rstrip('/')
        self.project_name = project_name
        self.pat = pat
        self.base_url = f"{self.org_url}/{project_name}/_apis/wit"
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create authenticated session"""
        session = requests.Session()
        encoded_pat = base64.b64encode(f":{self.pat}".encode()).decode()
        session.headers.update({
            "Authorization": f"Basic {encoded_pat}",
            "Accept": "application/json"
        })
        return session

    def _make_request(self, method: str, url: str, data: Optional[Dict] = None,
                     query_params: Optional[Dict] = None) -> Dict:
        """Make HTTP request"""
        params = {"api-version": "7.0"}
        params.update(query_params or {})

        if method == "GET":
            resp = self.session.get(url, params=params)
        elif method == "POST":
            resp = self.session.post(url, json=data, params=params)
        else:
            raise ValueError(f"Unsupported method: {method}")

        if resp.status_code >= 400:
            raise Exception(f"{resp.status_code}: {resp.text}")

        return resp.json() if resp.text else {}

    def check_work_items_exist(self) -> Dict:
        """Check if any User Story work items exist"""
        print("\n[1] Checking if work items exist...")

        try:
            url = f"{self.base_url}/wiql"
            query = "SELECT [System.Id], [System.Title] FROM workitems WHERE [System.WorkItemType]='User Story' ORDER BY [System.Id] DESC"

            result = self._make_request("POST", url, {"query": query})
            work_items = result.get("workItems", [])

            print(f"  Total User Story work items found: {len(work_items)}")

            if work_items:
                print(f"\n  First 10 work items:")
                for wi in work_items[:10]:
                    print(f"    - ID: {wi['id']}")
                return {"count": len(work_items), "items": work_items[:10], "success": True}
            else:
                print(f"  [WARNING] No User Story work items found!")
                return {"count": 0, "items": [], "success": False}

        except Exception as e:
            print(f"  [ERROR] Failed to query work items: {e}")
            return {"success": False, "error": str(e)}

    def check_custom_fields(self) -> Dict:
        """Check available custom fields"""
        print("\n[2] Checking custom fields in the project...")

        try:
            url = f"{self.base_url}/workitemtypes/User%20Story/fields"
            result = self._make_request("GET", url)

            fields = result.get("value", [])
            custom_fields = [f for f in fields if f["name"].startswith("Custom")]

            print(f"  Total custom fields: {len(custom_fields)}")

            if custom_fields:
                print(f"\n  Available custom fields:")
                for field in custom_fields:
                    print(f"    - {field['referenceName']}: {field.get('name', 'N/A')}")

                # Check if StoryID exists
                story_id_fields = [f for f in custom_fields if "story" in f['name'].lower() and "id" in f['name'].lower()]
                if story_id_fields:
                    print(f"\n  [OK] Found Story ID field(s):")
                    for f in story_id_fields:
                        print(f"    - Use: {f['referenceName']}")
                else:
                    print(f"\n  [WARNING] No 'Story ID' custom field found!")

                return {"fields": custom_fields, "success": True}
            else:
                print(f"  [WARNING] No custom fields found!")
                return {"fields": [], "success": False}

        except Exception as e:
            print(f"  [ERROR] Failed to get fields: {e}")
            return {"success": False, "error": str(e)}

    def find_story_by_id(self, story_id: str) -> Dict:
        """Try to find a specific story"""
        print(f"\n[3] Searching for story ID: {story_id}")

        try:
            url = f"{self.base_url}/wiql"

            # Try different field names
            field_names = [
                "[Custom.StoryID]",
                "[System.Title]",  # Fallback to title
            ]

            for field_name in field_names:
                try:
                    query = f"SELECT [System.Id], [System.Title] FROM workitems WHERE {field_name}='{story_id}'"
                    result = self._make_request("POST", url, {"query": query})

                    if result.get("workItems"):
                        print(f"  [OK] Found using {field_name}!")
                        for wi in result["workItems"]:
                            print(f"    - Work Item ID: {wi['id']}")
                        return {"found": True, "field_name": field_name, "items": result["workItems"]}
                except:
                    continue

            print(f"  [ERROR] Story not found with ID: {story_id}")
            return {"found": False, "story_id": story_id}

        except Exception as e:
            print(f"  [ERROR] Search failed: {e}")
            return {"success": False, "error": str(e)}

    def get_work_item_details(self, work_item_id: int) -> Dict:
        """Get detailed work item info"""
        print(f"\n[4] Getting details for work item ID: {work_item_id}")

        try:
            url = f"{self.base_url}/workitems/{work_item_id}"
            result = self._make_request("GET", url, query_params={"$expand": "all"})

            fields = result.get("fields", {})
            print(f"\n  Work Item Type: {fields.get('System.WorkItemType', 'N/A')}")
            print(f"  Title: {fields.get('System.Title', 'N/A')}")
            print(f"  Description: {fields.get('System.Description', '(empty)')[:100]}...")

            print(f"\n  Custom Fields:")
            for key, value in fields.items():
                if key.startswith("Custom"):
                    print(f"    - {key}: {value}")

            return {"success": True, "fields": fields}

        except Exception as e:
            print(f"  [ERROR] Failed to get work item: {e}")
            return {"success": False, "error": str(e)}


def main():
    """Main diagnostics"""
    print("=" * 70)
    print("Azure DevOps Story Diagnostics")
    print("=" * 70)

    load_env_file()

    try:
        org_url = get_required_config("AZURE_ORG_URL")
        project = get_required_config("AZURE_PROJECT_NAME")
        pat = get_required_config("AZURE_PAT")
    except ValueError as e:
        print(f"[ERROR] Missing config: {e}")
        return

    diag = ADODiagnostics(org_url, project, pat)

    # 1. Check work items exist
    wi_result = diag.check_work_items_exist()

    if not wi_result.get("success"):
        print("\n[WARNING] No work items found. You may need to:")
        print("  - Bulk import stories using expand_devops_stories_mcp.py first")
        print("  - Or create stories manually in Azure DevOps")
        return

    # 2. Check custom fields
    fields_result = diag.check_custom_fields()

    # 3. Find a specific story
    print("\nEnter a Story ID to search (e.g., CIP-PA-285):")
    story_id = input("Story ID: ").strip()
    if story_id:
        diag.find_story_by_id(story_id)

        # If found, get details
        if "items" in locals() and items:
            diag.get_work_item_details(items[0]["id"])

    print("\n" + "=" * 70)
    print("Diagnostics Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
