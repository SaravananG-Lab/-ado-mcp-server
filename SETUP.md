# Setup Guide

## Prerequisites

- Python 3.8+
- Azure DevOps organization and project
- Personal Access Token (PAT)
- Excel file with user stories

## Installation

```bash
pip install pandas openpyxl requests
python --version  # Verify 3.8+
```

## Azure DevOps Configuration

### 1. Create Personal Access Token

1. Go to https://dev.azure.com
2. Click profile → Personal Access Tokens → New Token
3. Fill in:
   - Name: "ADO MCP Import"
   - Expiration: 90 days
4. Enable scopes:
   - ✓ Work Items: Read & Write
   - ✓ Project and Team: Read
5. Create and copy token (won't be shown again)

### 2. Get Organization URL

Format: `https://dev.azure.com/organization_name`

Example: `https://dev.azure.com/myorg`

### 3. Get Project Name

Find in Azure DevOps URL or project settings.

## Excel File Format

| Column | Required | Example |
|--------|----------|---------|
| Requirement ID | Yes | REQ-001 |
| Story ID | Yes | STORY-001 |
| Epic | Yes | Chat Interface |
| Feature | Yes | Conversational AI |
| Title | Yes | User can start conversation |
| Description | Yes | Implement conversation endpoint |
| Priority | Yes | High |
| Delivery Phase | Yes | Phase 1 |
| Swimlane Step | No | Input Processing |
| Product Variation | No | Standard |
| Source Module | No | AI Agent |

See `sample_stories.csv` for example.

## First Run

### Option A: Command Line (Recommended)

```bash
python ado_mcp_server.py sample_stories.csv \
  --org-url https://dev.azure.com/myorg \
  --project MyProject \
  --pat your_token_here
```

### Option B: Python Script

```python
from ado_mcp_server import BulkImporter

importer = BulkImporter(
    excel_file="sample_stories.csv",
    org_url="https://dev.azure.com/myorg",
    project_name="MyProject",
    pat="your_token_here"
)

result = importer.run()
print(f"Imported: {result['imported']}, Failed: {result['failed']}")
```

## Output Files

After successful import:

1. **ado_traceability_map.json** - Full mapping of requirements to work items
2. **traceability_report_*.csv** - Human-readable audit trail

## Verify in Azure DevOps

1. Go to your project
2. Navigate to Work Items
3. Search for the Epic/Feature names from your Excel file
4. Verify the story hierarchy and tags

## Troubleshooting

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError: pandas | Run: `pip install pandas openpyxl xlrd` |
| 401 Unauthorized | Verify PAT is correct (no extra spaces), check expiration, verify scopes |
| Project not found | Check exact project name (case-sensitive), verify org URL format |
| Missing columns | Excel columns must match exactly (case-sensitive) |
| Import is slow | Check network, may be rate-limited by ADO |

## Query Traceability

After import, query the mapping:

```python
from ado_mcp_server import TraceabilityEngine

engine = TraceabilityEngine("ado_traceability_map.json")
entry = engine.get_entry("REQ-001")
print(f"Epic: {entry['epic']['name']}")
print(f"Feature: {entry['feature']['name']}")
print(f"Stories: {len(entry['stories'])}")

# Generate custom report
engine.generate_csv_report("custom_report.csv")
```

## Next Steps

1. Verify data in Azure DevOps
2. Review traceability_report_*.csv
3. Integrate into CI/CD pipelines if needed
