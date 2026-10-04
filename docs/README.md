# Azure DevOps MCP Server

Bulk-import user stories from Excel to Azure DevOps with automatic traceability mapping.

## Features

- **Bulk Import** - 100+ stories from Excel to Azure DevOps
- **Traceability** - Requirement ID → Epic → Feature → Story mapping
- **Deduplication** - Reuse existing Epics/Features automatically
- **Audit Reports** - CSV/JSON reports for compliance
- **Retry Logic** - Automatic retry with exponential backoff

## Quick Start

```bash
pip install pandas openpyxl requests
cp .env.example .env
# Edit .env with your Azure DevOps credentials
python src/ado_mcp_server.py
```

Results in `output/`:
- `ado_traceability_map.json` - Full mapping
- `traceability_report_*.csv` - Audit trail

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
- **[SETUP.md](SETUP.md)** - Troubleshooting and advanced help
- **[ENV_SETUP.md](ENV_SETUP.md)** - Environment variable reference

## Requirements

- Python 3.8+
- Azure DevOps organization and project
- Personal Access Token (PAT)
- Excel file with proper columns

## Excel Columns

| Column | Required | Example |
|--------|----------|---------|
| Requirement ID | Yes | REQ-001 |
| Story ID | Yes | STORY-001 |
| Epic | Yes | Chat Interface |
| Feature | Yes | NLP Processing |
| Title | Yes | User can start conversation |
| Description | Yes | Implement endpoint |
| Priority | Yes | High |
| Delivery Phase | Yes | Phase 1 |

Optional: Swimlane Step, Product Variation, Source Module

## Sample Data

Test the tool with `src/data/sample_stories.csv` (28 example stories).

---

**Start here:** [QUICKSTART.md](QUICKSTART.md)
