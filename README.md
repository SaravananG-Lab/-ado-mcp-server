# Azure DevOps MCP Server

Bulk-import user stories from Excel to Azure DevOps with automatic traceability mapping.

## Features

- Bulk import 100+ stories from Excel
- Full Requirement ID → Epic → Feature → Story mapping
- Auto-deduplicate existing items
- CSV/JSON audit reports
- Automatic retry logic

## Quick Start

```bash
pip install pandas openpyxl requests
cp .env.example .env
# Edit .env with your Azure DevOps credentials
python src/ado_mcp_server.py
```

## Project Structure

```
docs/              - Documentation
src/               - Source code
├── sample_stories.csv    - Example data
└── data/          - Your input files
output/            - Generated reports (auto-created)
```

## Documentation

- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Setup guide (5 min)
- **[docs/SETUP.md](docs/SETUP.md)** - Troubleshooting
- **[docs/ENV_SETUP.md](docs/ENV_SETUP.md)** - Config reference

## Requirements

- Python 3.8+
- Azure DevOps organization
- Personal Access Token (PAT)
- Excel file with columns: Requirement ID, Story ID, Epic, Feature, Title, Description, Priority, Delivery Phase

## Output

After import:
- `output/ado_traceability_map.json` - Full mapping
- `output/traceability_report_*.csv` - Audit trail

## Security

- `.env` is git-ignored (keep credentials local)
- Never share your PAT token
- Rotate token if exposed

---

👉 **Start with [docs/QUICKSTART.md](docs/QUICKSTART.md)**
