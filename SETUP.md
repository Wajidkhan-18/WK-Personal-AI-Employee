# AI Employee - Setup Guide

**Complete setup in 15 minutes**

---

## 📋 Prerequisites Check

Ensure you have installed:
- [ ] Python 3.13+
- [ ] Node.js v24+
- [ ] Obsidian
- [ ] Qwen Code (optional, for AI processing)

---

## 🚀 Step-by-Step Setup

### Step 1: Install Python Dependencies (2 minutes)

```bash
cd scripts
pip install -r requirements.txt
playwright install
```

### Step 2: Install Node.js Dependencies (1 minute)

```bash
cd scripts
npm install
```

### Step 3: Open Obsidian Vault (30 seconds)

1. Open Obsidian
2. Click "Open folder as vault"
3. Select: `AI_Employee_Vault/` folder

### Step 4: Test Filesystem Watcher (1 minute)

```bash
# Terminal 1: Start watcher
python scripts\filesystem_watcher.py AI_Employee_Vault --interval 5

# Terminal 2: Drop a test file
echo "Test document for processing" > AI_Employee_Vault\Drop\test.txt
```

Watcher should detect and create action file in `Needs_Action/`.

### Step 5: Run Orchestrator (1 minute)

```bash
python scripts\orchestrator.py AI_Employee_Vault
```

Check `Dashboard.md` in Obsidian - it should update!

---

## 🔗 Optional Integrations

### Gmail Integration (5 minutes)

1. **Get Gmail Credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing
   - Enable "Gmail API"
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
   - Download `credentials.json`
   - Place in `scripts/` folder

2. **First Run (Authorizes OAuth):**
   ```bash
   python scripts\gmail_watcher.py AI_Employee_Vault --interval 120
   ```
   - Browser will open
   - Sign in with Google
   - Grant permissions
   - Token saved to `AI_Employee_Vault/.gmail_token.json`

3. **Test:** Send yourself an email with subject "Test"

### WhatsApp Integration (3 minutes)

1. **First Run (QR Code Scan):**
   ```bash
   python scripts\whatsapp_watcher.py AI_Employee_Vault --no-headless
   ```
   - Browser opens with WhatsApp Web
   - Scan QR code with your phone
   - Session saved to `AI_Employee_Vault/.whatsapp_session/`

2. **Subsequent Runs (Headless):**
   ```bash
   python scripts\whatsapp_watcher.py AI_Employee_Vault
   ```

### LinkedIn Integration (3 minutes)

1. **First Run (Login):**
   ```bash
   python scripts\linkedin_poster.py AI_Employee_Vault draft --content "Test post" --no-headless
   ```
   - Browser opens
   - Login to LinkedIn
   - Session saved

2. **Create Lead Gen Post:**
   ```bash
   python scripts\linkedin_poster.py AI_Employee_Vault leadgen ^
     --topic "AI Automation" ^
     --value-prop "Reduce operational costs by 50%" ^
     --cta "Let's connect!"
   ```

### Email MCP Server (5 minutes)

1. **Setup Gmail Credentials** (same as Gmail Watcher above)

2. **Start MCP Server:**
   ```bash
   node scripts\email-mcp-server.js --credentials scripts\credentials.json
   ```

3. **Use with Qwen Code:**
   ```bash
   # Qwen Code will use the MCP server tools automatically
   ```

---

## ⏰ Set Up Scheduling (2 minutes)

### Windows Task Scheduler

```bash
# Install scheduled tasks
python scripts\scheduler.py install --vault AI_Employee_Vault

# Check status
python scripts\scheduler.py status

# Uninstall
python scripts\scheduler.py uninstall
```

### Linux/Mac Cron

```bash
# Install cron jobs
python scripts\scheduler.py install --vault AI_Employee_Vault --use-cron

# View crontab
crontab -l
```

---

## ✅ Verify Setup

### Check All Components

```bash
# 1. Test Python scripts
python -m py_compile scripts\*.py
# Should show no errors

# 2. Test orchestrator
python scripts\orchestrator.py AI_Employee_Vault
# Should show "Cycle complete"

# 3. Test briefing generator
python scripts\generate_briefing.py AI_Employee_Vault
# Should create briefing in Briefings/

# 4. Check Obsidian
# Open AI_Employee_Vault/Dashboard.md
# Should see updated status
```

### Expected Vault Structure

```
AI_Employee_Vault/
├── Dashboard.md              ✅ Should be updated
├── Company_Handbook.md       ✅ Created
├── Business_Goals.md         ✅ Created
├── Drop/                     ✅ Ready for files
├── Inbox/                    ✅ Contains processed files
├── Needs_Action/             ✅ Action files here
├── Plans/                    ✅ Generated plans
├── Pending_Approval/         ✅ Approval requests
├── Approved/                 ✅ Approved items
├── Done/                     ✅ Completed items
├── Briefings/                ✅ Weekly briefings
├── Accounting/               ✅ Financial records
└── Logs/                     ✅ System logs
```

---

## 🎯 Quick Test Workflow

1. **Drop a file:**
   ```bash
   echo "Process this invoice" > AI_Employee_Vault\Drop\invoice.txt
   ```

2. **Wait 5 seconds** (Filesystem Watcher detects)

3. **Run orchestrator:**
   ```bash
   python scripts\orchestrator.py AI_Employee_Vault
   ```

4. **Check in Obsidian:**
   - `Needs_Action/` should have new action file
   - `Plans/` should have generated plan
   - `Dashboard.md` should be updated

5. **Process with AI (optional):**
   ```bash
   cd AI_Employee_Vault
   qwen --prompt "Process files in Needs_Action/ folder"
   ```

---

## 🆘 Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Playwright not installed"
```bash
playwright install
```

### "Gmail credentials not found"
- Download `credentials.json` from Google Cloud Console
- Place in `scripts/` folder

### "WhatsApp not logging in"
- Run with `--no-headless` flag
- Scan QR code promptly (expires in ~30 seconds)

### "Dashboard not updating"
- Check orchestrator ran successfully
- Verify vault path is correct
- Check `Logs/` folder for errors

---

## 📞 Support

- **Documentation:** `SILVER_TIER_README.md`
- **Architecture:** `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`
- **Weekly Meeting:** Wednesdays 10:00 PM on Zoom

---

*Setup Guide - AI Employee v0.2 (Silver Tier)*
