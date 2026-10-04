# Setup & Troubleshooting

Start with [QUICKSTART.md](QUICKSTART.md) first.

## Detailed Troubleshooting

### Installation Issues

**ModuleNotFoundError: No module named 'pandas'**
```bash
pip install pandas openpyxl requests xlrd
python --version  # Verify 3.8+
```

### Authentication Issues

**401 Unauthorized**
- Verify PAT token is correct (no extra spaces)
- Check token hasn't expired (regenerate if needed)
- Ensure scopes: Work Items (Read & Write), Project (Read)

**Organization not found**
- Verify URL: `https://dev.azure.com/organization_name`
- Not `https://dev.azure.com/organization_name/`

### Excel Issues

**Missing columns error**
- Excel columns must match EXACTLY (case-sensitive)
- Required: Requirement ID, Story ID, Epic, Feature, Title, Description, Priority, Delivery Phase
- Optional: Swimlane Step, Product Variation, Source Module

**File encoding issues**
- Save Excel as `.csv` with UTF-8 or Windows-1252 encoding
- Or use `.xlsx` (Excel native format)

### Import Issues

**Network timeout**
- Automatic retry with exponential backoff (3 attempts)
- Check internet connection
- May be rate-limited by Azure DevOps

**Import hangs**
- Check your network connection
- Try smaller file first
- May hit ADO rate limits (wait and retry)

## Query Results After Import

```python
from src.config import get_ado_config
from src.ado_mcp_server import TraceabilityEngine

engine = TraceabilityEngine("output/ado_traceability_map.json")
entry = engine.get_entry("REQ-001")
print(f"Epic: {entry['epic']['name']}")
```

## Environment Variables Reference

See [ENV_SETUP.md](ENV_SETUP.md) for complete list.

## Need More Help?

1. Check [QUICKSTART.md](QUICKSTART.md) - basic setup
2. Check [ENV_SETUP.md](ENV_SETUP.md) - configuration
3. Run with `--help`: `python src/ado_mcp_server.py --help`
