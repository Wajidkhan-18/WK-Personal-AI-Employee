# AI Employee - Command Reference (Windows)

All commands are designed to be run from the **project root folder**:
`C:\Users\adnanlaptop\OneDrive\Documents\GitHub\WK-Personal-AI-Employee\`

> **Note:** This system works with any AI assistant (Qwen Code, Claude Code, etc.). Since you're using **Qwen Code**, all processing is done by Qwen itself.

---

## 🚀 Quick Start Commands

### 1. Start Filesystem Watcher (Terminal 1)

```bash
python scripts\filesystem_watcher.py AI_Employee_Vault --interval 5
```

**What it does:** Watches the `Drop/` folder for new files

**Expected output:**
```
📁 Filesystem Watcher starting...
   Vault: AI_Employee_Vault
   Drop folder: AI_Employee_Vault\Drop
   Check interval: 5s
   Mode: Polling
```

---

### 2. Drop a Test File (any terminal)

```bash
echo "Test content for processing" > AI_Employee_Vault\Drop\test.txt
```

**What it does:** Creates a file for the watcher to detect

---

### 3. Run Orchestrator (Terminal 2)

```bash
python scripts\orchestrator.py AI_Employee_Vault
```

**What it does:** Processes action files in `Needs_Action/` folder

**Expected output:**
```
🤖 AI Employee Orchestrator
   Vault: AI_Employee_Vault
   Mode: Single run

✓ Orchestrator initialized
✓ Starting processing cycle
✓ Dashboard updated
✓ Cycle complete
```

---

### 4. Process with Qwen Code (optional)

The orchestrator can trigger Qwen Code automatically, or you can run it manually:

```bash
cd AI_Employee_Vault
# Qwen Code will read and process the action files
# (Use your preferred method to invoke Qwen Code)
```

**What it does:** Uses Qwen Code to analyze and process action files

---

## 🔄 Continuous Operation

### Run Watcher + Orchestrator Together

**Terminal 1 - Watcher:**
```bash
python scripts\filesystem_watcher.py AI_Employee_Vault --interval 5
```

**Terminal 2 - Orchestrator:**
```bash
python scripts\orchestrator.py AI_Employee_Vault --continuous --interval 30
```

**What it does:** Fully autonomous operation - files are processed automatically

---

## 📋 All Available Commands

| Command | Purpose |
|---------|---------|
| `python scripts\filesystem_watcher.py AI_Employee_Vault` | Start file watcher (polling mode) |
| `python scripts\filesystem_watcher.py AI_Employee_Vault --interval 2` | Start watcher with 2 second check interval |
| `python scripts\filesystem_watcher.py AI_Employee_Vault --watchdog` | Start watcher (event-based, requires `pip install watchdog`) |
| `python scripts\orchestrator.py AI_Employee_Vault` | Run orchestrator once |
| `python scripts\orchestrator.py AI_Employee_Vault --continuous --interval 30` | Run orchestrator continuously (every 30 seconds) |
| `Ctrl+C` | Stop any running process |

---

## 🛑 Stop Commands

To stop any running process, press:
```
Ctrl+C
```

---

## 🧪 Complete Test Sequence

Copy and paste these commands one by one:

```bash
# Step 1: Start watcher (Terminal 1)
start python scripts\filesystem_watcher.py AI_Employee_Vault --interval 2

# Wait 3 seconds for watcher to start
timeout /t 3 /nobreak >nul

# Step 2: Drop a test file
echo "Please summarize this document" > AI_Employee_Vault\Drop\test_file.txt

# Wait 5 seconds for watcher to detect
timeout /t 5 /nobreak >nul

# Step 3: Check if action file was created
dir AI_Employee_Vault\Needs_Action

# Step 4: Run orchestrator (Terminal 2)
python scripts\orchestrator.py AI_Employee_Vault

# Step 5: Check results
dir AI_Employee_Vault\Done
type AI_Employee_Vault\Dashboard.md
```

---

## 📁 Folder Locations

| Folder | Path (from root) |
|--------|------------------|
| Project Root | `C:\Users\adnanlaptop\OneDrive\Documents\GitHub\WK-Personal-AI-Employee\` |
| Scripts | `scripts\` |
| Vault | `AI_Employee_Vault\` |
| Drop Zone | `AI_Employee_Vault\Drop\` |
| Inbox | `AI_Employee_Vault\Inbox\` |
| Needs Action | `AI_Employee_Vault\Needs_Action\` |
| Done | `AI_Employee_Vault\Done\` |
| Logs | `AI_Employee_Vault\Logs\` |

---

## 🔧 Installation Commands

### Install Python Dependencies

```bash
pip install watchdog
```

---

## ❓ Troubleshooting Commands

| Problem | Command to Fix |
|---------|----------------|
| "No such file" error | Make sure you're in project root: `cd C:\Users\adnanlaptop\OneDrive\Documents\GitHub\WK-Personal-AI-Employee` |
| Watcher not detecting files | Use shorter interval: `--interval 2` |
| Check if watcher is running | Look for log files in `AI_Employee_Vault\Logs\` |

---

*All commands work on Windows. For Mac/Linux, use `/` instead of `\` in paths.*
