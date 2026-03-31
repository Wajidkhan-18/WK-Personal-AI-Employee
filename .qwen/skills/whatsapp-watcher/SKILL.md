---
name: whatsapp-watcher
description: |
  Monitor WhatsApp Web for new messages. Uses Playwright to automate WhatsApp Web
  and detect messages containing priority keywords. Creates action files in the
  Needs_Action folder for Claude Code to process.
---

# WhatsApp Watcher Skill

Monitor WhatsApp Web for messages requiring action.

## Prerequisites

```bash
# Install Playwright
pip install playwright
playwright install chromium

# Install base dependencies
pip install google-auth google-auth-oauthlib
```

## Usage

### Start WhatsApp Watcher

```bash
# Basic usage
python scripts/whatsapp_watcher.py

# Custom vault path
python scripts/whatsapp_watcher.py --vault /path/to/vault

# Custom check interval (default: 30 seconds)
python scripts/whatsapp_watcher.py --interval 60

# Headless mode (no browser UI)
python scripts/whatsapp_watcher.py --headless

# Specify keywords to detect
python scripts/whatsapp_watcher.py --keywords "urgent,payment,invoice,asap"
```

### Run in Background

```bash
# Using PM2 (recommended)
pm2 start scripts/whatsapp_watcher.py --name whatsapp-watcher --interpreter python3

# Using nohup
nohup python scripts/whatsapp_watcher.py > logs/whatsapp_watcher.log 2>&1 &
```

## How It Works

### 1. WhatsApp Web Automation

The watcher uses Playwright to:
- Launch Chromium with persistent session
- Navigate to web.whatsapp.com
- Scan chat list for unread messages
- Extract message content

### 2. Priority Keyword Detection

Default keywords that trigger action files:
- `urgent`, `asap`, `immediate`
- `invoice`, `payment`, `billing`, `money`
- `help`, `need`, `problem`
- `meeting`, `call`, `today`
- `contract`, `agreement`, `deal`

### 3. Action File Creation

For each priority message, creates:

```markdown
---
type: whatsapp
from: "+1234567890"
contact_name: "John Doe"
message: "Urgent: Need invoice for January"
received: 2026-03-30T14:30:00Z
priority: high
status: pending
chat_id: "1234567890@c.us"
keywords_matched: ["urgent", "invoice"]
---

## WhatsApp Message

**From:** John Doe (+1234567890)
**Received:** March 30, 2026 at 2:30 PM
**Chat:** Individual

---

Urgent: Need invoice for January

---

## Suggested Actions

- [ ] Generate invoice for January
- [ ] Send invoice (requires approval)
- [ ] Reply to contact (requires approval)
- [ ] Log transaction

## Context

- **Priority:** HIGH
- **Keywords:** urgent, invoice
- **Contact Type:** Business

## Notes

*Add any notes about this message below*

---

*Detected by WhatsAppWatcher at 2026-03-30 14:30:05*
```

## Session Management

### First-Time Setup

1. Run watcher in interactive mode:
```bash
python scripts/whatsapp_watcher.py --no-headless
```

2. Scan QR code with WhatsApp mobile app

3. Session saved to `~/.whatsapp_session/`

### Session Issues

```bash
# Clear session and re-authenticate
rm -rf ~/.whatsapp_session
python scripts/whatsapp_watcher.py --no-headless
```

## Security Considerations

⚠️ **Important:** WhatsApp Web automation may violate WhatsApp's Terms of Service.

- Use only for business accounts you own
- Consider official WhatsApp Business API for production
- Rate limit requests to avoid bans
- Never use for spam or unsolicited messages

## Error Handling

| Issue | Solution |
|-------|----------|
| QR code not showing | Clear session, restart with `--no-headless` |
| Session expired | Re-scan QR code |
| No messages detected | Check keyword list, verify unread messages exist |
| Browser crashes | Restart watcher, check system resources |

## Integration Flow

```
WhatsApp Web → Playwright → Keyword Detection → Needs_Action/
                                                      ↓
                                            Orchestrator → Pending_Approval
                                                                    ↓
                                                            [Human approves]
                                                                    ↓
                                                            Approved/ → WhatsApp MCP → Reply
```

## Testing

```bash
# Test connection (opens browser)
python scripts/whatsapp_watcher.py --test-connection

# Dry run (detect but don't create files)
python scripts/whatsapp_watcher.py --dry-run

# Verbose logging
python scripts/whatsapp_watcher.py --verbose
```

## Logs

- `AI_Employee_Vault/Logs/YYYY-MM-DD_WhatsAppWatcher.log`
- Console output (foreground mode)

## Troubleshooting

### "Playwright not installed"

```bash
pip install playwright
playwright install chromium
```

### "QR code timeout"

- Increase timeout: `--timeout 120`
- Ensure good internet connection
- Try with `--no-headless` to see browser

### "No unread messages"

- Verify messages are actually unread in WhatsApp
- Check keyword list matches message content
- Run with `--verbose` for debug info

## Example Workflow

### Client Requests Invoice via WhatsApp

```
Message: "Hey, can you send me the invoice?"
↓
WhatsApp Watcher detects: keywords "invoice"
↓
Creates: Needs_Action/WHATSAPP_john_doe.md (priority: high)
↓
Orchestrator moves to: Pending_Approval/
↓
Dashboard shows: 🔔 1 item awaiting review
↓
Human reviews and approves
↓
Claude generates invoice PDF
↓
WhatsApp MCP sends message with PDF
↓
File moved to Done/
```

## API Reference

### WhatsApp Watcher Class

```python
class WhatsAppWatcher(BaseWatcher):
    def __init__(self, vault_path: str, check_interval: int = 30,
                 keywords: List[str] = None, headless: bool = True)
    def check_for_updates(self) -> List[Dict]
    def create_action_file(self, message: Dict) -> Path
    def scan_qr_code(self) -> bool
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--vault` | `./AI_Employee_Vault` | Path to Obsidian vault |
| `--interval` | `30` | Check interval in seconds |
| `--keywords` | (see above) | Comma-separated keywords |
| `--headless` | `True` | Run browser without UI |
| `--timeout` | `60` | QR code timeout (seconds) |
| `--dry-run` | `False` | Detect but don't create files |

---

*WhatsApp Watcher v0.1 - Silver Tier Component*
*Part of Personal AI Employee Hackathon*
