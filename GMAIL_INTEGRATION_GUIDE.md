# 📧 Gmail Integration - Complete Guide

## ✅ What's Working

Your Gmail integration is **fully functional**:

- ✅ OAuth2 authentication complete
- ✅ Token saved: `AI_Employee_Vault/.gmail_token.json`
- ✅ Gmail Watcher running
- ✅ Monitoring INBOX for unread emails
- ✅ Priority detection (urgent, invoice, payment, etc.)

---

## 🔄 How Gmail Workflow Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. Gmail Watcher runs every 30 seconds                     │
│     python scripts/gmail_watcher.py VAULT_PATH              │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Checks Gmail API for new unread emails                  │
│     - Uses OAuth2 token (already authenticated)             │
│     - Looks for: is:unread in:INBOX                         │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  3. For each new email:                                     │
│     - Extracts: From, Subject, Body, Attachments            │
│     - Detects priority (urgent, billing, lead, etc.)        │
│     - Categorizes (billing, meeting, support, etc.)         │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Creates action file in Needs_Action/                    │
│     FILE: EMAIL_20260330_123456_sender_subject.md           │
│                                                             │
│     Contains:                                               │
│     - Full email content                                    │
│     - Priority level                                        │
│     - Suggested actions                                     │
│     - Reply draft section                                   │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  5. Orchestrator processes the file                         │
│     python scripts/orchestrator.py VAULT_PATH               │
│                                                             │
│     - Moves to Pending_Approval/                            │
│     - Updates Dashboard.md                                  │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  6. Human reviews (HITL)                                    │
│     - Opens Needs_Action/ or Pending_Approval/              │
│     - Reviews email and suggested actions                   │
│     - Moves to Approved/ to proceed                         │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  7. AI processes (Qwen Code)                                │
│     qwen --prompt "Process all files in Approved"           │
│                                                             │
│     - Drafts response                                       │
│     - Takes action (via MCP if configured)                  │
│     - Moves to Done/                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure

```
AI_Employee_Vault/
├── .gmail_token.json          # OAuth2 token (authenticated!)
├── .state_GmailWatcher.json   # Processed email IDs
├── Dashboard.md               # Real-time status
├── Company_Handbook.md        # Rules for email handling
├── Inbox/                     # Processed email files
├── Needs_Action/              # New action files from Gmail
├── Pending_Approval/          # Awaiting your review
├── Approved/                  # Ready for AI processing
├── Done/                      # Completed emails
└── Logs/
    └── YYYY-MM-DD_GmailWatcher.log
```

---

## 🚀 How to Use

### Start Gmail Watcher

```bash
cd C:\Users\adnanlaptop\OneDrive\Documents\GitHub\WK-Personal-AI-Employee

# Run Gmail Watcher (checks every 30 seconds)
python scripts\gmail_watcher.py AI_Employee_Vault --interval 30
```

### Run Orchestrator

```bash
# Process new emails
python scripts\orchestrator.py AI_Employee_Vault

# Or continuous mode
python scripts\orchestrator.py AI_Employee_Vault --continuous --interval 30
```

### Process with Qwen Code

```bash
cd AI_Employee_Vault
qwen --prompt "Process all files in Needs_Action folder"
```

---

## 📊 Email Priority Detection

The watcher automatically detects priority based on keywords:

| Priority | Keywords |
|----------|----------|
| **High** | urgent, asap, immediate, priority |
| **Billing** | invoice, payment, bill, receipt |
| **Meeting** | meeting, call, schedule, zoom |
| **Lead** | pricing, quote, interested, demo |
| **Support** | help, issue, problem, bug |

---

## 📧 Example Action File

When you receive an email like:
```
From: client@example.com
Subject: Invoice Request - January 2026
Body: Can you please send me the invoice for January?
```

It creates: `Needs_Action/EMAIL_20260330_143000_client_invoice.md`

```markdown
---
type: email
from: "client@example.com"
subject: "Invoice Request - January 2026"
received: 2026-03-30T14:30:00Z
priority: high
category: billing
status: pending
gmail_id: "18f3c2a1b5d4e6f7"
---

## Email Content

**From:** client@example.com
**To:** you@yourcompany.com
**Date:** March 30, 2026 at 2:30 PM
**Subject:** Invoice Request - January 2026

---

Can you please send me the invoice for January?

---

## Suggested Actions

- [ ] Generate invoice for January 2026
- [ ] Send invoice via email (requires approval)
- [ ] Log transaction in Accounting folder

## Reply Draft

*Draft your reply here*

---

*Detected by GmailWatcher at 2026-03-30 14:30:05*
```

---

## 🎯 Test It Now

### Send Yourself a Test Email

1. From another email, send to your Gmail:
   - Subject: `Test invoice request`
   - Body: `Please send me a test invoice`

2. Wait 30 seconds (watcher checks every 30s)

3. Check `Needs_Action/` folder - new file should appear!

4. Run orchestrator:
   ```bash
   python scripts\orchestrator.py AI_Employee_Vault
   ```

5. Check `Dashboard.md` - it should show the new email!

---

## ⚙️ Configuration

### Gmail Watcher Options

```bash
# Custom interval (default: 30 seconds)
python scripts\gmail_watcher.py AI_Employee_Vault --interval 60

# Check all emails (not just unread)
python scripts\gmail_watcher.py AI_Employee_Vault --all-emails

# Specific label (default: INBOX)
python scripts\gmail_watcher.py AI_Employee_Vault --label "Important"

# Verbose logging
python scripts\gmail_watcher.py AI_Employee_Vault --verbose
```

### Company Handbook Rules

Edit `Company_Handbook.md` to customize:
- Response time targets
- Approval thresholds
- Email handling rules
- Priority keywords

---

## 🔧 Troubleshooting

### "Gmail service not initialized"

Run authentication again:
```bash
python scripts\gmail_watcher.py AI_Employee_Vault --authenticate
```

### "No new emails detected"

- Check if emails are marked as unread
- Verify Gmail API has correct scopes
- Check watcher logs in `Logs/` folder

### "Token expired"

The token auto-refreshes, but if needed:
```bash
# Delete old token
del AI_Employee_Vault\.gmail_token.json

# Re-authenticate
python scripts\gmail_watcher.py AI_Employee_Vault --authenticate
```

---

## 📈 Dashboard Integration

The Dashboard.md automatically updates to show:
- Number of new emails
- Priority emails awaiting action
- Response time metrics
- Email processing history

---

## 🔐 Security

- ✅ OAuth2 authentication (no passwords stored)
- ✅ Token stored securely in vault
- ✅ Read-only access by default
- ✅ Send requires separate approval workflow
- ✅ All actions logged

---

## 📞 Support

- Logs: `AI_Employee_Vault/Logs/YYYY-MM-DD_GmailWatcher.log`
- State: `AI_Employee_Vault/.state_GmailWatcher.json`
- Token: `AI_Employee_Vault/.gmail_token.json`

---

*Gmail Integration - Silver Tier Component*
*Status: ✅ Fully Working*
*Last Updated: 2026-03-30*
