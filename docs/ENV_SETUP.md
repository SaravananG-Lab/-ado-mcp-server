# Environment Configuration

## Setup .env File

```bash
cp .env.example .env
```

Edit `.env` with your values:

```
AZURE_ORG_URL=https://dev.azure.com/myorg
AZURE_PROJECT_NAME=MyProject
AZURE_PAT=your_token
EXCEL_FILE_PATH=src/data/stories.xlsx
MAPPING_FILE_PATH=output/ado_traceability_map.json
REPORT_FORMAT=csv
REPORT_OUTPUT_DIR=./output
```

Then run:
```bash
python src/ado_mcp_server.py
```

## Configuration Variables

| Variable | Required | Example |
|----------|----------|---------|
| AZURE_ORG_URL | Yes | https://dev.azure.com/myorg |
| AZURE_PROJECT_NAME | Yes | MyProject |
| AZURE_PAT | Yes | your_token_here |
| EXCEL_FILE_PATH | Yes | src/data/stories.xlsx |
| MAPPING_FILE_PATH | No | output/ado_traceability_map.json |
| REPORT_FORMAT | No | csv or json |
| REPORT_OUTPUT_DIR | No | ./output |
| LOG_LEVEL | No | INFO, DEBUG |
| DEBUG | No | true or false |

## Priority Order

1. Command-line arguments (highest)
2. .env file values
3. Defaults in code (lowest)

Example: CLI args override .env values

## Security

✅ `.env` is git-ignored (never committed)  
✅ Keep `.env` file private and local  
✅ Never share your PAT token  
✅ Rotate token if exposed

## Command Line Alternative

```bash
python src/ado_mcp_server.py stories.xlsx \
  --org-url https://dev.azure.com/myorg \
  --project MyProject \
  --pat token
```

---

Start with [QUICKSTART.md](QUICKSTART.md) | Help: [SETUP.md](SETUP.md)
