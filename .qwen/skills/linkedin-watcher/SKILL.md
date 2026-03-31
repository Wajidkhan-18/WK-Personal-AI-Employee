---
name: linkedin-watcher
description: |
  Monitor LinkedIn for notifications, messages, and engagement.
  Uses Playwright to automate LinkedIn and detect important notifications
  such as connection requests, messages, and post engagement. Creates action
  files in the Needs_Action folder for Qwen Code to process.
---

# LinkedIn Watcher Skill

Monitor LinkedIn for business opportunities and engagement.

## Prerequisites

```bash
# Install Playwright
pip install playwright
playwright install chromium
```

## Usage

### Start LinkedIn Watcher

```bash
# Basic usage
python scripts/linkedin_watcher.py

# Custom vault path
python scripts/linkedin_watcher.py --vault /path/to/vault

# Custom check interval (default: 300 seconds)
python scripts/linkedin_watcher.py --interval 180

# Interactive mode (for first login)
python scripts/linkedin_watcher.py --no-headless
```

### Run in Background

```bash
# Using PM2 (recommended)
pm2 start scripts/linkedin_watcher.py --name linkedin-watcher --interpreter python3

# Using nohup
nohup python scripts/linkedin_watcher.py > logs/linkedin_watcher.log 2>&1 &
```

## How It Works

### 1. LinkedIn Automation

The watcher uses Playwright to:
- Launch Chromium with persistent session
- Navigate to linkedin.com
- Check for notifications
- Scan messages
- Monitor post engagement

### 2. Notification Types

| Type | Keywords | Action |
|------|----------|--------|
| **Connection Request** | "invited you to connect" | Review profile |
| **Message** | "sent you a message" | Draft response |
| **Post Engagement** | "liked your post", "commented" | Track metrics |
| **Job Alert** | "job you may be interested" | Save opportunity |
| **Mention** | "mentioned you" | Review context |

### 3. Action File Creation

For each important notification, creates:

```markdown
---
type: linkedin_notification
from: "John Doe"
notification_type: message
received: 2026-03-30T14:30:00Z
priority: high
status: pending
linkedin_url: "https://linkedin.com/in/johndoe"
---

## LinkedIn Message

**From:** John Doe
**Title:** CEO at TechCorp
**Received:** March 30, 2026 at 2:30 PM

---

Hi, I saw your post about AI automation and would love to discuss...

---

## Suggested Actions

- [ ] Review sender profile
- [ ] Draft response (requires approval)
- [ ] Check if lead opportunity
- [ ] Log in CRM

## Context

- **Notification Type:** Message
- **Priority:** HIGH (potential lead)
- **Connection Degree:** 2nd

---

*Detected by LinkedInWatcher at 2026-03-30 14:30:05*
```

## Session Management

### First-Time Setup

1. Run watcher in interactive mode:
```bash
python scripts/linkedin_watcher.py --no-headless
```

2. Log in with LinkedIn credentials

3. Session saved to `~/.linkedin_session/`

### Session Issues

```bash
# Clear session and re-authenticate
rm -rf ~/.linkedin_session
python scripts/linkedin_watcher.py --no-headless
```

## Security Considerations

⚠️ **Important:** LinkedIn automation may violate Terms of Service.

- Use only for business accounts you own
- Rate limit requests to avoid bans
- Never use for spam or unsolicited messages
- Consider LinkedIn Marketing API for production

## Error Handling

| Issue | Solution |
|-------|----------|
| Login page shows | Session expired, re-login |
| No notifications | Check if already processed |
| Browser crashes | Restart watcher |
| Rate limited | Increase check interval |

## Integration Flow

```
LinkedIn → Playwright → Notification Detection → Needs_Action/
                                                        ↓
                                              Orchestrator → Pending_Approval
                                                                      ↓
                                                              [Human approves]
                                                                      ↓
                                                              Approved/ → Response
```

## Testing

```bash
# Test connection (opens browser)
python scripts/linkedin_watcher.py --test-connection

# Dry run (detect but don't create files)
python scripts/linkedin_watcher.py --dry-run

# Verbose logging
python scripts/linkedin_watcher.py --verbose
```

## Logs

- `AI_Employee_Vault/Logs/YYYY-MM-DD_LinkedInWatcher.log`
- Console output (foreground mode)

## Troubleshooting

### "Playwright not installed"

```bash
pip install playwright
playwright install chromium
```

### "Session expired"

```bash
rm -rf ~/.linkedin_session
python scripts/linkedin_watcher.py --no-headless
```

### "No notifications detected"

- Check if notifications already processed
- Verify session is valid
- Run with `--verbose` for debug info

## Example Workflow

### Lead Inquiry via LinkedIn

```
Notification: "John Doe sent you a message"
↓
LinkedIn Watcher detects: new message
↓
Creates: Needs_Action/LINKEDIN_john_doe_message.md
↓
Orchestrator moves to: Pending_Approval/
↓
Dashboard shows: 🔔 1 item awaiting review
↓
Human reviews and approves
↓
Qwen Code drafts response
↓
Human approves response
↓
LinkedIn MCP sends message
↓
File moved to Done/
```

## API Reference

### LinkedIn Watcher Class

```python
class LinkedInWatcher(BaseWatcher):
    def __init__(self, vault_path: str, check_interval: int = 300,
                 headless: bool = True)
    def check_for_updates(self) -> List[Dict]
    def create_action_file(self, notification: Dict) -> Path
    def login(self) -> bool
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--vault` | `./AI_Employee_Vault` | Path to Obsidian vault |
| `--interval` | `300` | Check interval in seconds |
| `--no-headless` | `False` | Run browser with UI |
| `--dry-run` | `False` | Detect but don't create files |
| `--verbose` | `False` | Enable debug logging |

---

*LinkedIn Watcher v0.1 - Silver Tier Component*
*Part of Personal AI Employee Hackathon*
