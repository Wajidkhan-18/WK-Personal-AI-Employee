# AI Employee - Bronze Tier Setup

Quick start guide for the Bronze Tier implementation.

## Prerequisites

Ensure you have installed:
- **Qwen Code**: Install from https://github.com/QwenLM/Qwen
- **Python 3.13+**: Download from python.org
- **Obsidian**: Download from obsidian.md
- **Node.js v24+**: Download from nodejs.org

## Quick Start

### 1. Open the Vault in Obsidian

```
# Open Obsidian and select the AI_Employee_Vault folder as your vault
# Or run:
obsidian://open?vault=AI_Employee_Vault
```

### 2. Install Python Dependencies (Optional)

For event-based file watching (recommended):

```bash
pip install watchdog
```

### 3. Test the Filesystem Watcher

Start the watcher in one terminal (run from project root):

```bash
python scripts\filesystem_watcher.py AI_Employee_Vault --interval 5
```

### 4. Drop a Test File

In another terminal, drop a file into the Drop folder:

```bash
echo "Test content for AI Employee processing" > AI_Employee_Vault\Drop\test_document.txt
```

The watcher should detect the file and create an action file in `Needs_Action/`.

### 5. Run the Orchestrator

In a third terminal (run from project root):

```bash
python scripts\orchestrator.py AI_Employee_Vault
```

This will:
- Scan the Needs_Action folder
- Process any pending action files
- Update Dashboard.md
- Move completed files to Done

### 6. Verify Results

Check the vault:
- `Dashboard.md` should be updated
- `Inbox/test_document.txt` should exist
- `Needs_Action/` should have a new action file (or be empty if processed)
- `Logs/` should contain log files

## Continuous Operation

For continuous monitoring (run from project root):

```bash
# Terminal 1: Filesystem Watcher
python scripts\filesystem_watcher.py AI_Employee_Vault --interval 5

# Terminal 2: Orchestrator (every 30 seconds)
python scripts\orchestrator.py AI_Employee_Vault --continuous --interval 30
```

## Using with Qwen Code

Process files manually with Qwen Code (run from project root):

```bash
cd AI_Employee_Vault
qwen --prompt "Process all files in Needs_Action folder. Follow the Company_Handbook.md rules."
```

## Folder Structure

```
AI_Employee_Vault/
├── Dashboard.md          # Real-time status dashboard
├── Company_Handbook.md   # Rules of engagement
├── Business_Goals.md     # Objectives and targets
├── Inbox/                # Drop zone for new files
├── Needs_Action/         # Pending action files
├── Done/                 # Completed items
├── Plans/                # Task plans
├── Pending_Approval/     # Awaiting human approval
├── Approved/             # Approved actions
├── Rejected/             # Rejected actions
├── Logs/                 # System logs
├── Briefings/            # CEO briefings
└── Accounting/           # Financial records
```

## Bronze Tier Checklist

- [x] Obsidian vault with Dashboard.md
- [x] Company_Handbook.md with rules
- [x] Business_Goals.md template
- [x] Basic folder structure
- [x] Filesystem Watcher script
- [x] Orchestrator script
- [ ] Test with Qwen Code processing
- [ ] Verify end-to-end workflow

## Troubleshooting

### "Qwen Code not found"
```bash
# Install Qwen Code from https://github.com/QwenLM/Qwen
qwen --version
```

### "watchdog not installed"
```bash
pip install watchdog
```

### "Vault path does not exist"
Ensure you're using the correct path to AI_Employee_Vault folder.

### Files not being detected
- Check watcher is running
- Verify drop folder permissions
- Try shorter check interval (--interval 2)

## Next Steps (Silver Tier)

After Bronze is working:
1. Add Gmail Watcher
2. Add WhatsApp Watcher
3. Implement MCP server for email sending
4. Add scheduling (cron/Task Scheduler)
5. Create Plan.md generation logic

## Support

- Documentation: `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`
- Weekly Meeting: Wednesdays 10:00 PM on Zoom
