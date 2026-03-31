---
name: gmail-watcher
description: |
  Monitor Gmail for new and important emails. Creates action files in the
  Needs_Action folder for Claude Code to process. Supports OAuth2 authentication,
  priority detection, and duplicate prevention.
---

# Gmail Watcher Skill

Monitor Gmail inbox and create actionable files for new emails.

## Prerequisites

### 1. Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials.json

### 2. Install Dependencies

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 3. First-Time Authentication

```bash
python scripts/gmail_watcher.py --authenticate
```

This creates a token.json file for future use.

## Configuration

Create `.env` file in project root:

```bash
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REDIRECT_URI=http://localhost:8080
VAULT_PATH=/path/to/AI_Employee_Vault
```

## Usage

### Start Gmail Watcher

```bash
# Basic usage
python scripts/gmail_watcher.py

# Custom vault path
python scripts/gmail_watcher.py --vault /path/to/vault

# Custom check interval (default: 120 seconds)
python scripts/gmail_watcher.py --interval 60

# Only check unread emails
python scripts/gmail_watcher.py --unread-only

# Check specific label/folder
python scripts/gmail_watcher.py --label "INBOX"
```

### Run in Background

```bash
# Using PM2 (recommended)
pm2 start scripts/gmail_watcher.py --name gmail-watcher --interpreter python3

# Using nohup
nohup python scripts/gmail_watcher.py > logs/gmail_watcher.log 2>&1 &
```

## How It Works

### 1. Email Detection

The watcher polls Gmail every N seconds (configurable) for:
- Unread emails
- Important/starred emails
- Emails from known contacts
- Emails matching priority keywords

### 2. Priority Detection

Keywords that trigger **high priority**:
- `urgent`, `asap`, `immediate`
- `invoice`, `payment`, `billing`
- `contract`, `legal`, `agreement`
- `meeting`, `deadline`, `today`

### 3. Action File Creation

For each new email, creates:

```markdown
---
type: email
from: "John Doe <john@example.com>"
to: "you@yourcompany.com"
subject: "Invoice Request - January 2026"
received: 2026-03-30T14:30:00Z
priority: high
status: pending
gmail_id: "18f3c2a1b5d4e6f7"
labels: ["INBOX", "UNREAD", "IMPORTANT"]
---

## Email Content

**From:** John Doe <john@example.com>
**To:** you@yourcompany.com
**Date:** March 30, 2026 at 2:30 PM
**Subject:** Invoice Request - January 2026

---

Hi,

Could you please send me the invoice for January 2026?
I need it for accounting purposes.

Thanks,
John

---

## Suggested Actions

- [ ] Generate invoice for January 2026
- [ ] Send invoice via email (requires approval)
- [ ] Log transaction in Accounting folder
- [ ] Mark email as read

## Attachments

*No attachments*

## Context

- **Known Contact:** Yes (3 previous emails)
- **Contains Keywords:** invoice, accounting
- **Action Required:** Yes - billing request

---

*Detected by GmailWatcher at 2026-03-30 14:30:05*
```

### 4. Duplicate Prevention

Tracks processed Gmail IDs in `.state_GmailWatcher.json` to avoid processing the same email twice.

## Email Categories

The watcher categorizes emails for better handling:

| Category | Keywords | Auto-Action |
|----------|----------|-------------|
| **Billing** | invoice, payment, bill, receipt | Draft response |
| **Meeting** | meeting, call, schedule, zoom | Create calendar event draft |
| **Lead** | pricing, quote, interested, demo | Flag for follow-up |
| **Support** | help, issue, problem, bug | Create support ticket |
| **Newsletter** | newsletter, digest, update | Archive after reading |
| **General** | (none of above) | Standard processing |

## Integration with Orchestrator

The Gmail Watcher integrates with the main orchestrator:

```
Gmail → Gmail Watcher → Needs_Action/ → Orchestrator → Pending_Approval
                                                    ↓
                                            [Human approves reply]
                                                    ↓
                                            Approved/ → Email MCP → Send
```

## Error Handling

### Common Issues

| Issue | Solution |
|-------|----------|
| `credentials.json not found` | Download from Google Cloud Console |
| `token.json expired` | Run `--authenticate` again |
| `API quota exceeded` | Increase interval between checks |
| `Connection timeout` | Check internet connection, retry logic handles this |

### Retry Logic

Automatic retry with exponential backoff:
- Attempt 1: Immediate
- Attempt 2: After 5 seconds
- Attempt 3: After 15 seconds
- Attempt 4: After 30 seconds (then alert)

## Security

### Credential Storage

- **NEVER** commit credentials to git
- Store in `.env` file (added to `.gitignore`)
- Use system keychain for production
- Rotate credentials monthly

### Scopes Requested

```python
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # Read emails
    'https://www.googleapis.com/auth/gmail.send',      # Send emails (for MCP)
    'https://www.googleapis.com/auth/gmail.modify',    # Mark as read
]
```

## Testing

```bash
# Test connection
python scripts/gmail_watcher.py --test-connection

# Test authentication
python scripts/gmail_watcher.py --test-auth

# Simulate email detection (dry run)
python scripts/gmail_watcher.py --dry-run
```

## Logs

Logs are written to:
- `AI_Employee_Vault/Logs/YYYY-MM-DD_GmailWatcher.log`
- Console output (when running in foreground)

## Stopping the Watcher

```bash
# If running with PM2
pm2 stop gmail-watcher

# If running in foreground
Ctrl+C

# Kill all Python watchers
pkill -f gmail_watcher
```

## Troubleshooting

### "ImportError: No module named google"

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### "Token expired"

```bash
rm token.json
python scripts/gmail_watcher.py --authenticate
```

### "No emails detected"

1. Check Gmail API is enabled
2. Verify credentials have correct scopes
3. Check if emails are already processed (check state file)
4. Run with `--verbose` flag for detailed logs

## Example Workflow

### 1. Client Asks for Invoice

```
Email received: "Can you send the invoice?"
↓
Gmail Watcher creates: Needs_Action/EMAIL_invoice_request.md
↓
Orchestrator moves to: Pending_Approval/
↓
Human reviews and approves
↓
Claude generates invoice PDF
↓
Email MCP sends with attachment
↓
File moved to Done/
```

### 2. Lead Inquiry

```
Email received: "Interested in your services"
↓
Gmail Watcher creates: Needs_Action/EMAIL_lead_inquiry.md (priority: high)
↓
Alert sent to Dashboard
↓
Claude drafts response
↓
Human reviews and approves
↓
Email MCP sends response
↓
Follow-up reminder created
```

## API Reference

### Gmail Watcher Class

```python
class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path: str, credentials_path: str, check_interval: int = 120)
    def check_for_updates(self) -> List[Dict]
    def create_action_file(self, message: Dict) -> Path
    def authenticate(self) -> bool
    def mark_as_read(self, gmail_id: str) -> None
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--vault` | `./AI_Employee_Vault` | Path to Obsidian vault |
| `--interval` | `120` | Check interval in seconds |
| `--unread-only` | `False` | Only check unread emails |
| `--label` | `INBOX` | Gmail label/folder to monitor |
| `--dry-run` | `False` | Detect but don't create files |
| `--verbose` | `False` | Enable debug logging |

## Next Steps

After setting up Gmail Watcher:
1. Configure WhatsApp Watcher for multi-channel support
2. Set up Email MCP for sending replies
3. Implement Human-in-the-Loop approval workflow
4. Schedule with cron/Task Scheduler for 24/7 operation

---

*Gmail Watcher v0.1 - Silver Tier Component*
*Part of Personal AI Employee Hackathon*
