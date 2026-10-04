# Azure DevOps MCP Server

Bulk-import user stories from Excel to Azure DevOps with automatic Epic ↔ Feature ↔ Story traceability mapping.

## Features

- **Bulk Import**: Import 100+ user stories from Excel directly to Azure DevOps
- **Traceability**: Automatic mapping of Requirement ID → Epic → Feature → Story chain
- **Deduplication**: Reuse existing Epics/Features by name
- **Audit Reports**: CSV/JSON traceability reports for compliance
- **Error Resilience**: Automatic retry logic, partial failure handling

## Quick Start

### 1. Install

```bash
pip install pandas openpyxl requests
```

### 2. Prepare Excel

Required columns:
- `Requirement ID`, `Story ID`, `Epic`, `Feature`, `Title`, `Description`, `Priority`, `Delivery Phase`
- Optional: `Swimlane Step`, `Product Variation`, `Source Module`

See `sample_stories.csv` for format.

### 3. Get Azure DevOps Token

1. Go to https://dev.azure.com → Personal Access Tokens
2. Create token with scopes: `Work Items: Read & Write`, `Project and Team: Read`
3. Copy token

### 4. Run Import

```bash
python ado_mcp_server.py stories.xlsx \
  --org-url https://dev.azure.com/myorg \
  --project MyProject \
  --pat YOUR_TOKEN
```

**Output:**
- `ado_traceability_map.json` - Full mapping
- `traceability_report_*.csv` - Audit report

## Usage

### Command Line

```bash
python ado_mcp_server.py <file> --org-url <url> --project <name> --pat <token>
```

### Python API

```python
from ado_mcp_server import BulkImporter

importer = BulkImporter(
    excel_file="stories.xlsx",
    org_url="https://dev.azure.com/myorg",
    project_name="MyProject",
    pat="token"
)
result = importer.run()
```

## Traceability Output

### JSON Mapping
Maps each Requirement ID to its Epic, Feature, and Stories:
```json
{
  "REQ-001": {
    "epic": {"id": "12345", "name": "Chat Interface"},
    "feature": {"id": "12346", "name": "NLP Processing"},
    "stories": [{"id": "12347", "title": "Extract intent"}]
  }
}
```

### CSV Report
Human-readable audit trail with all relationships.

## Files

- `ado_mcp_server.py` - Core implementation (AzureDevOpsClient, TraceabilityEngine, BulkImporter)
- `mcp_ado_server.py` - MCP Protocol wrapper
- `sample_stories.csv` - Example data

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Token invalid | Verify token scopes: Work Items Read & Write |
| Project not found | Check project name (case-sensitive) |
| Missing columns | Excel columns must match exactly (case-sensitive) |
| Network timeout | Automatic retry with exponential backoff (3 attempts) |

## Performance

- **Speed**: 5-10 stories/second (network dependent)
- **120 stories**: ~15-30 seconds
- **Bottleneck**: ADO API rate limits, network latency

## Ready for production deployment.
