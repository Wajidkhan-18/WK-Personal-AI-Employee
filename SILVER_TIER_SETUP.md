# Silver Tier Setup Guide

Complete setup instructions for the Silver Tier AI Employee.

---

## Prerequisites

Ensure Bronze Tier is complete and working:
- [x] Obsidian vault with Dashboard.md
- [x] Filesystem Watcher working
- [x] Orchestrator processing files
- [x] Qwen Code skills registered

---

## Step 1: Install Python Dependencies

```bash
cd scripts
pip install -r requirements.txt
playwright install chromium
```

### Verify Installation

```bash
python -c "import playwright; print('Playwright OK')"
python -c "from google.oauth2 import credentials; print('Gmail API OK')"
```

---

## Step 2: Set Up Gmail API (for Gmail Watcher)

### 2.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "AI Employee"
3. Enable **Gmail API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"

### 2.2 Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: **Desktop app**
4. Download `credentials.json`
5. Save to: `C:\Users\adnanlaptop\OneDrive\Documents\GitHub\WK-Personal-AI-Employee\credentials.json`

### 2.3 First-Time Authentication

```bash
cd scripts
python gmail_watcher.py --authenticate
```

This will:
1. Open browser
2. Ask for Google login
3. Request permissions
4. Save `token.json` to vault

---

## Step 3: Configure Skills in Qwen Code

Skills are already in `.qwen/skills/`:

```
.qwen/skills/
├── browsing-with-playwright/
├── gmail-watcher/
├── whatsapp-watcher/
├── linkedin-auto-post/
├── plan-generator/
└── vault-processor/
```

Verify in Qwen Code:
```bash
qwen --version
```

---

## Step 4: Set Up WhatsApp Watcher

### First Run (QR Code Scan)

```bash
cd scripts
python whatsapp_watcher.py --no-headless
```

1. Browser opens
2. Scan QR code with WhatsApp mobile app:
   - Open WhatsApp on phone
   - Settings → Linked Devices
   - Link a Device
   - Scan QR code
3. Session saved to `~/.whatsapp_session/`

### Subsequent Runs

```bash
python whatsapp_watcher.py  # Headless mode
```

---

## Step 5: Set Up LinkedIn Auto-Post

### First Run (Login)

```bash
cd scripts
python linkedin_poster.py create --content "Test post" --no-headless
```

1. Browser opens
2. Log in to LinkedIn
3. Session saved to `~/.linkedin_session/`

### Create Post Draft

```bash
python linkedin_poster.py create \
  --content "Excited to announce our new AI Employee system!" \
  --hashtags "#AI,#Automation,#Business"
```

### Post After Approval

After moving draft to `Approved/`:
```bash
python linkedin_poster.py post --vault ../AI_Employee_Vault
```

---

## Step 6: Install Scheduled Tasks

### Windows (Task Scheduler)

```bash
cd scripts
python scheduler.py install
```

Verify:
```bash
schtasks /query | findstr AI_Employee
```

### macOS (launchd)

```bash
python scheduler.py install
```

Verify:
```bash
launchctl list | grep aiemployee
```

### Linux (cron)

```bash
python scheduler.py install
```

Verify:
```bash
crontab -l
```

---

## Step 7: Configure MCP Email Server

### Install Node.js Dependencies

```bash
cd mcp-servers/email-mcp
npm install @modelcontextprotocol/sdk googleapis
```

### Create `.env` File

```bash
cd mcp-servers/email-mcp
echo GMAIL_CLIENT_ID=your_client_id > .env
echo GMAIL_CLIENT_SECRET=your_client_secret >> .env
```

### Configure Claude Code (Optional)

If using Claude Code with MCP:

```json
// ~/.config/claude-code/mcp.json
{
  "servers": [
    {
      "name": "email",
      "command": "node",
      "args": ["/path/to/email-mcp/index.js"],
      "env": {
        "GMAIL_CLIENT_ID": "your_client_id",
        "GMAIL_CLIENT_SECRET": "your_client_secret"
      }
    }
  ]
}
```

---

## Step 8: Start All Watchers

### Option A: Manual Start

```bash
# Terminal 1: Filesystem Watcher
python filesystem_watcher.py ../AI_Employee_Vault --interval 5

# Terminal 2: Gmail Watcher
python gmail_watcher.py ../AI_Employee_Vault --interval 120

# Terminal 3: WhatsApp Watcher
python whatsapp_watcher.py ../AI_Employee_Vault --interval 30
```

### Option B: Background with PM2

```bash
# Install PM2
npm install -g pm2

# Start watchers
pm2 start filesystem_watcher.py --name fs-watcher --interpreter python3 -- ../AI_Employee_Vault --interval 5
pm2 start gmail_watcher.py --name gmail-watcher --interpreter python3 -- ../AI_Employee_Vault --interval 120
pm2 start whatsapp_watcher.py --name whatsapp-watcher --interpreter python3 -- ../AI_Employee_Vault --interval 30

# Save configuration
pm2 save

# Auto-start on boot
pm2 startup
```

---

## Step 9: Run Orchestrator

### Manual Run

```bash
python orchestrator.py ../AI_Employee_Vault
```

### Continuous Mode

```bash
python orchestrator.py ../AI_Employee_Vault --continuous --interval 30
```

### Scheduled (via scheduler.py)

Already configured in Step 6 for daily briefings at 8 AM.

---

## Step 10: Test End-to-End Workflow

### Test Gmail Integration

1. Send yourself an email with subject: "Test invoice request"
2. Wait 2 minutes (or run Gmail Watcher manually)
3. Check `Needs_Action/` for `EMAIL_*.md` file
4. Run orchestrator:
   ```bash
   python orchestrator.py ../AI_Employee_Vault
   ```
5. Check `Pending_Approval/` for the file
6. Check `Dashboard.md` for update

### Test WhatsApp Integration

1. Send yourself a WhatsApp message: "Urgent: need help"
2. Run WhatsApp Watcher:
   ```bash
   python whatsapp_watcher.py ../AI_Employee_Vault
   ```
3. Check `Needs_Action/` for `WHATSAPP_*.md` file

### Test LinkedIn Post

1. Create draft:
   ```bash
   python linkedin_poster.py create --content "Silver tier test!" --vault ../AI_Employee_Vault
   ```
2. Move file from `Needs_Action/` to `Approved/`
3. Post:
   ```bash
   python linkedin_poster.py post --vault ../AI_Employee_Vault
   ```

---

## Verification Checklist

### Watchers

- [ ] Filesystem Watcher: Detects files in Drop/
- [ ] Gmail Watcher: Detects new emails
- [ ] WhatsApp Watcher: Detects priority messages
- [ ] All create action files in Needs_Action/

### Processing

- [ ] Orchestrator moves files to Pending_Approval/
- [ ] Dashboard.md updates correctly
- [ ] Approved files get processed

### Skills

- [ ] Qwen Code sees all 6 skills
- [ ] Skills can be invoked
- [ ] Plan.md generation works

### Scheduling

- [ ] Daily briefing scheduled (8 AM)
- [ ] Weekly audit scheduled (Sunday 7 AM)
- [ ] Health check every 30 min

---

## Troubleshooting

### "Gmail API not working"

1. Check credentials.json exists
2. Re-run authentication: `python gmail_watcher.py --authenticate`
3. Check Gmail API is enabled in Google Cloud Console

### "WhatsApp QR code not showing"

1. Clear session: `rm -rf ~/.whatsapp_session`
2. Run with `--no-headless`
3. Ensure good internet connection

### "LinkedIn post fails"

1. Clear session: `rm -rf ~/.linkedin_session`
2. Log in manually first
3. Check content length (< 3000 chars)

### "Scheduled tasks not running"

**Windows:**
```bash
schtasks /run /tn "AI_Employee_daily_briefing"
```

**macOS:**
```bash
launchctl start com.aiemployee.daily_briefing
```

**Linux:**
```bash
run-parts /etc/cron.daily/
```

---

## Next Steps

After Silver Tier is fully operational:

1. **Monitor for 24-48 hours** to ensure stability
2. **Review Company_Handbook.md** and customize rules
3. **Add more keywords** to watchers as needed
4. **Set up Gold Tier** components:
   - Odoo accounting integration
   - Facebook/Instagram integration
   - Twitter (X) integration
   - Enhanced error recovery

---

## Support

- Documentation: `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`
- Weekly Meeting: Wednesdays 10:00 PM on Zoom
- Silver Tier Summary: `SILVER_TIER_COMPLETE.md`

---

*Silver Tier Setup Guide v0.1*
*Generated: 2026-03-30*
