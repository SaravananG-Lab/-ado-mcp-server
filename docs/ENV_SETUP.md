# Environment Configuration Guide

## Using .env File

Instead of passing arguments on the command line, you can create a `.env` file with your configuration.

### 1. Copy Template

```bash
cp .env.example .env
```

### 2. Edit .env File

```
AZURE_ORG_URL=https://dev.azure.com/myorg
AZURE_PROJECT_NAME=MyProject
AZURE_PAT=your_personal_access_token_here
EXCEL_FILE_PATH=stories.csv
MAPPING_FILE_PATH=ado_traceability_map.json
```

### 3. Run Without Arguments

```bash
python ado_mcp_server.py
```

The script will automatically read from `.env` file.

## Configuration Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| AZURE_ORG_URL | Yes | Azure DevOps organization URL | https://dev.azure.com/myorg |
| AZURE_PROJECT_NAME | Yes | Project name | MyProject |
| AZURE_PAT | Yes | Personal Access Token | your_token_here |
| EXCEL_FILE_PATH | Yes | Path to Excel file | stories.csv |
| MAPPING_FILE_PATH | No | Output mapping file | ado_traceability_map.json |
| REPORT_FORMAT | No | Report format (csv/json) | csv |
| REPORT_OUTPUT_DIR | No | Report output directory | ./reports |
| LOG_LEVEL | No | Logging level | INFO |
| DEBUG | No | Debug mode (true/false) | false |

## Security Notes

⚠️ **IMPORTANT**: Never commit `.env` file to version control!

✓ Already in `.gitignore`: `.env` files are automatically excluded

✓ Safe to use: Store sensitive tokens only locally

## Using CLI Arguments (Override .env)

You can still use command-line arguments, which override `.env` values:

```bash
python ado_mcp_server.py stories.csv \
  --org-url https://dev.azure.com/myorg \
  --project MyProject \
  --pat YOUR_TOKEN
```

## Priority Order

1. Command-line arguments (highest priority)
2. Environment variables from `.env`
3. Defaults in code (lowest priority)

Example: If you set `EXCEL_FILE_PATH` in `.env` but also pass `stories.csv` as argument, the argument is used.
