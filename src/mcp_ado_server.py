#!/usr/bin/env python3
"""
MCP Server for Azure DevOps Bulk Import
Exposes tools for managing user story import with traceability
"""

import json
import sys
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import our implementation
from ado_mcp_server import (
    BulkImporter, TraceabilityEngine, ExcelImporter,
    AzureDevOpsClient, EpicData, FeatureData, StoryData
)


# ============================================================================
# MCP SERVER
# ============================================================================

class ADOMCPServer:
    """MCP Server for Azure DevOps operations"""

    def __init__(self):
        self.current_importer: Optional[BulkImporter] = None
        self.current_traceability: Optional[TraceabilityEngine] = None

    def get_tools(self) -> List[Dict]:
        """Return available tools"""
        return [
            {
                "name": "bulk_import_from_excel",
                "description": "Bulk import user stories from Excel to Azure DevOps with traceability",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to Excel file"
                        },
                        "org_url": {
                            "type": "string",
                            "description": "Azure DevOps organization URL (e.g., https://dev.azure.com/myorg)"
                        },
                        "project_name": {
                            "type": "string",
                            "description": "Project name"
                        },
                        "pat": {
                            "type": "string",
                            "description": "Personal Access Token for authentication"
                        },
                        "mapping_file": {
                            "type": "string",
                            "description": "Output file for traceability mapping (default: ado_traceability_map.json)"
                        }
                    },
                    "required": ["file_path", "org_url", "project_name", "pat"]
                }
            },
            {
                "name": "create_epic",
                "description": "Create an Epic in Azure DevOps",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Epic name"
                        },
                        "description": {
                            "type": "string",
                            "description": "Epic description"
                        },
                        "org_url": {
                            "type": "string",
                            "description": "Azure DevOps organization URL"
                        },
                        "project_name": {
                            "type": "string",
                            "description": "Project name"
                        },
                        "pat": {
                            "type": "string",
                            "description": "Personal Access Token"
                        }
                    },
                    "required": ["name", "description", "org_url", "project_name", "pat"]
                }
            },
            {
                "name": "create_feature",
                "description": "Create a Feature in Azure DevOps linked to an Epic",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Feature name"
                        },
                        "description": {
                            "type": "string",
                            "description": "Feature description"
                        },
                        "epic_id": {
                            "type": "integer",
                            "description": "Parent Epic ID"
                        },
                        "org_url": {
                            "type": "string",
                            "description": "Azure DevOps organization URL"
                        },
                        "project_name": {
                            "type": "string",
                            "description": "Project name"
                        },
                        "pat": {
                            "type": "string",
                            "description": "Personal Access Token"
                        }
                    },
                    "required": ["name", "description", "epic_id", "org_url", "project_name", "pat"]
                }
            },
            {
                "name": "create_story",
                "description": "Create a User Story in Azure DevOps linked to a Feature",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Story title"
                        },
                        "description": {
                            "type": "string",
                            "description": "Story description"
                        },
                        "feature_id": {
                            "type": "integer",
                            "description": "Parent Feature ID"
                        },
                        "requirement_id": {
                            "type": "string",
                            "description": "Source requirement ID"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["High", "Medium", "Low"],
                            "description": "Priority level"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags to apply"
                        },
                        "org_url": {
                            "type": "string",
                            "description": "Azure DevOps organization URL"
                        },
                        "project_name": {
                            "type": "string",
                            "description": "Project name"
                        },
                        "pat": {
                            "type": "string",
                            "description": "Personal Access Token"
                        }
                    },
                    "required": ["title", "description", "feature_id", "requirement_id",
                               "org_url", "project_name", "pat"]
                }
            },
            {
                "name": "get_traceability_map",
                "description": "Get the current traceability mapping (Requirement ID → Epic → Feature → Stories)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mapping_file": {
                            "type": "string",
                            "description": "Path to mapping file (default: ado_traceability_map.json)"
                        }
                    }
                }
            },
            {
                "name": "query_story_by_requirement",
                "description": "Query story chain for a specific requirement ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "requirement_id": {
                            "type": "string",
                            "description": "Requirement ID to look up"
                        },
                        "mapping_file": {
                            "type": "string",
                            "description": "Path to mapping file"
                        }
                    },
                    "required": ["requirement_id"]
                }
            },
            {
                "name": "generate_traceability_report",
                "description": "Generate a traceability audit report (CSV or JSON)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "output_file": {
                            "type": "string",
                            "description": "Output file path (auto-generated if not provided)"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["csv", "json"],
                            "description": "Report format"
                        },
                        "mapping_file": {
                            "type": "string",
                            "description": "Path to mapping file"
                        }
                    }
                }
            },
            {
                "name": "validate_excel",
                "description": "Validate Excel file structure and required columns",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to Excel file"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        ]

    # ========================================================================
    # TOOL IMPLEMENTATIONS
    # ========================================================================

    def bulk_import_from_excel(self, file_path: str, org_url: str, project_name: str,
                              pat: str, mapping_file: str = "ado_traceability_map.json") -> Dict:
        """Import stories from Excel"""
        try:
            if not Path(file_path).exists():
                return {"error": f"File not found: {file_path}"}

            importer = BulkImporter(file_path, org_url, project_name, pat)
            importer.traceability.mapping_file = mapping_file
            result = importer.run()

            return result
        except Exception as e:
            return {"error": str(e)}

    def create_epic(self, name: str, description: str, org_url: str,
                   project_name: str, pat: str) -> Dict:
        """Create epic"""
        try:
            client = AzureDevOpsClient(org_url, project_name, pat)

            # Check if exists
            existing = client.find_epic_by_name(name)
            if existing:
                return {
                    "id": existing["id"],
                    "name": existing["fields"]["System.Title"],
                    "url": existing.get("url", ""),
                    "status": "found"
                }

            # Create new
            result = client.create_epic(name, description)
            return {
                "id": result["id"],
                "name": result["fields"]["System.Title"],
                "url": result.get("url", ""),
                "status": "created"
            }
        except Exception as e:
            return {"error": str(e)}

    def create_feature(self, name: str, description: str, epic_id: int,
                      org_url: str, project_name: str, pat: str) -> Dict:
        """Create feature"""
        try:
            client = AzureDevOpsClient(org_url, project_name, pat)

            # Check if exists under epic
            existing = client.find_feature_by_name_under_epic(name, epic_id)
            if existing:
                return {
                    "id": existing["id"],
                    "name": existing["fields"]["System.Title"],
                    "url": existing.get("url", ""),
                    "parent_epic_id": epic_id,
                    "status": "found"
                }

            # Create new
            result = client.create_feature(name, description, epic_id)
            return {
                "id": result["id"],
                "name": result["fields"]["System.Title"],
                "url": result.get("url", ""),
                "parent_epic_id": epic_id,
                "status": "created"
            }
        except Exception as e:
            return {"error": str(e)}

    def create_story(self, title: str, description: str, feature_id: int,
                    requirement_id: str, org_url: str, project_name: str, pat: str,
                    priority: str = "Medium", tags: Optional[List[str]] = None) -> Dict:
        """Create user story"""
        try:
            client = AzureDevOpsClient(org_url, project_name, pat)
            result = client.create_user_story(title, description, feature_id, priority, tags)

            return {
                "id": result["id"],
                "title": result["fields"]["System.Title"],
                "url": result.get("url", ""),
                "requirement_id": requirement_id,
                "status": "created"
            }
        except Exception as e:
            return {"error": str(e)}

    def get_traceability_map(self, mapping_file: str = "ado_traceability_map.json") -> Dict:
        """Get traceability mapping"""
        try:
            if not Path(mapping_file).exists():
                return {"error": f"Mapping file not found: {mapping_file}"}

            engine = TraceabilityEngine(mapping_file)
            mapping = engine.get_all_entries()

            return {
                "mapping": mapping,
                "requirement_count": len(mapping),
                "epic_count": len(set(e["epic"]["id"] for e in mapping.values())),
                "feature_count": len(set(e["feature"]["id"] for e in mapping.values())),
                "story_count": sum(len(e["stories"]) for e in mapping.values())
            }
        except Exception as e:
            return {"error": str(e)}

    def query_story_by_requirement(self, requirement_id: str,
                                  mapping_file: str = "ado_traceability_map.json") -> Dict:
        """Query story chain for requirement"""
        try:
            engine = TraceabilityEngine(mapping_file)
            entry = engine.get_entry(requirement_id)

            if not entry:
                return {"error": f"Requirement not found: {requirement_id}"}

            return {
                "requirement_id": requirement_id,
                "epic": entry["epic"],
                "feature": entry["feature"],
                "stories": entry["stories"]
            }
        except Exception as e:
            return {"error": str(e)}

    def generate_traceability_report(self, output_file: Optional[str] = None,
                                    format: str = "csv",
                                    mapping_file: str = "ado_traceability_map.json") -> Dict:
        """Generate traceability report"""
        try:
            if not Path(mapping_file).exists():
                return {"error": f"Mapping file not found: {mapping_file}"}

            engine = TraceabilityEngine(mapping_file)

            if format == "json":
                report_file = engine.generate_json_report(output_file)
            else:
                report_file = engine.generate_csv_report(output_file)

            # Count rows
            entries = engine.get_all_entries()
            row_count = sum(len(e["stories"]) for e in entries.values())

            return {
                "file": report_file,
                "rows": row_count,
                "location": Path(report_file).absolute()
            }
        except Exception as e:
            return {"error": str(e)}

    def validate_excel(self, file_path: str) -> Dict:
        """Validate Excel file"""
        try:
            importer = ExcelImporter(file_path)

            return {
                "status": "valid",
                "row_count": len(importer.get_rows()),
                "unique_epics": len(importer.get_unique_epics()),
                "epics": importer.get_unique_epics(),
                "errors": []
            }
        except Exception as e:
            return {
                "status": "invalid",
                "errors": [str(e)]
            }

    def handle_tool_call(self, tool_name: str, tool_input: Dict) -> Dict:
        """Route tool calls"""
        method_name = tool_name.replace("-", "_")

        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(**tool_input)
        else:
            return {"error": f"Unknown tool: {tool_name}"}


# ============================================================================
# MCP PROTOCOL IMPLEMENTATION
# ============================================================================

def handle_request(request: Dict) -> Dict:
    """Handle MCP request"""
    server = ADOMCPServer()

    if request.get("jsonrpc") != "2.0":
        return {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}}

    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    try:
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "ado-mcp",
                        "version": "1.0.0"
                    }
                }
            }
            if request_id:
                response["id"] = request_id
            return response

        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "result": {
                    "tools": server.get_tools()
                }
            }
            if request_id:
                response["id"] = request_id
            return response

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_input = params.get("arguments", {})

            result = server.handle_tool_call(tool_name, tool_input)

            response = {
                "jsonrpc": "2.0",
                "result": result
            }
            if request_id:
                response["id"] = request_id
            return response

        else:
            response = {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }
            if request_id:
                response["id"] = request_id
            return response

    except Exception as e:
        response = {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)}
        }
        if request_id:
            response["id"] = request_id
        return response


def main():
    """MCP server entry point"""
    # For testing, read from stdin
    import sys
    line = sys.stdin.readline()
    while line:
        try:
            request = json.loads(line.strip())
            response = handle_request(request)
            print(json.dumps(response))
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}))

        line = sys.stdin.readline()


if __name__ == "__main__":
    main()
