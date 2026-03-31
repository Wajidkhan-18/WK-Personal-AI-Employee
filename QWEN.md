# Personal AI Employee Project

## Project Overview

This is a **hackathon project** for building a "Digital FTE" (Full-Time Equivalent) — an autonomous AI agent that manages personal and business affairs 24/7. The project uses **Qwen Code** as the reasoning engine and **Obsidian** (local Markdown) as the dashboard/memory system.

**Key Concept:** Transform AI from a chatbot into a proactive business partner that:
- Monitors communications (Gmail, WhatsApp, LinkedIn)
- Manages tasks and projects
- Handles accounting and bank transactions
- Posts to social media autonomously
- Generates "Monday Morning CEO Briefings" with revenue reports and bottleneck analysis

## Architecture

### Core Components

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Brain** | Qwen Code | Reasoning engine, task execution |
| **Memory/GUI** | Obsidian Vault | Dashboard, long-term memory, state management |
| **Senses** | Python Watchers | Monitor Gmail, WhatsApp, filesystems |
| **Hands** | MCP Servers | External actions (email, browser automation, payments) |

### Folder Structure

```
WK-Personal-AI-Employee/
├── .agents/skills/           # Agent skill definitions
│   └── browsing-with-playwright/
│       ├── SKILL.md          # Skill documentation
│       ├── scripts/          # MCP client & server helpers
│       └── references/       # Tool reference docs
├── .qwen/skills/             # Qwen skill configurations
├── skills-lock.json          # Skill version lock file
└── Personal AI Employee Hackathon 0_....md  # Full architectural blueprint
```

### Obsidian Vault Structure (Expected)

```
Vault/
├── Dashboard.md              # Real-time summary
├── Company_Handbook.md       # Rules of engagement
├── Business_Goals.md         # Q1/Q2 objectives
├── Inbox/                    # New items to process
├── Needs_Action/             # Items requiring attention
├── In_Progress/<agent>/      # Claimed tasks
├── Pending_Approval/         # Human-in-the-loop requests
├── Approved/                 # Approved actions
├── Done/                     # Completed tasks
└── Briefings/                # CEO briefings
```

## Technologies & Tools

- **Qwen Code**: Primary AI reasoning engine
- **Obsidian**: Knowledge base & dashboard (Markdown-based)
- **Python 3.13+**: Watcher scripts, orchestration
- **Node.js v24+**: MCP servers
- **Playwright MCP**: Browser automation (22 tools available)
- **Git**: Version control for vault sync

## Building and Running

### Prerequisites Setup

```bash
# 1. Install required software
# - Qwen Code (free)
# - Obsidian v1.10.6+
# - Python 3.13+
# - Node.js v24+ LTS
# - GitHub Desktop

# 2. Create Obsidian vault
# Name: AI_Employee_Vault

# 3. Verify Qwen Code works
qwen --version  # or your Qwen Code command

# 4. Set up UV Python project (recommended)
```

### Playwright MCP Server

```bash
# Start server (shared browser context for persistent state)
bash .agents/skills/browsing-with-playwright/scripts/start-server.sh
# Or manually:
npx @playwright/mcp@latest --port 8808 --shared-browser-context &

# Verify server is running
python3 .agents/skills/browsing-with-playwright/scripts/verify.py

# Stop server (closes browser first)
bash .agents/skills/browsing-with-playwright/scripts/stop-server.sh
```

### MCP Client Usage

```bash
# Navigate to URL
python3 scripts/mcp-client.py call -u http://localhost:8808 \
  -t browser_navigate -p '{"url": "https://example.com"}'

# Get page snapshot (accessibility tree)
python3 scripts/mcp-client.py call -u http://localhost:8808 \
  -t browser_snapshot -p '{}'

# Click element
python3 scripts/mcp-client.py call -u http://localhost:8808 \
  -t browser_click -p '{"element": "Submit", "ref": "e42"}'

# Type text
python3 scripts/mcp-client.py call -u http://localhost:8808 \
  -t browser_type -p '{"element": "Search", "ref": "e15", "text": "hello"}'
```

### Watcher Scripts (To Be Implemented)

```python
# Example: Gmail Watcher pattern
class GmailWatcher(BaseWatcher):
    def check_for_updates(self) -> list:
        # Monitor unread/important emails
        pass
    
    def create_action_file(self, message) -> Path:
        # Create .md file in Needs_Action/
        pass
```

## Development Tiers

### Bronze Tier (8-12 hours)
- [ ] Obsidian vault with Dashboard.md and Company_Handbook.md
- [ ] One working Watcher script
- [ ] Qwen Code reading/writing to vault
- [ ] Basic folder structure: /Inbox, /Needs_Action, /Done

### Silver Tier (20-30 hours)
- [ ] Multiple Watcher scripts (Gmail + WhatsApp + LinkedIn)
- [ ] Auto-post to LinkedIn for lead generation
- [ ] Plan.md creation with reasoning loop
- [ ] One working MCP server
- [ ] Human-in-the-loop approval workflow
- [ ] Basic scheduling (cron/Task Scheduler)

### Gold Tier (40+ hours)
- [ ] Full cross-domain integration
- [ ] Odoo accounting integration via MCP
- [ ] Facebook/Instagram/Twitter integration
- [ ] Weekly Business Audit + CEO Briefing
- [ ] Error recovery & audit logging
- [ ] Ralph Wiggum loop for autonomous completion

### Platinum Tier (60+ hours)
- [ ] Cloud deployment (24/7 always-on)
- [ ] Cloud/Local work-zone specialization
- [ ] Vault sync via Git/Syncthing
- [ ] Odoo on Cloud VM with HTTPS + backups
- [ ] A2A communication upgrade

## Key Patterns

### Ralph Wiggum Loop (Persistence)
Stop hook that keeps Qwen Code working until task completion:
```bash
# Start Ralph loop
/ralph-loop "Process all files in /Needs_Action" \
  --completion-promise "TASK_COMPLETE" \
  --max-iterations 10
```

### Human-in-the-Loop (HITL)
For sensitive actions, Qwen Code writes approval request:
```markdown
---
type: approval_request
action: payment
amount: 500.00
status: pending
---
## To Approve
Move this file to /Approved folder.
```

### Claim-by-Move Rule
First agent to move item from `/Needs_Action` to `/In_Progress/<agent>/` owns it.

## MCP Servers Reference

| Server | Capabilities | Use Case |
|--------|-------------|----------|
| filesystem | Read, write, list files | Vault operations (built-in) |
| email-mcp | Send, draft, search emails | Gmail integration |
| browser-mcp | Navigate, click, fill forms | Payment portals, web automation |
| calendar-mcp | Create, update events | Scheduling |

## Testing & Verification

```bash
# Verify Playwright MCP server
python3 .agents/skills/browsing-with-playwright/scripts/verify.py

# Expected output: ✓ Playwright MCP server running
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Element not found | Run `browser_snapshot` first to get current refs |
| Click fails | Try `browser_hover` first, then click |
| Server not responding | Stop and restart: `stop-server.sh && start-server.sh` |
| Task incomplete | Use Ralph Wiggum loop for multi-step tasks |

## Resources

- [Full Architecture Doc](./Personal%20AI%20Employee%20Hackathon%200_%20Building%20Autonomous%20FTEs%20in%202026.md)
- [Playwright Tools Reference](./.agents/skills/browsing-with-playwright/references/playwright-tools.md)
- [Qwen Code Documentation](https://github.com/QwenLM/Qwen)
- [Agent Skills Documentation](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

## Weekly Research Meeting

- **When:** Wednesdays at 10:00 PM
- **Zoom:** [Join Meeting](https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1)
- **YouTube:** [Panaversity Channel](https://www.youtube.com/@panaversity)
