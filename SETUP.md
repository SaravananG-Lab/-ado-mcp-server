# Setup Guide - Azure DevOps MCP Server

## Prerequisites

- Python 3.8 or later
- Azure DevOps organization and project
- Personal Access Token (PAT) with appropriate permissions
- Excel file with user stories

## Installation

### 1. Install Python Dependencies

```bash
pip install pandas openpyxl requests
```

### 2. Verify Installation

```bash
python --version  # Should be 3.8+
python -c "import pandas; import openpyxl; import requests; print('All dependencies OK')"
```

### 3. Copy Scripts

Place these files in your project directory:
- `ado_mcp_server.py` - Core implementation
- `mcp_ado_server.py` - MCP protocol wrapper
- Your Excel file with stories

```bash
ls -la
# ado_mcp_server.py
# mcp_ado_server.py
# stories.xlsx
# (or sample_stories.csv)
```

## Azure DevOps Configuration

### Step 1: Create Personal Access Token

1. Go to Azure DevOps: https://dev.azure.com
2. Click your profile icon (top right) → Personal Access Tokens
3. Click "New Token"
4. Fill in details:
   - **Name**: "ADO MCP Import"
   - **Organization**: Select your organization
   - **Expiration**: 90 days (or as needed)
5. Click "Show all scopes"
6. Enable these scopes:
   - ✓ Work Items: Read & Write
   - ✓ Project and Team: Read

7. Click "Create"
8. **COPY THE TOKEN** (you won't see it again)
9. Store it securely (e.g., in environment variable or secure note)

### Step 2: Get Organization URL

Format: `https://dev.azure.com/{organization_name}`

Example: `https://dev.azure.com/myorg`

### Step 3: Get Project Name

Find your project name in Azure DevOps URL or project settings.

Example: `ATL-Chatbot` or `MyProject`

## Excel File Setup

### Required Columns

Your Excel file must have these columns (exact names, case-sensitive):

| Column Name | Description | Example |
|------------|-------------|---------|
| Requirement ID | Unique requirement identifier | REQ-001 |
| Story ID | Story identifier | STORY-001 |
| Epic | Epic name (will deduplicate) | Chat Interface |
| Feature | Feature name under epic | Conversational AI |
| Title | User story title | User can start a conversation |
| Description | Full description | Implement basic conversation endpoint |
| Priority | High/Medium/Low | High |
| Delivery Phase | Phase name | Phase 1 |
| Swimlane Step | (optional) Process step | Input Processing |
| Product Variation | (optional) Product variant | Standard |
| Source Module | (optional) Module name | AI Agent |

### Create from CSV

If you have a CSV file:

```bash
# Convert CSV to Excel
python -c "
import pandas as pd
df = pd.read_csv('sample_stories.csv')
df.to_excel('stories.xlsx', index=False)
print('Created stories.xlsx')
"
```

### Validate Excel

```bash
python ado_mcp_server.py stories.xlsx \
  --org-url https://dev.azure.com/myorg \
  --project MyProject \
  --pat dummy_token
```

This will fail with auth error but will validate the Excel structure first.

## First Run - Step by Step

### Option A: Command Line (Recommended)

```bash
# 1. Set environment variables (optional but secure)
export AZURE_ORG_URL="https://dev.azure.com/myorg"
export AZURE_PROJECT="MyProject"
export AZURE_PAT="your_token_here"

# 2. Validate Excel file
python ado_mcp_server.py sample_stories.csv \
  --org-url "$AZURE_ORG_URL" \
  --project "$AZURE_PROJECT" \
  --pat "$AZURE_PAT"
```

Or inline:

```bash
python ado_mcp_server.py sample_stories.csv \
  --org-url https://dev.azure.com/myorg \
  --project MyProject \
  --pat "your_token_here"
```

### Option B: Python Script

Create `run_import.py`:

```python
#!/usr/bin/env python3
import sys
from ado_mcp_server import BulkImporter

if __name__ == "__main__":
    importer = BulkImporter(
        excel_file="sample_stories.csv",
        org_url="https://dev.azure.com/myorg",
        project_name="MyProject",
        pat="your_token_here"
    )
    
    result = importer.run()
    
    print(f"\nImport Result:")
    print(f"  Status: {result['status']}")
    print(f"  Imported: {result['imported']}")
    print(f"  Failed: {result['failed']}")
    print(f"  Mapping: {result['mapping_file']}")
    print(f"  Report: {result['report_file']}")
    
    if result['errors']:
        print(f"\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")
```

Run:

```bash
python run_import.py
```

### Option C: MCP Server Mode

```bash
# Start MCP server
python mcp_ado_server.py
```

In another terminal, send requests:

```bash
# Create a test request
cat > test_request.json << 'EOF'
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "validate_excel",
    "arguments": {
      "file_path": "sample_stories.csv"
    }
  }
}
EOF

# Send to server
cat test_request.json | python mcp_ado_server.py
```

## Testing Checklist

- [ ] Python 3.8+ installed: `python --version`
- [ ] Dependencies installed: `pip list | grep pandas`
- [ ] Excel file exists: `ls sample_stories.csv`
- [ ] Excel validated: Check column names match requirements
- [ ] Azure DevOps accessible: Can you log into dev.azure.com?
- [ ] PAT created with correct scopes
- [ ] PAT copied correctly (no spaces/extra characters)
- [ ] Organization URL correct (with `/`)
- [ ] Project name correct (exact spelling)

## Run Import (Sample Data)

Using the provided `sample_stories.csv` (28 stories):

```bash
python ado_mcp_server.py sample_stories.csv \
  --org-url https://dev.azure.com/yourorg \
  --project YourProject \
  --pat your_pat_token_here
```

Expected output:

```
[2026-10-03 15:30:00 UTC] Starting import of 28 stories

📚 Epic: Chat Interface
  ✓ Created Epic ID 12345
  📋 Feature: Conversational AI
    ✓ Created Feature ID 12346
      ✓ Story 1/2: STORY-001 (ID 12347)
      ✓ Story 2/2: STORY-002 (ID 12348)
  📋 Feature: Natural Language Understanding
    ✓ Created Feature ID 12349
      ✓ Story 1/4: STORY-004 (ID 12350)
      ...

============================================================
[2026-10-03 15:30:15 UTC] Import Complete
  Imported:  28
  Failed:    0
  Mapping:   ado_traceability_map.json
  Report:    traceability_report_20261003_153015.csv
============================================================
```

## Outputs

After successful import:

### 1. Traceability Mapping (JSON)
File: `ado_traceability_map.json`

Contains every created item and its relationships:

```json
{
  "REQ-001": {
    "requirement_id": "REQ-001",
    "epic": {
      "id": "12345",
      "name": "Chat Interface",
      "url": "https://..."
    },
    "feature": {
      "id": "12346",
      "name": "Conversational AI",
      "url": "https://..."
    },
    "stories": [
      {
        "id": "12347",
        "title": "User can start a conversation",
        "url": "https://..."
      }
    ]
  }
}
```

### 2. Traceability Report (CSV)
File: `traceability_report_YYYYMMDD_HHMMSS.csv`

Human-readable audit trail:

```csv
Requirement ID,Epic ID,Epic Name,...,Story Title,...
REQ-001,12345,Chat Interface,...,User can start a conversation,...
REQ-002,12345,Chat Interface,...,User receives responses from AI,...
```

## Query Your Data

After import, query the traceability mapping:

```python
from ado_mcp_server import TraceabilityEngine

engine = TraceabilityEngine("ado_traceability_map.json")

# Get all entries
mapping = engine.get_all_entries()
print(f"Total requirements imported: {len(mapping)}")

# Get specific entry
entry = engine.get_entry("REQ-001")
print(f"REQ-001 maps to:")
print(f"  Epic: {entry['epic']['name']} (ID {entry['epic']['id']})")
print(f"  Feature: {entry['feature']['name']} (ID {entry['feature']['id']})")
print(f"  Stories: {len(entry['stories'])} story(ies)")
for story in entry['stories']:
    print(f"    - {story['title']} (ID {story['id']})")

# Generate report
csv_file = engine.generate_csv_report("custom_report.csv")
print(f"Report saved to: {csv_file}")
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pandas'"

**Solution:**
```bash
pip install pandas openpyxl
```

### Issue: "Request error: 401 Unauthorized"

**Solution:**
- Verify PAT is correct (no extra spaces)
- Check PAT hasn't expired
- Verify scopes include "Work Items: Read & Write"

### Issue: "Project not found"

**Solution:**
- Check project name (case-sensitive)
- Verify org URL: `https://dev.azure.com/organization_name`
- Not: `https://dev.azure.com/organization_name/`

### Issue: "Missing columns: ..."

**Solution:**
- Excel columns must match exactly (case-sensitive)
- Column names: `Requirement ID`, `Story ID`, `Epic`, `Feature`, `Title`, `Description`, `Priority`, `Delivery Phase`
- Optional: `Swimlane Step`, `Product Variation`, `Source Module`

### Issue: Import is very slow

**Solution:**
- Check internet connectivity
- May be hitting ADO rate limits (wait, then retry)
- ADO API is sometimes slower during peak hours

### Issue: "Mapping file not found"

**Solution:**
- Ensure you ran bulk import first (creates the mapping)
- Check file exists: `ls ado_traceability_map.json`
- Use correct mapping file path in commands

## Next Steps

1. **Verify in Azure DevOps**: Check created Epics/Features/Stories
2. **Review Traceability**: Open `traceability_report_*.csv`
3. **Integrate with CI/CD**: Use MCP server in automated pipelines
4. **Extend**: Add custom fields or tags as needed

## Support

For issues:
1. Check troubleshooting section above
2. Review console output for error messages
3. Verify Azure DevOps PAT permissions
4. Check Excel file column names and formats
