#!/usr/bin/env python3
"""
Azure DevOps MCP Server
Bulk-import user stories with Epic ↔ Feature ↔ Story traceability mapping
"""

import json
import os
import sys
import time
import html
import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import base64
import requests
from urllib.parse import urljoin

# Spreadsheet column -> custom field reference name in the ADO process
CUSTOM_FIELD_MAP = {
    "Requirement ID": "Custom.RequirementID",
    "Story ID": "Custom.StoryID",
    "Delivery Phase": "Custom.DeliveryPhase",
    "Technical Requirement": "Custom.TechnicalRequirement",
}
HTML_FIELDS = {"Custom.TechnicalRequirement"}

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class EpicData:
    id: str
    name: str
    url: str

@dataclass
class FeatureData:
    id: str
    name: str
    url: str
    parent_epic_id: str

@dataclass
class StoryData:
    id: str
    title: str
    url: str
    requirement_id: str

@dataclass
class TraceabilityEntry:
    requirement_id: str
    epic: EpicData
    feature: FeatureData
    stories: List[StoryData]
    created_at: str
    import_batch_id: str


# ============================================================================
# AZURE DEVOPS API CLIENT
# ============================================================================

class AzureDevOpsClient:
    """Client for Azure DevOps REST API"""

    def __init__(self, org_url: str, project_name: str, pat: str):
        """
        Initialize ADO client

        Args:
            org_url: Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)
                     Can also include project name (will be extracted)
            project_name: Project name
            pat: Personal Access Token
        """
        org_url = org_url.rstrip('/')

        # Handle case where org_url includes project name
        # If org_url ends with the project name, remove it
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
        # Encode PAT as Basic auth
        encoded_pat = base64.b64encode(f":{self.pat}".encode()).decode()
        session.headers.update({
            "Authorization": f"Basic {encoded_pat}",
            "Accept": "application/json"
            # Note: Content-Type is set per-request in _make_request()
        })
        return session

    def _make_request(self, method: str, url: str, data: Optional[Any] = None,
                     query_params: Optional[Dict] = None, retries: int = 3,
                     json_patch: bool = False) -> Dict:
        """Make HTTP request with retry logic"""
        params = {"api-version": "7.0"}
        params.update(query_params or {})

        # Work item create/update bodies are JSON Patch documents and require this content type
        headers = {"Content-Type": "application/json-patch+json" if json_patch else "application/json"}

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
                    # Surface the ADO error message instead of a bare status code
                    try:
                        detail = resp.json().get("message", resp.text)
                    except ValueError:
                        detail = resp.text
                    err = requests.exceptions.HTTPError(
                        f"{resp.status_code} {resp.reason}: {detail}", response=resp)
                    # Client errors won't succeed on retry
                    if resp.status_code < 500 and resp.status_code != 429:
                        raise err
                    raise requests.exceptions.RetryError(str(err))

                return resp.json() if resp.text else {}

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout,
                    requests.exceptions.RetryError) as e:
                if attempt == retries - 1:
                    raise
                # Exponential backoff
                wait_time = 2 ** attempt
                print(f"  Retry {attempt + 1}/{retries} after {wait_time}s: {e}")
                time.sleep(wait_time)

    def find_epic_by_name(self, name: str) -> Optional[Dict]:
        """Find existing epic by name"""
        url = f"{self.org_url}/{self.project_name}/_apis/wit/wiql"
        # Escape single quotes in the name
        escaped_name = name.replace("'", "''")
        query = f"SELECT [System.Id] FROM workitems WHERE [System.WorkItemType]='Epic' AND [System.Title]='{escaped_name}'"

        try:
            result = self._make_request("POST", url, {"query": query}, query_params={"api-version": "7.0"})
            if result.get("workItems"):
                work_item_id = result["workItems"][0]["id"]
                return self.get_work_item(work_item_id)
            return None
        except Exception as e:
            print(f"  Warning: Failed to search for epic '{name}': {e}")
            return None

    def find_feature_by_name_under_epic(self, name: str, epic_id: str) -> Optional[Dict]:
        """Find existing feature by name under epic"""
        url = f"{self.org_url}/{self.project_name}/_apis/wit/wiql"
        # Escape single quotes in the name
        escaped_name = name.replace("'", "''")
        query = f"""SELECT [System.Id] FROM workitems
                   WHERE [System.WorkItemType]='Feature'
                   AND [System.Title]='{escaped_name}'"""

        try:
            result = self._make_request("POST", url, {"query": query}, query_params={"api-version": "7.0"})
            if result.get("workItems"):
                # Filter by epic parent
                for wi in result["workItems"]:
                    work_item = self.get_work_item(wi["id"])
                    if work_item and self._get_parent_id(work_item) == str(epic_id):
                        return work_item
            return None
        except Exception as e:
            print(f"  Warning: Failed to search for feature '{name}': {e}")
            return None

    def get_work_item(self, work_item_id: int) -> Dict:
        """Get work item details"""
        url = f"{self.base_url}/{work_item_id}"
        return self._make_request("GET", url, query_params={"$expand": "all"})

    def create_epic(self, name: str, description: str, tags: Optional[List[str]] = None) -> Dict:
        """Create epic"""
        return self._create_work_item("Epic", name, description, tags)

    def create_feature(self, name: str, description: str, epic_id: int,
                      tags: Optional[List[str]] = None) -> Dict:
        """Create feature linked to epic"""
        feature = self._create_work_item("Feature", name, description, tags)

        # Link to epic
        self._link_work_items(feature["id"], epic_id, "System.LinkTypes.Hierarchy-Reverse")

        return feature

    def create_user_story(self, title: str, description: str, feature_id: int,
                         priority: str = "Medium", tags: Optional[List[str]] = None,
                         work_item_type: str = "User Story", state: Optional[str] = None,
                         extra_fields: Optional[Dict] = None) -> Dict:
        """Create user story linked to feature"""
        fields = {
            "Microsoft.VSTS.Common.Priority": self._normalize_priority(priority),
            "System.State": state,
            **(extra_fields or {}),
        }

        story = self._create_work_item(work_item_type or "User Story", title, description, tags,
                                       custom_fields=fields)

        # Link to feature
        self._link_work_items(story["id"], feature_id, "System.LinkTypes.Hierarchy-Reverse")

        return story

    def update_user_story(self, work_item_id: int, title: str, description: str,
                          priority: str = "Medium", tags: Optional[List[str]] = None,
                          state: Optional[str] = None, extra_fields: Optional[Dict] = None) -> Dict:
        """Overwrite fields on an existing story"""
        fields = {
            "System.Title": title,
            "System.Description": description,
            "System.Tags": ";".join(tags) if tags else "",
            "Microsoft.VSTS.Common.Priority": self._normalize_priority(priority),
            "System.State": state,
            **(extra_fields or {}),
        }
        patch = [{"op": "add", "path": f"/fields/{field}", "value": value}
                 for field, value in fields.items() if value not in (None, "") or field == "System.Tags"]
        return self._make_request("PATCH", f"{self.base_url}/{work_item_id}", patch, json_patch=True)

    def get_children(self, work_item_id: int) -> List[Dict]:
        """Get child work items of a work item"""
        parent = self._make_request("GET", f"{self.base_url}/{work_item_id}",
                                    query_params={"$expand": "relations"})
        child_ids = [rel["url"].rsplit("/", 1)[-1] for rel in parent.get("relations") or []
                     if rel.get("rel") == "System.LinkTypes.Hierarchy-Forward"]
        children = []
        # The batch endpoint accepts up to 200 ids per call
        for i in range(0, len(child_ids), 200):
            batch = self._make_request("GET", f"{self.base_url}",
                                       query_params={"ids": ",".join(child_ids[i:i + 200])})
            children.extend(batch.get("value", []))
        return children

    def _create_work_item(self, work_item_type: str, title: str, description: str,
                         tags: Optional[List[str]] = None, custom_fields: Optional[Dict] = None) -> Dict:
        """Create work item (generic)"""
        # Azure DevOps API requires work item type in the URL path
        url = f"{self.base_url}/${work_item_type}"

        patch = [
            {"op": "add", "path": "/fields/System.Title", "value": title},
            {"op": "add", "path": "/fields/System.Description", "value": description},
        ]

        # Add tags
        if tags:
            patch.append({"op": "add", "path": "/fields/System.Tags", "value": ";".join(tags)})

        # Add custom fields
        if custom_fields:
            for field, value in custom_fields.items():
                if value and field not in ["System.Title", "System.Description", "System.Tags"]:
                    patch.append({"op": "add", "path": f"/fields/{field}", "value": value})

        result = self._make_request("POST", url, patch, json_patch=True)

        if "id" not in result:
            raise Exception(f"Failed to create {work_item_type}: {result}")

        return result

    def _link_work_items(self, source_id: int, target_id: int, link_type: str):
        """Create link between work items"""
        url = f"{self.base_url}/{source_id}"

        patch = [{
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": link_type,
                "url": f"{self.org_url}/_apis/wit/workItems/{target_id}"
            }
        }]

        try:
            self._make_request("PATCH", url, patch, json_patch=True)
        except Exception as e:
            print(f"  Warning: Failed to link work items {source_id} → {target_id}: {e}")

    def _get_parent_id(self, work_item: Dict) -> Optional[str]:
        """Extract parent ID from work item relations"""
        relations = work_item.get("relations", [])
        for rel in relations:
            if rel.get("rel") == "System.LinkTypes.Hierarchy-Reverse":
                url = rel.get("url", "")
                if "/workitems/" in url:
                    return url.split("/workitems/")[-1]
        return None

    def _normalize_priority(self, priority: str) -> int:
        """Normalize priority string to ADO priority number (ADO allows 1-4)"""
        mapping = {
            "Highest": 1,
            "High": 2,
            "Medium": 3,
            "Low": 4,
            "Lowest": 4,
            "P0": 1,
            "P1": 2,
            "P2": 3,
            "P3": 4,
        }
        return mapping.get(str(priority).strip(), 3)


# ============================================================================
# TRACEABILITY ENGINE
# ============================================================================

class TraceabilityEngine:
    """Manage traceability mapping"""

    def __init__(self, mapping_file: str = "ado_traceability_map.json"):
        self.mapping_file = mapping_file
        self.mapping: Dict[str, Dict] = self._load_mapping()
        self.import_batch_id = self._generate_batch_id()

    def _generate_batch_id(self) -> str:
        """Generate unique batch ID"""
        timestamp = datetime.utcnow().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]

    def _load_mapping(self) -> Dict:
        """Load existing mapping from file"""
        if Path(self.mapping_file).exists():
            with open(self.mapping_file) as f:
                return json.load(f)
        return {}

    def save_mapping(self):
        """Persist mapping to file"""
        with open(self.mapping_file, 'w') as f:
            json.dump(self.mapping, f, indent=2)

    def add_entry(self, requirement_id: str, epic: EpicData, feature: FeatureData,
                  stories: List[StoryData]):
        """Add traceability entry (one requirement can map to many stories)"""
        entry = self.mapping.get(requirement_id)
        if not entry or entry.get("import_batch_id") != self.import_batch_id:
            entry = {
                "requirement_id": requirement_id,
                "epic": asdict(epic),
                "feature": asdict(feature),
                "stories": [],
                "created_at": datetime.utcnow().isoformat(),
                "import_batch_id": self.import_batch_id
            }
            self.mapping[requirement_id] = entry
        entry["stories"].extend(asdict(s) for s in stories)

    def get_entry(self, requirement_id: str) -> Optional[Dict]:
        """Get traceability entry"""
        return self.mapping.get(requirement_id)

    def get_all_entries(self) -> Dict:
        """Get all entries"""
        return self.mapping

    def generate_csv_report(self, output_file: str = None) -> str:
        """Generate CSV audit report"""
        if output_file is None:
            output_file = f"traceability_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "Requirement ID", "Epic ID", "Epic Name", "Epic URL",
                "Feature ID", "Feature Name", "Feature URL",
                "Story ID", "Story Title", "Story URL", "Created At"
            ])

            # Rows
            for req_id, entry in self.mapping.items():
                epic = entry["epic"]
                feature = entry["feature"]

                for story in entry["stories"]:
                    writer.writerow([
                        req_id,
                        epic["id"], epic["name"], epic["url"],
                        feature["id"], feature["name"], feature["url"],
                        story["id"], story["title"], story["url"],
                        entry["created_at"]
                    ])

        return output_file

    def generate_json_report(self, output_file: str = None) -> str:
        """Generate JSON audit report"""
        if output_file is None:
            output_file = f"traceability_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_file, 'w') as f:
            json.dump(self.mapping, f, indent=2)

        return output_file


# ============================================================================
# EXCEL IMPORTER
# ============================================================================

class ExcelImporter:
    """Import user stories from Excel"""

    REQUIRED_COLUMNS = {
        "Requirement ID", "Story ID", "Epic", "Feature", "Title",
        "Priority", "Delivery Phase"
    }

    # Alternate spreadsheet headers -> canonical column names used by the importer
    COLUMN_ALIASES = {
        "story swimlane step / component": "Swimlane Step",
        "swimlane step / component": "Swimlane Step",
        "product variation(s)": "Product Variation",
        "work item type": "Work Item Type",
        "state": "State",
    }

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = self._read_excel()
        self.status = {}  # Track import status per row

    def _read_excel(self) -> List[Dict]:
        """Read Excel file with multiple format support"""
        try:
            import pandas as pd

            # Get file extension
            file_ext = Path(self.file_path).suffix.lower()
            print(f"  Reading file: {self.file_path} (type: {file_ext})")

            df = None
            error_log = []

            # Try multiple engines in order
            engines_to_try = []

            if file_ext in ['.xlsx', '.xlsm']:
                engines_to_try = ['openpyxl', 'xlrd']
            elif file_ext == '.xls':
                engines_to_try = ['xlrd']
            elif file_ext == '.csv':
                engines_to_try = ['csv']
            else:
                # Unknown extension, try all
                engines_to_try = ['openpyxl', 'xlrd', 'csv']

            # Try each engine
            for engine in engines_to_try:
                try:
                    if engine == 'csv':
                        print(f"  Trying CSV format...")
                        # Excel-saved CSVs are often Windows-1252, not UTF-8
                        for encoding in ('utf-8-sig', 'cp1252'):
                            try:
                                df = pd.read_csv(self.file_path, encoding=encoding)
                                break
                            except UnicodeDecodeError:
                                continue
                        if df is None:
                            raise Exception("unsupported text encoding")
                    else:
                        print(f"  Trying {engine} engine...")
                        df = pd.read_excel(self.file_path, engine=engine)

                    print(f"  ✓ Successfully read with {engine}")
                    break

                except Exception as e:
                    error_log.append(f"{engine}: {str(e)}")
                    continue

            if df is None:
                raise Exception(f"Could not read file with any engine. Errors: {'; '.join(error_log)}")

            # Normalize headers and drop empty spacer columns
            df.columns = [str(c).strip() for c in df.columns]
            df = df.loc[:, ~df.columns.str.startswith("Unnamed:")]
            df = df.rename(columns={c: self.COLUMN_ALIASES[c.lower()] for c in df.columns
                                    if c.lower() in self.COLUMN_ALIASES
                                    and self.COLUMN_ALIASES[c.lower()] not in df.columns})

            # Validate columns
            missing = self.REQUIRED_COLUMNS - set(df.columns)
            if missing:
                print(f"  Warning: Missing columns: {missing}")
                print(f"  Available columns: {list(df.columns)}")
                # Don't fail, just warn

            # Blank cells come back as NaN, which is not valid JSON for the ADO API
            df = df.fillna("")
            return df.to_dict('records')

        except ImportError as e:
            raise ImportError(f"Missing library: {e}. Install with: pip install pandas openpyxl xlrd")
        except Exception as e:
            raise Exception(f"Failed to read Excel: {e}")

    def get_rows(self) -> List[Dict]:
        """Get all rows"""
        return self.data

    def get_unique_epics(self) -> List[str]:
        """Get unique epic names"""
        return sorted(set(row["Epic"] for row in self.data if row.get("Epic")))

    def get_features_for_epic(self, epic_name: str) -> List[Tuple[str, str]]:
        """Get unique features for an epic (returns tuples of (feature_name, feature_description))"""
        features = {}
        for row in self.data:
            if row.get("Epic") == epic_name:
                feature_name = row.get("Feature", "")
                feature_desc = row.get("Description", "")
                if feature_name and feature_name not in features:
                    features[feature_name] = feature_desc

        return sorted(features.items())

    def get_stories_for_feature(self, epic_name: str, feature_name: str) -> List[Dict]:
        """Get stories for a feature"""
        return [
            row for row in self.data
            if row.get("Epic") == epic_name and row.get("Feature") == feature_name
        ]


# ============================================================================
# BULK IMPORTER
# ============================================================================

class BulkImporter:
    """Orchestrate bulk import"""

    def __init__(self, excel_file: str, org_url: str, project_name: str, pat: str):
        self.excel = ExcelImporter(excel_file)
        self.ado = AzureDevOpsClient(org_url, project_name, pat)
        self.traceability = TraceabilityEngine()
        self.results = {
            "imported": 0,
            "failed": 0,
            "errors": []
        }

    def run(self) -> Dict:
        """Execute bulk import"""
        print(f"[{self._timestamp()}] Starting import of {len(self.excel.get_rows())} stories")

        epics_cache = {}  # name -> epic_data
        features_cache = {}  # (epic_id, name) -> feature_data

        try:
            # Process each epic
            for epic_name in self.excel.get_unique_epics():
                print(f"\n📚 Epic: {epic_name}")

                # Create or find epic
                try:
                    existing_epic = self.ado.find_epic_by_name(epic_name)
                    if existing_epic:
                        epic = self._work_item_to_epic(existing_epic)
                        print(f"  ↳ Found existing Epic ID {epic.id}")
                    else:
                        epic_data = self.ado.create_epic(epic_name, f"Epic: {epic_name}")
                        epic = self._work_item_to_epic(epic_data)
                        print(f"  ✓ Created Epic ID {epic.id}")

                    epics_cache[epic_name] = epic
                except Exception as e:
                    self.results["failed"] += sum(1 for r in self.excel.get_rows() if r.get("Epic") == epic_name)
                    self.results["errors"].append(f"Failed to create epic '{epic_name}': {e}")
                    print(f"  ✗ Error: {e}")
                    continue

                # Process features under this epic
                features = self.excel.get_features_for_epic(epic_name)
                for feature_name, feature_desc in features:
                    print(f"  📋 Feature: {feature_name}")

                    try:
                        existing_feature = self.ado.find_feature_by_name_under_epic(feature_name, epic.id)
                        if existing_feature:
                            feature = self._work_item_to_feature(existing_feature)
                            print(f"    ↳ Found existing Feature ID {feature.id}")
                        else:
                            feature_data = self.ado.create_feature(
                                feature_name, feature_desc or f"Feature: {feature_name}", epic.id
                            )
                            feature = self._work_item_to_feature(feature_data)
                            print(f"    ✓ Created Feature ID {feature.id}")

                        features_cache[(epic.id, feature_name)] = feature
                    except Exception as e:
                        self.results["failed"] += len(self.excel.get_stories_for_feature(epic_name, feature_name))
                        self.results["errors"].append(f"Failed to create feature '{feature_name}': {e}")
                        print(f"    ✗ Error: {e}")
                        continue

                    # Existing children let a re-run update stories instead of duplicating them
                    try:
                        existing_children = self.ado.get_children(feature.id)
                    except Exception as e:
                        print(f"    Warning: could not list existing stories: {e}")
                        existing_children = []

                    # Process stories under this feature
                    stories = self.excel.get_stories_for_feature(epic_name, feature_name)
                    for idx, story_row in enumerate(stories, 1):
                        try:
                            story_fields = dict(
                                title=str(story_row.get("Title", "")).strip(),
                                description=self._build_description(story_row),
                                priority=story_row.get("Priority") or "Medium",
                                tags=self._extract_tags(story_row),
                                state=str(story_row.get("State", "")).strip() or None,
                                extra_fields=self._custom_fields(story_row),
                            )
                            existing = self._match_existing_story(existing_children, story_row)
                            if existing:
                                existing_children.remove(existing)
                                story_data = self.ado.update_user_story(existing["id"], **story_fields)
                                action = "Updated"
                            else:
                                story_data = self.ado.create_user_story(
                                    feature_id=feature.id,
                                    work_item_type=str(story_row.get("Work Item Type", "")).strip() or "User Story",
                                    **story_fields
                                )
                                action = "Created"

                            story = StoryData(
                                id=str(story_data["id"]),
                                title=story_data["fields"]["System.Title"],
                                url=story_data["url"],
                                requirement_id=story_row.get("Requirement ID", "")
                            )

                            # Add to traceability
                            self.traceability.add_entry(
                                story_row.get("Requirement ID", ""),
                                epic, feature, [story]
                            )

                            self.results["imported"] += 1
                            print(f"      ✓ Story {idx}/{len(stories)}: {story_row.get('Story ID')} ({action} ID {story.id})")

                        except Exception as e:
                            self.results["failed"] += 1
                            self.results["errors"].append(
                                f"Story '{story_row.get('Story ID')}': {e}"
                            )
                            print(f"      ✗ Story {idx}/{len(stories)}: {e}")

            # Save traceability mapping
            self.traceability.save_mapping()
            mapping_file = self.traceability.mapping_file

            # Generate report
            report_file = self.traceability.generate_csv_report()

            print(f"\n{'='*60}")
            print(f"[{self._timestamp()}] Import Complete")
            print(f"  Imported:  {self.results['imported']}")
            print(f"  Failed:    {self.results['failed']}")
            print(f"  Mapping:   {mapping_file}")
            print(f"  Report:    {report_file}")
            print(f"{'='*60}\n")

            return {
                "status": "success" if self.results["failed"] == 0 else "partial",
                "imported": self.results["imported"],
                "failed": self.results["failed"],
                "mapping_file": mapping_file,
                "report_file": report_file,
                "errors": self.results["errors"]
            }

        except Exception as e:
            print(f"✗ Fatal error: {e}")
            return {
                "status": "failed",
                "imported": self.results["imported"],
                "failed": self.results["failed"],
                "mapping_file": None,
                "report_file": None,
                "errors": self.results["errors"] + [str(e)]
            }

    def _extract_tags(self, row: Dict) -> List[str]:
        """Extract tags from row (multi-value cells become one tag per value)"""
        def split(value, sep):
            return [v.strip() for v in str(value).split(sep) if v.strip()]

        tags = []
        for step in split(row.get("Swimlane Step", ""), ";"):
            tags.append(f"Swimlane:{step}")
        for product in split(row.get("Product Variation", ""), ","):
            tags.append(f"Product:{product}")
        if row.get("Source Module"):
            tags.append(f"Module:{str(row['Source Module']).strip()}")
        # ';' is ADO's tag separator, so it cannot appear inside a tag
        return list(dict.fromkeys(t.replace(";", ",") for t in tags))

    @staticmethod
    def _to_html(value) -> str:
        return html.escape(str(value).strip()).replace("\n", "<br>")

    def _build_description(self, row: Dict) -> str:
        """Build HTML description"""
        return self._to_html(row.get("Description", ""))

    def _custom_fields(self, row: Dict) -> Dict:
        """Map spreadsheet columns to the project's custom ADO fields"""
        fields = {}
        for column, field in CUSTOM_FIELD_MAP.items():
            value = str(row.get(column, "")).strip()
            if value:
                fields[field] = self._to_html(value) if field in HTML_FIELDS else value
        return fields

    @staticmethod
    def _match_existing_story(children: List[Dict], row: Dict) -> Optional[Dict]:
        """Find a story already under the feature by Story ID, else by exact title"""
        story_id = str(row.get("Story ID", "")).strip()
        title = str(row.get("Title", "")).strip()
        for child in children:
            if story_id and str(child["fields"].get(CUSTOM_FIELD_MAP["Story ID"], "")).strip() == story_id:
                return child
        for child in children:
            if child["fields"].get("System.Title", "").strip() == title:
                return child
        return None

    def _work_item_to_epic(self, work_item: Dict) -> EpicData:
        """Convert ADO work item to EpicData"""
        return EpicData(
            id=str(work_item["id"]),
            name=work_item["fields"]["System.Title"],
            url=work_item.get("url", "")
        )

    def _work_item_to_feature(self, work_item: Dict) -> FeatureData:
        """Convert ADO work item to FeatureData"""
        parent_id = self._get_parent_id(work_item)
        return FeatureData(
            id=str(work_item["id"]),
            name=work_item["fields"]["System.Title"],
            url=work_item.get("url", ""),
            parent_epic_id=parent_id or ""
        )

    def _get_parent_id(self, work_item: Dict) -> Optional[str]:
        """Extract parent ID"""
        relations = work_item.get("relations", [])
        for rel in relations:
            if rel.get("rel") == "System.LinkTypes.Hierarchy-Reverse":
                url = rel.get("url", "")
                if "/workitems/" in url:
                    return url.split("/workitems/")[-1]
        return None

    @staticmethod
    def _timestamp() -> str:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI entry point"""
    import argparse
    from config import load_env_file, get_config

    # Load from .env file if it exists
    load_env_file()

    parser = argparse.ArgumentParser(
        description="Bulk import user stories from Excel to Azure DevOps",
        epilog="""
Examples:
  python ado_mcp_server.py stories.csv --org-url https://dev.azure.com/myorg --project MyProject --pat <PAT>
  python ado_mcp_server.py --env  (read from .env file)

Note: Arguments override .env file values.
        """
    )
    parser.add_argument("excel_file", nargs="?", help="Path to Excel file (or use EXCEL_FILE_PATH in .env)")
    parser.add_argument("--org-url", help="Azure DevOps org URL (or use AZURE_ORG_URL in .env)")
    parser.add_argument("--project", help="Project name (or use AZURE_PROJECT_NAME in .env)")
    parser.add_argument("--pat", help="Personal Access Token (or use AZURE_PAT in .env)")
    parser.add_argument("--mapping-file", default="ado_traceability_map.json",
                       help="Output mapping file")
    parser.add_argument("--env", action="store_true", help="Use .env file for all configuration")

    args = parser.parse_args()

    # Get values from args or .env
    excel_file = args.excel_file or get_config("EXCEL_FILE_PATH")
    org_url = args.org_url or get_config("AZURE_ORG_URL")
    project = args.project or get_config("AZURE_PROJECT_NAME")
    pat = args.pat or get_config("AZURE_PAT")

    if not all([excel_file, org_url, project, pat]):
        parser.error("Missing required arguments. Provide via CLI args or .env file (see .env.example)")

    # Run import
    importer = BulkImporter(
        excel_file,
        org_url,
        project,
        pat
    )

    result = importer.run()

    # Print result
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
