# Azure DevOps Story Expansion Tool

Automatically expand Azure DevOps User Story work items with detailed descriptions, assumptions, and acceptance criteria using Claude AI via MCP.

---

## ✨ Features

✅ **Reads directly from Azure DevOps** - No CSV or Custom field mapping needed  
✅ **Smart filtering** - Only expands stories without descriptions (by default)  
✅ **MCP-powered** - Uses Claude through MCP server (no API costs)  
✅ **Organized output** - Puts descriptions in separate ADO fields  
✅ **Resumable** - Tracks progress and can retry failed stories  
✅ **Batch processing** - Process 100+ stories per batch  

---

## 🚀 Quick Start (3 Steps)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Azure DevOps
Edit `.env` with your credentials:
```
AZURE_ORG_URL=https://dev.azure.com/YourOrg
AZURE_PROJECT_NAME=YourProject
AZURE_PAT=your_personal_access_token
```

### 3. Run Expansion
```bash
# Test with 5 stories (dry run)
python expand_devops_stories_direct.py --limit 5 --dry-run --no-confirm

# Expand first 100 stories
python expand_devops_stories_direct.py --batch 1 --limit 100 --no-confirm
```

---

## 📁 Project Files

```
expand_devops_stories_direct.py    ← Main expansion script
story_expansion_mcp.py             ← MCP server
mcp_client.py                      ← MCP client library
check_ado_stories.py               ← Diagnostic tool
.env                               ← Configuration
requirements.txt                   ← Dependencies
expansion_progress_direct.json     ← Progress tracking (auto-generated)
```

---

## 📋 How It Works

```
Azure DevOps Work Items (49 total)
         ↓
Load all User Stories
         ↓
Filter: Skip stories WITH descriptions (by default)
         ↓
For each story: Claude AI generates:
  - Detailed Description (2-3 paragraphs)
  - Assumptions (5-8 bullets)
  - Acceptance Criteria (8-12 items)
         ↓
Update Azure DevOps:
  System.Description ← Description + Assumptions
  Microsoft.VSTS.Common.AcceptanceCriteria ← AC
         ↓
Track in: expansion_progress_direct.json
```

---

## 💻 Command Reference

### Expand Stories
```bash
# Expand 100 stories without descriptions
python expand_devops_stories_direct.py --batch 1 --limit 100 --no-confirm

# Expand next batch
python expand_devops_stories_direct.py --batch 2 --limit 100 --no-confirm
```

### Testing & Diagnostics
```bash
# Test without updating
python expand_devops_stories_direct.py --limit 10 --dry-run --no-confirm

# Check progress
python expand_devops_stories_direct.py --status

# Diagnose issues
python check_ado_stories.py
```

### Expand All Stories (Including those with descriptions)
```bash
# Overwrites existing descriptions
python expand_devops_stories_direct.py --limit 100 --skip-with-description --no-confirm
```

---

## 📊 Processing Your Stories

**Example with 49 stories:**

**Batch 1 (Smart Filter):**
```bash
python expand_devops_stories_direct.py --batch 1 --limit 100 --no-confirm
```
Result: Expands 16 stories (33 skipped - already have descriptions)

**Batch 2 (All Stories):**
```bash
python expand_devops_stories_direct.py --batch 2 --limit 100 --skip-with-description --no-confirm
```
Result: Expands remaining 33 stories

---

## ⚙️ Options

```
--batch N                    Batch number for tracking
--limit N                    Stories to process (default: 100)
--dry-run                    Generate only, don't update ADO
--no-confirm                 Skip confirmation prompt
--skip-with-description      Process ALL stories (even with existing descriptions)
--status                     Show progress and exit
--mcp-server PATH            Path to MCP server script
-h, --help                   Show help
```

---

## 📈 Output Format

Each expanded story gets:

**System.Description Field:**
```
<h3>Detailed Description</h3>
The platform requires implementation of [feature]...

<h3>Assumptions</h3>
- Azure AKS for orchestration
- Kubernetes 1.24+
- ...
```

**Microsoft.VSTS.Common.AcceptanceCriteria Field:**
```
1. [ ] Component deployed and accessible
2. [ ] Integration tests pass
3. [ ] Monitoring configured
4. [ ] Load testing passed
5. [ ] Documentation completed
6. [ ] Security scan passed
7. [ ] Disaster recovery tested
8. [ ] UAT completed
```

---

## 📝 Progress Tracking

Progress saved in `expansion_progress_direct.json`:
```json
{
  "expanded": ["36", "37", "38", ...],
  "failed": [{"work_item_id": "999", "error": "...", "timestamp": "..."}],
  "pending": []
}
```

**Resume from failures:**
```bash
python expand_devops_stories_direct.py --batch 1 --limit 100 --no-confirm
```

---

## 🔧 Troubleshooting

### No stories found
```bash
python check_ado_stories.py
```

### Invalid credentials
Check `.env`:
- AZURE_ORG_URL format
- AZURE_PAT validity (may have expired)
- AZURE_PROJECT_NAME spelling

### MCP server issues
```bash
ls -la story_expansion_mcp.py
python story_expansion_mcp.py  # Test manually
```

---

## ⚡ Performance

- **Total stories:** 49
- **Per story:** 1-2 seconds
- **Per batch (100):** ~2 minutes
- **All stories:** ~5-10 minutes

---

## ✅ Next Steps

```bash
# 1. Test (dry run)
python expand_devops_stories_direct.py --limit 5 --dry-run --no-confirm

# 2. Check status
python expand_devops_stories_direct.py --status

# 3. Expand batch 1
python expand_devops_stories_direct.py --batch 1 --limit 100 --no-confirm

# 4. Verify in Azure DevOps
# Open any story and check Description + Acceptance Criteria fields
```

---

🚀 **Ready?** Run:
```bash
python expand_devops_stories_direct.py --batch 1 --limit 100 --no-confirm
```
