# Azure DevOps MCP Server

Bulk-import user stories from Excel to Azure DevOps with automatic traceability mapping.

## 📁 Project Structure

```
azure-devops-mcp-server/
├── docs/                    # Documentation
│   ├── README.md           # Feature overview
│   ├── QUICKSTART.md       # 5-minute setup guide (START HERE!)
│   ├── SETUP.md            # Detailed setup instructions
│   └── ENV_SETUP.md        # Environment variable reference
│
├── src/                     # Source code
│   ├── ado_mcp_server.py   # Core implementation
│   ├── mcp_ado_server.py   # MCP Protocol wrapper
│   ├── config.py           # Configuration loader
│   └── sample_stories.csv  # Example data
│
├── output/                  # Generated files (git-ignored)
│   ├── ado_traceability_map.json
│   └── traceability_report_*.csv
│
├── .env.example            # Configuration template
└── .gitignore              # Git ignore rules
```

## 🚀 Quick Start

**New here?** Start with the quickstart guide:

```bash
cat docs/QUICKSTART.md
```

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | **START HERE** - 8-step setup (5 minutes) |
| [docs/README.md](docs/README.md) | Features & overview |
| [docs/SETUP.md](docs/SETUP.md) | Detailed configuration |
| [docs/ENV_SETUP.md](docs/ENV_SETUP.md) | Environment variables |

## 💻 Installation

```bash
pip install pandas openpyxl requests
```

## ⚙️ Configuration

```bash
cp .env.example .env
# Edit .env with your Azure DevOps credentials
```

## ▶️ Run Import

```bash
python src/ado_mcp_server.py
```

Output files are generated in the `output/` folder:
- `ado_traceability_map.json` - Full mapping
- `traceability_report_*.csv` - Audit report

## ✨ Features

- **Bulk Import** - Import 100+ stories from Excel
- **Traceability** - Full Requirement ID → Epic → Feature → Story mapping
- **Deduplication** - Reuse existing items automatically
- **Audit Trail** - CSV/JSON reports for compliance
- **Error Resilience** - Automatic retry with exponential backoff

## 📋 Requirements

- Python 3.8+
- Azure DevOps organization and project
- Personal Access Token (PAT) with Work Items scope
- Excel file with proper columns

## ⚠️ Security

- ✅ `.env` is git-ignored - store credentials safely locally
- ✅ Never commit `.env` file
- ✅ Keep PAT token private
- ✅ Rotate token if accidentally exposed

## 📞 Need Help?

1. Check [docs/QUICKSTART.md](docs/QUICKSTART.md) for 5-minute setup
2. See [docs/SETUP.md](docs/SETUP.md) for troubleshooting
3. Review [docs/ENV_SETUP.md](docs/ENV_SETUP.md) for configuration

---

**Ready to get started?** See [docs/QUICKSTART.md](docs/QUICKSTART.md) 🚀
