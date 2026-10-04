# Quick Start Guide

Get up and running in 5 minutes.

## Step 1: Clone/Download Repository

```bash
cd your-project-directory
# Files should include: ado_mcp_server.py, config.py, .env.example, etc.
```

## Step 2: Install Python Dependencies

```bash
pip install pandas openpyxl requests
```

Verify installation:
```bash
python --version  # Should be 3.8+
pip list | grep pandas
```

## Step 3: Create Personal Access Token

1. Go to https://dev.azure.com
2. Click your profile (top right) → **Personal Access Tokens**
3. Click **New Token**
4. Fill in:
   - **Name:** ADO MCP Import
   - **Expiration:** 90 days
5. Under **Scopes**, enable:
   - ✓ Work Items (Read & Write)
   - ✓ Project and Team (Read)
6. Click **Create**
7. **Copy the token immediately** (won't be shown again)

## Step 4: Configure .env File

```bash
# Copy the template
cp .env.example .env
```

Edit `.env` with your values:

```
AZURE_ORG_URL=https://dev.azure.com/your_org_name
AZURE_PROJECT_NAME=your_project_name
AZURE_PAT=paste_your_token_here
EXCEL_FILE_PATH=sample_stories.csv
```

**Where to find these:**
- **ORG_URL**: Look at your Azure DevOps URL
  - Example: `https://dev.azure.com/mycompany`
- **PROJECT_NAME**: Your project name in Azure DevOps
  - Example: `MyProject`
- **PAT**: The token you just created
- **EXCEL_FILE**: Path to your Excel file (or use `sample_stories.csv`)

## Step 5: Prepare Your Excel File

Your Excel file needs these columns:
- `Requirement ID` - e.g., REQ-001
- `Story ID` - e.g., STORY-001
- `Epic` - Epic name
- `Feature` - Feature name
- `Title` - Story title
- `Description` - Full description
- `Priority` - High/Medium/Low
- `Delivery Phase` - Phase name

See `sample_stories.csv` for an example.

## Step 6: Run the Import

```bash
python ado_mcp_server.py
```

The script will:
1. Read configuration from `.env`
2. Parse your Excel file
3. Create/find Epics in Azure DevOps
4. Create/find Features under those Epics
5. Create Stories under those Features
6. Generate traceability mapping

## Step 7: Check Results

After successful import, you'll see:

```
============================================================
[2026-10-04 15:30:00 UTC] Import Complete
  Imported:  28
  Failed:    0
  Mapping:   ado_traceability_map.json
  Report:    traceability_report_20261004_153000.csv
============================================================
```

**Output files:**
- `ado_traceability_map.json` - Full mapping (JSON)
- `traceability_report_*.csv` - Audit trail (CSV)

## Step 8: Verify in Azure DevOps

1. Go to https://dev.azure.com/your_org/your_project
2. Navigate to **Work Items**
3. Search for your Epic name
4. Verify the hierarchy:
   - Epic
     - Feature
       - Stories

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **ModuleNotFoundError** | Run: `pip install pandas openpyxl requests` |
| **401 Unauthorized** | Verify PAT token is correct and hasn't expired |
| **Project not found** | Check project name (case-sensitive) |
| **File not found** | Verify Excel file path in `.env` |
| **Missing columns** | Excel columns must match exactly (case-sensitive) |

## Alternative: Command Line Arguments

Instead of `.env` file, you can pass arguments directly:

```bash
python ado_mcp_server.py stories.xlsx \
  --org-url https://dev.azure.com/myorg \
  --project MyProject \
  --pat your_token_here
```

## Using Sample Data

Test with the included sample file:

```bash
# Update .env
EXCEL_FILE_PATH=sample_stories.csv

# Run import
python ado_mcp_server.py
```

The sample file has 28 stories across 7 epics (imported in ~10 seconds).

## Next Steps

1. ✅ Review the traceability report: `traceability_report_*.csv`
2. ✅ Verify in Azure DevOps that all items were created
3. ✅ Query the mapping: See `ENV_SETUP.md` for Python API examples
4. ✅ Run again with your own data

## Need Help?

- **Environment variables:** See `ENV_SETUP.md`
- **Excel format:** See `sample_stories.csv`
- **Setup details:** See `SETUP.md`
- **Full documentation:** See `README.md`

---

**That's it!** You now have all your user stories in Azure DevOps with full traceability. 🎉
