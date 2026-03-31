# AI Employee - How Qwen Code Processes Files

## Overview

This system is designed to work with **Qwen Code** (or any AI assistant). The Python scripts handle file monitoring and organization, while Qwen Code does the actual reasoning and decision-making.

---

## 🔄 Complete Workflow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  You drop file  │ ──▶ │  Filesystem      │ ──▶ │  Creates action │
│  in Drop/       │     │  Watcher (Python)│     │  file           │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  File in Done/  │ ◀── │  Qwen Code       │ ◀── │  Orchestrator   │
│  (complete)     │     │  (AI reasoning)  │     │  prepares       │
└─────────────────┘     └──────────────────┘     └──────────────────┘
```

---

## 📋 Step-by-Step Process

### Step 1: Filesystem Watcher (Python)

**Runs continuously in background**

```bash
python scripts\filesystem_watcher.py AI_Employee_Vault --interval 5
```

**What it does:**
- Monitors `Drop/` folder every 5 seconds
- When file detected: moves to `Inbox/` and creates action file in `Needs_Action/`

---

### Step 2: Orchestrator (Python)

**Runs once or continuously**

```bash
python scripts\orchestrator.py AI_Employee_Vault
```

**What it does:**
- Scans `Needs_Action/` for action files
- Creates `_AI_PROCESSING_INSTRUCTIONS.md` with list of files to process
- Updates `Dashboard.md`
- **Does NOT process files itself** - prepares them for Qwen Code

---

### Step 3: Qwen Code Processing (AI)

**You interact with Qwen Code directly**

After the orchestrator runs, you'll see:
- `_AI_PROCESSING_INSTRUCTIONS.md` in the vault root
- Action files in `Needs_Action/`

**Now ask Qwen Code to process:**

Since you're already using Qwen Code (like in this chat), just say:

> "Process the action files in Needs_Action folder according to Company_Handbook.md"

Or manually:

1. Open the vault in Obsidian
2. Read `_AI_PROCESSING_INSTRUCTIONS.md`
3. Read each action file in `Needs_Action/`
4. Execute the required tasks
5. Move completed files to `Done/`
6. Update `Dashboard.md`

---

## 🤖 How Qwen Code Processes Files

When Qwen Code processes action files, it should:

### 1. Read Action File

```markdown
---
type: file_drop
original_name: "document.txt"
file_path: "Inbox/20260327_000000_document.txt"
priority: "normal"
---

## File Drop for Processing
...
```

### 2. Understand the Task

Based on the file type and content:
- `file_drop` → Review and categorize
- `email` → Draft response
- `whatsapp` → Analyze and respond
- `invoice` → Process payment (may need approval)

### 3. Execute Actions

Examples:
- Read the file content from `Inbox/`
- Analyze and extract key information
- Create summary or response
- Update relevant files

### 4. Move to Done

After processing:
```bash
# Move action file to Done/
move Needs_Action\FILE_*.md Done\
```

### 5. Update Dashboard

Update `Dashboard.md`:
- Increment task counters
- Add entry to Recent Activity
- Clear processed items

---

## 🧪 Example: Complete Flow

### You drop a file:
```bash
echo "Meeting notes: Discuss Q1 budget and new project timeline" > AI_Employee_Vault\Drop\meeting_notes.txt
```

### Watcher detects (within 5 seconds):
```
Needs_Action/FILE_20260327_120000_meeting_notes.md created
```

### Orchestrator runs:
```bash
python scripts\orchestrator.py AI_Employee_Vault
```

Output:
```
✓ Found 1 pending item(s)
✓ Created processing instructions: _AI_PROCESSING_INSTRUCTIONS.md
✓ Files ready for AI processing
✓ Dashboard updated
```

### Qwen Code processes:

**Reads:**
- `_AI_PROCESSING_INSTRUCTIONS.md`
- `Needs_Action/FILE_20260327_120000_meeting_notes.md`
- `Inbox/20260327_120000_meeting_notes.txt`

**Actions:**
1. Summarizes meeting notes
2. Extracts action items
3. Creates summary in `Inbox/meeting_notes_summary.md`
4. Moves action file to `Done/`
5. Updates `Dashboard.md`

---

## 📝 Qwen Code Instructions

When asking Qwen Code to process files, use this prompt:

```
I have an AI Employee system with action files ready for processing.

Please:
1. Read _AI_PROCESSING_INSTRUCTIONS.md for the list of files
2. For each action file in Needs_Action/:
   - Read the frontmatter to understand the type
   - Read the content for details
   - Execute the required actions (file operations, analysis, drafting)
   - Follow Company_Handbook.md rules
3. When complete for each file:
   - Move the action file to Done/
   - Update Dashboard.md with progress
   - Log actions in Logs/YYYY-MM-DD.md

Be thorough and ask for approval before any sensitive actions (payments, 
sending messages, etc.).
```

---

## 🎯 Key Files

| File | Purpose |
|------|---------|
| `_AI_PROCESSING_INSTRUCTIONS.md` | List of files ready for AI processing |
| `Needs_Action/*.md` | Action files waiting to be processed |
| `Company_Handbook.md` | Rules and guidelines for AI |
| `Dashboard.md` | Real-time status |
| `Logs/YYYY-MM-DD_orchestrator.log` | Python script logs |

---

## ✅ Bronze Tier Capabilities

The current implementation:
- ✅ Monitors for new files (Python Watcher)
- ✅ Creates structured action files
- ✅ Prepares files for AI processing (Orchestrator)
- ✅ Updates Dashboard
- ✅ Maintains logs
- ⏳ AI processing done by Qwen Code (manual trigger)

### Future Enhancement (Silver Tier)
- Auto-trigger Qwen Code via API
- Gmail/WhatsApp integration
- MCP servers for external actions
- Scheduled operations

---

## 💡 Pro Tips

1. **Run orchestrator after dropping files** - Creates processing instructions
2. **Check Dashboard.md** - See what needs attention
3. **Review Company_Handbook.md** - Understand the rules
4. **Move files to Done/** - Mark tasks complete
5. **Check Logs/** - Debug any issues

---

*This system is AI-agnostic. While designed for Qwen Code, it can work with Claude Code, Cursor, or any AI assistant that can read/write files.*
