# Quick Start (5 Minutes)

## 1. Install

```bash
pip install pandas openpyxl requests
```

## 2. Get PAT Token

1. https://dev.azure.com → Profile → Personal Access Tokens → New Token
2. Scopes: ✓ Work Items (Read & Write), ✓ Project (Read)
3. Copy token

## 3. Configure

```bash
cp .env.example .env
```

Edit `.env`:
```
AZURE_ORG_URL=https://dev.azure.com/your_org
AZURE_PROJECT_NAME=YourProject
AZURE_PAT=your_token
EXCEL_FILE_PATH=src/data/your_file.xlsx
```

## 4. Prepare Excel

Required columns: Requirement ID, Story ID, Epic, Feature, Title, Description, Priority, Delivery Phase

Optional: Swimlane Step, Product Variation, Source Module

See `src/sample_stories.csv` for example.

## 5. Run

```bash
python src/ado_mcp_server.py
```

Results in `output/`:
- `ado_traceability_map.json`
- `traceability_report_*.csv`

## 6. Verify

Go to Azure DevOps → Search for your Epic

## Troubleshooting

| Issue | Fix |
|-------|-----|
| ModuleNotFoundError | `pip install pandas openpyxl requests` |
| 401 Unauthorized | Check PAT is correct and not expired |
| Project not found | Verify project name (case-sensitive) |

## Command Line Alternative

```bash
python src/ado_mcp_server.py stories.xlsx \
  --org-url https://dev.azure.com/myorg \
  --project MyProject \
  --pat token
```

---

More help: [SETUP.md](SETUP.md) | Config details: [ENV_SETUP.md](ENV_SETUP.md)
