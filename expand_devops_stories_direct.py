#!/usr/bin/env python3
"""
Expand DevOps stories using work item IDs from Azure DevOps directly.
No CSV or Custom field mapping needed - works with actual ADO work items.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import argparse
import base64

import requests

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))
from config import load_env_file, get_required_config
from mcp_client import MCPClient


# ============================================================================
# AZURE DEVOPS CLIENT
# ============================================================================

class AzureDevOpsClient:
    """Client for Azure DevOps REST API"""

    def __init__(self, org_url: str, project_name: str, pat: str):
        org_url = org_url.rstrip('/')
        if org_url.endswith(f"/{project_name}"):
            org_url = org_url[:-len(f"/{project_name}")]

        self.org_url = org_url
        self.project_name = project_name
        self.pat = pat
        self.base_url = f"{self.org_url}/{project_name}/_apis/wit/workitems"
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
                     query_params: Optional[Dict] = None, retries: int = 3) -> Dict:
        """Make HTTP request with retry logic"""
        params = {"api-version": "7.0"}
        params.update(query_params or {})
        headers = {"Content-Type": "application/json-patch+json" if method == "PATCH" else "application/json"}

        for attempt in range(retries):
            try:
                if method == "GET":
                    resp = self.session.get(url, params=params, headers=headers)
                elif method == "POST":
                    resp = self.session.post(url, json=data, params=params, headers=headers)
                elif method == "PATCH":
                    resp = self.session.patch(url, json=data, params=params, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                if resp.status_code >= 400:
                    try:
                        detail = resp.json().get("message", resp.text)
                    except ValueError:
                        detail = resp.text
                    if resp.status_code < 500 and resp.status_code != 429:
                        raise Exception(f"{resp.status_code}: {detail}")
                    raise Exception(f"Retryable error: {resp.status_code}")

                return resp.json() if resp.text else {}

            except Exception as e:
                if attempt == retries - 1:
                    raise
                wait_time = 2 ** attempt
                print(f"    Retry {attempt + 1}/{retries} after {wait_time}s")
                time.sleep(wait_time)

    def get_work_item(self, work_item_id: int) -> Dict:
        """Get work item details"""
        url = f"{self.base_url}/{work_item_id}"
        return self._make_request("GET", url, query_params={"$expand": "all"})

    def get_all_user_stories(self) -> List[Dict]:
        """Get all User Story work items from ADO"""
        try:
            url = f"{self.org_url}/{self.project_name}/_apis/wit/wiql"
            query = "SELECT [System.Id], [System.Title], [System.Description] FROM workitems WHERE [System.WorkItemType]='User Story' ORDER BY [System.Id]"

            result = self._make_request("POST", url, {"query": query},
                                       query_params={"api-version": "7.0"})

            work_item_ids = [wi["id"] for wi in result.get("workItems", [])]

            # Get full details for all work items
            stories = []
            for wi_id in work_item_ids:
                try:
                    wi = self.get_work_item(wi_id)
                    stories.append(wi)
                except Exception as e:
                    print(f"    Warning: Could not get details for work item {wi_id}: {e}")

            return stories

        except Exception as e:
            print(f"[ERROR] Failed to get work items: {e}")
            return []

    def update_work_item(self, work_item_id: int, expanded_data: Dict) -> Dict:
        """Update work item with expanded details

        Puts:
        - All description sections in System.Description
        - Acceptance Criteria in Microsoft.VSTS.Common.AcceptanceCriteria
        """
        # Build description with all sections
        full_description = self._build_full_description_v2(expanded_data)

        patch = [
            {
                "op": "add",
                "path": "/fields/System.Description",
                "value": full_description
            }
        ]

        # Add acceptance criteria to its dedicated field
        acceptance_criteria = expanded_data.get('acceptance_criteria', [])
        if acceptance_criteria:
            ac_text = "\n".join(acceptance_criteria) if isinstance(acceptance_criteria, list) else acceptance_criteria
            patch.append({
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
                "value": ac_text
            })

        url = f"{self.base_url}/{work_item_id}"
        return self._make_request("PATCH", url, patch, query_params={"api-version": "7.0"})

    @staticmethod
    def _build_full_description(description: str, assumptions: str, acceptance_criteria: str) -> str:
        """Build formatted description with all sections"""
        sections = []

        if description:
            sections.append(f"<h3>Detailed Description</h3>\n{description}\n")

        if assumptions:
            sections.append(f"<h3>Assumptions</h3>\n{assumptions}\n")

        if acceptance_criteria:
            sections.append(f"<h3>Acceptance Criteria</h3>\n{acceptance_criteria}\n")

        return "\n".join(sections)

    @staticmethod
    def _build_full_description_v2(expanded_data: Dict) -> str:
        """Build formatted description with all sections from new prompt"""
        sections = []

        # User Story (new)
        user_story = expanded_data.get('user_story', '').strip()
        if user_story:
            sections.append(f"<h3>User Story</h3>\n{user_story}\n")

        # Detailed Description
        description = expanded_data.get('expanded_description', '').strip()
        if description:
            sections.append(f"<h3>Detailed Description</h3>\n{description}\n")

        # Assumptions
        assumptions = expanded_data.get('assumptions', [])
        if assumptions:
            assumptions_text = "\n".join(assumptions) if isinstance(assumptions, list) else assumptions
            sections.append(f"<h3>Assumptions</h3>\n{assumptions_text}\n")

        # Dependencies (new)
        dependencies = expanded_data.get('dependencies', [])
        if dependencies:
            deps_text = "\n".join(dependencies) if isinstance(dependencies, list) else dependencies
            sections.append(f"<h3>Dependencies</h3>\n{deps_text}\n")

        # Story Quality (new)
        story_quality = expanded_data.get('story_quality', {})
        if story_quality:
            quality_notes = []
            if story_quality.get('is_broad'):
                quality_notes.append("[BROAD] Story is broad - consider splitting")
            if story_quality.get('can_be_split'):
                quality_notes.append("[SPLITTABLE] Story can be split into smaller stories")
            missing = story_quality.get('missing_information', [])
            if missing:
                quality_notes.append(f"[MISSING INFO] {', '.join(missing)}")

            if quality_notes:
                sections.append(f"<h3>Story Quality Notes</h3>\n" + "\n".join(quality_notes) + "\n")

        return "\n".join(sections)


# ============================================================================
# STORY EXPANDER WITH MCP
# ============================================================================

class StoryExpander:
    """Expand stories from Azure DevOps using MCP server"""

    def __init__(self, mcp_client: MCPClient, ado_client: AzureDevOpsClient):
        self.mcp = mcp_client
        self.ado = ado_client
        self.stories = []
        self.progress_file = "expansion_progress_direct.json"
        self.progress = self._load_progress()

    def load_stories_from_ado(self) -> List[Dict]:
        """Load all User Story work items from Azure DevOps"""
        print("[INFO] Loading stories from Azure DevOps...")
        self.stories = self.ado.get_all_user_stories()
        print(f"[OK] Loaded {len(self.stories)} stories from ADO\n")
        return self.stories

    def _load_progress(self) -> Dict:
        """Load expansion progress"""
        if Path(self.progress_file).exists():
            with open(self.progress_file) as f:
                return json.load(f)
        return {"expanded": [], "failed": [], "pending": []}

    def _save_progress(self):
        """Save expansion progress"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def filter_stories(self, epic: Optional[str] = None, feature: Optional[str] = None,
                      limit: int = 100, skip_with_description: bool = True) -> List[Dict]:
        """Filter stories by title/epic and skip those with descriptions

        Args:
            epic: Filter by epic name (searches in title)
            feature: Filter by feature name (searches in title)
            limit: Maximum stories to return
            skip_with_description: If True, skip stories that have descriptions
        """
        filtered = self.stories

        if epic:
            filtered = [s for s in filtered if epic.lower() in s.get('fields', {}).get('System.Title', '').lower()]

        if feature:
            filtered = [s for s in filtered if feature.lower() in s.get('fields', {}).get('System.Title', '').lower()]

        # Skip already processed stories
        story_id = str
        filtered = [s for s in filtered if str(s.get('id')) not in self.progress['expanded']]

        # Skip stories that already have descriptions
        if skip_with_description:
            print(f"\n  [INFO] Checking descriptions...")
            stories_without_desc = []
            skipped_count = 0

            for story in filtered:
                work_item_id = story.get('id')
                description = story.get('fields', {}).get('System.Description', '').strip()

                if not description:
                    stories_without_desc.append(story)
                else:
                    skipped_count += 1

            filtered = stories_without_desc
            if skipped_count > 0:
                print(f"  [OK] Skipped {skipped_count} stories with descriptions")

        return filtered[:limit]

    def expand_batch(self, stories: List[Dict], dry_run: bool = False) -> Dict:
        """Expand a batch of stories"""
        results = {"expanded": 0, "failed": 0, "errors": []}

        print(f"\n[EPIC] Expanding {len(stories)} stories...")
        print(f"{'='*70}")

        for idx, story in enumerate(stories, 1):
            work_item_id = story.get('id')
            title = story.get('fields', {}).get('System.Title', 'N/A')

            print(f"\n[{idx}/{len(stories)}] ID {work_item_id}: {title}")

            try:
                # Prepare story data for MCP
                story_data = {
                    'story_id': str(work_item_id),
                    'title': title,
                    'description': story.get('fields', {}).get('System.Description', ''),
                    'epic': '',  # Not available in ADO directly
                    'feature': '',  # Not available in ADO directly
                    'priority': story.get('fields', {}).get('Microsoft.VSTS.Common.Priority', 'Medium'),
                    'requirement_id': ''  # Not available without custom field
                }

                # Call MCP to expand
                print(f"  -> Calling MCP server...")
                expanded = self.mcp.expand_story(**story_data)
                print(f"  [OK] Generated expansion")

                if not dry_run:
                    print(f"  -> Updating ADO...")
                    self.ado.update_work_item(work_item_id, expanded)
                    print(f"  [OK] Updated in Azure DevOps")

                    # Track progress
                    self.progress['expanded'].append(str(work_item_id))
                    results["expanded"] += 1
                else:
                    print(f"  [DRY RUN] Would update work item")
                    self.progress['expanded'].append(str(work_item_id))
                    results["expanded"] += 1

                # Small delay between calls
                if idx < len(stories):
                    time.sleep(0.5)

            except Exception as e:
                print(f"  [ERROR] {e}")
                self.progress['failed'].append({
                    'work_item_id': str(work_item_id),
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
                results["failed"] += 1
                results["errors"].append(f"{work_item_id}: {e}")

        # Save progress
        self._save_progress()

        print(f"\n{'='*70}")
        print(f"Summary: {results['expanded']} expanded, {results['failed']} failed")

        return results

    def get_status(self) -> Dict:
        """Get expansion status"""
        return {
            "expanded": len(self.progress['expanded']),
            "failed": len(self.progress['failed']),
            "total_stories": len(self.stories),
            "remaining": len(self.stories) - len(self.progress['expanded']) - len(self.progress['failed'])
        }


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI entry point"""
    load_env_file()

    parser = argparse.ArgumentParser(
        description="Expand DevOps stories from Azure DevOps work items directly (no CSV needed)",
        epilog="""
Examples:
  python expand_devops_stories_direct.py --batch 1 --limit 100
  python expand_devops_stories_direct.py --limit 50 --dry-run
  python expand_devops_stories_direct.py --status
        """
    )

    parser.add_argument("--batch", type=int, help="Batch number for tracking")
    parser.add_argument("--limit", type=int, default=100, help="Number of stories to process (default: 100)")
    parser.add_argument("--dry-run", action="store_true", help="Don't update Azure DevOps")
    parser.add_argument("--status", action="store_true", help="Show expansion status and exit")
    parser.add_argument("--no-confirm", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--mcp-server", default="story_expansion_mcp.py",
                       help="Path to MCP server script")
    parser.add_argument("--skip-with-description", action="store_false", dest="skip_with_description",
                       help="Process ALL stories (including those with descriptions)")

    args = parser.parse_args()

    # Get API credentials
    try:
        ado_config = {
            "org_url": get_required_config("AZURE_ORG_URL"),
            "project_name": get_required_config("AZURE_PROJECT_NAME"),
            "pat": get_required_config("AZURE_PAT")
        }
    except ValueError as e:
        print(f"[ERROR] Missing configuration: {e}")
        sys.exit(1)

    # Initialize clients
    mcp = MCPClient(args.mcp_server)
    ado = AzureDevOpsClient(**ado_config)
    expander = StoryExpander(mcp, ado)

    # Load stories from ADO
    expander.load_stories_from_ado()

    # Show status if requested
    if args.status:
        status = expander.get_status()
        print("\n[STATUS] Expansion Status")
        print(f"{'='*50}")
        print(f"Expanded:  {status['expanded']}")
        print(f"Failed:    {status['failed']}")
        print(f"Remaining: {status['remaining']}")
        print(f"Total:     {status['total_stories']}")
        print(f"{'='*50}\n")
        return

    # Filter stories
    print(f"\n[SEARCH] Filtering stories from Azure DevOps...")
    if args.batch:
        print(f"  Batch: {args.batch}")
    if args.skip_with_description:
        print(f"  Mode: Skip stories WITH descriptions")
    else:
        print(f"  Mode: Process ALL stories")

    filtered = expander.filter_stories(limit=args.limit, skip_with_description=args.skip_with_description)

    if not filtered:
        print("[ERROR] No stories found matching filters")
        return

    print(f"[OK] Found {len(filtered)} stories to expand\n")

    if args.dry_run:
        print("[WARNING] DRY RUN MODE - Will not update Azure DevOps\n")

    # Confirm before proceeding
    if args.dry_run or args.no_confirm:
        print(f"Proceeding with {len(filtered)} stories...\n")
    else:
        try:
            response = input(f"Proceed with expanding {len(filtered)} stories? (yes/no): ").lower()
            if response != "yes":
                print("Cancelled.")
                return
        except EOFError:
            print(f"Proceeding with {len(filtered)} stories...\n")

    # Expand stories
    try:
        start_time = datetime.utcnow()
        results = expander.expand_batch(filtered, dry_run=args.dry_run)
        end_time = datetime.utcnow()

        # Print summary
        duration = (end_time - start_time).total_seconds()
        print(f"\n[SUCCESS] Batch Complete")
        print(f"  Duration: {duration:.1f}s")
        print(f"  Expanded: {results['expanded']}")
        print(f"  Failed: {results['failed']}")

        if results['errors']:
            print(f"\n[FAILED] Errors (first 10):")
            for error in results['errors'][:10]:
                print(f"  - {error}")

    finally:
        # Stop MCP server
        mcp.stop()


if __name__ == "__main__":
    main()
