---
name: linkedin-auto-post
description: |
  Automatically post business updates to LinkedIn for lead generation.
  Uses Playwright to automate LinkedIn posting with draft approval workflow.
  Creates scheduled posts and tracks engagement metrics.
---

# LinkedIn Auto-Post Skill

Automate LinkedIn posting for business lead generation.

## Prerequisites

```bash
# Install Playwright
pip install playwright
playwright install chromium

# Install LinkedIn API wrapper (optional, for API-based posting)
pip install linkedin-api
```

## Usage

### Create Post Draft

```bash
# Create a post draft file
python scripts/linkedin_poster.py create --content "Excited to announce our new AI Employee service!"

# Create post with hashtags
python scripts/linkedin_poster.py create --content "New milestone reached!" --hashtags "#AI #Automation"

# Schedule post for later
python scripts/linkedin_poster.py create --content "Weekly update" --schedule "2026-03-30T09:00:00"
```

### Post to LinkedIn

```bash
# Post with approval workflow (default)
python scripts/linkedin_poster.py post --vault /path/to/vault

# Direct post (no approval, use with caution)
python scripts/linkedin_poster.py post --no-approval

# Post specific file
python scripts/linkedin_poster.py post --file Needs_Action/LINKEDIN_post_001.md
```

### Run in Background

```bash
# Using PM2
pm2 start scripts/linkedin_poster.py --name linkedin-poster --interpreter python3 -- post --watch

# Check pending posts
python scripts/linkedin_poster.py status
```

## How It Works

### 1. Post Creation

The AI Employee creates post drafts based on:
- Business milestones from `Business_Goals.md`
- Completed tasks from `Done/` folder
- Weekly achievements
- Product updates

### 2. Draft File Format

```markdown
---
type: linkedin_post
created: 2026-03-30T14:30:00Z
status: draft
priority: normal
scheduled_for: null
hashtags: ["#AI", "#Automation", "#Business"]
character_count: 245
---

## Post Content

🚀 Excited to share a major milestone!

Our AI Employee system just completed its first autonomous business audit,
identifying $500 in cost savings and generating 3 new lead follow-ups.

This is the future of business automation - AI that doesn't just respond,
but proactively manages your business 24/7.

#AI #Automation #Business #Innovation

---

## Posting Details

- **Platform:** LinkedIn
- **Post Type:** Text + Hashtags
- **Character Count:** 245/3000
- **Best Time to Post:** Tuesday-Thursday, 9-11 AM

## Approval Required

⚠️ This post requires human approval before publishing.

**To Approve:** Move this file to `/Approved` folder
**To Reject:** Move this file to `/Rejected` folder
**To Edit:** Edit content above and save

---

*Created by AI Employee at 2026-03-30 14:30:00*
```

### 3. Approval Workflow

```
AI creates draft → Needs_Action/LINKEDIN_post_001.md
                          ↓
              Human reviews content
                          ↓
          ┌───────────────┴───────────────┐
          ↓                               ↓
    Move to Approved                  Move to Rejected
          ↓                               ↓
    Post to LinkedIn              Log rejection reason
          ↓
    Move to Done/
```

### 4. Auto-Post Triggers

The watcher can auto-generate posts for:

| Trigger | Example Post |
|---------|-------------|
| Task completed | "Just delivered [project] to happy client!" |
| Revenue milestone | "Reached $10K MRR! Thank you to our amazing clients." |
| New feature | "Introducing [feature] - now you can [benefit]!" |
| Weekly recap | "This week: 3 projects delivered, 2 new clients" |

## LinkedIn Automation (Playwright)

### Browser-Based Posting

```python
# Internal workflow
1. Navigate to linkedin.com
2. Wait for authentication (session persisted)
3. Click "Start a post"
4. Fill content in textarea
5. Add hashtags
6. Click "Post"
7. Verify post published
8. Screenshot for logs
```

### Session Management

```bash
# First login (interactive)
python scripts/linkedin_poster.py login

# Session stored in ~/.linkedin_session/
# Subsequent posts use saved session
```

## Content Guidelines

### Best Practices

- **Length:** 150-300 characters for engagement
- **Hashtags:** 3-5 relevant hashtags
- **Timing:** Tuesday-Thursday, 9-11 AM local time
- **Frequency:** Max 3 posts/day, 15 posts/week
- **Tone:** Professional but friendly

### Post Templates

```markdown
# Milestone Template
🎉 Milestone Alert!

[Brief description of achievement]

This wouldn't be possible without [thank relevant parties].

#Hashtag1 #Hashtag2

# Lesson Template
💡 Lesson Learned Today

[Share insight/tip]

[Explain relevance to audience]

#Hashtag1 #Hashtag2

# Client Win Template
✅ Client Win!

Helped [client type] achieve [result] using [solution].

The key was [insight].

#Hashtag1 #Hashtag2
```

## Integration with AI Employee

### Weekly Auto-Post Workflow

```
Every Friday at 5 PM:
1. Orchestrator scans Done/ folder
2. Counts completed tasks
3. Identifies notable achievements
4. Creates post draft in Needs_Action/
5. Moves to Pending_Approval/
6. Human approves Monday morning
7. Posts automatically at 9 AM
```

### Lead Generation Flow

```
LinkedIn Post Published
        ↓
Comments/Messages received
        ↓
WhatsApp/Gmail Watcher detects
        ↓
Creates: Needs_Action/LINKEDIN_lead_001.md
        ↓
AI drafts response
        ↓
Human approves → Send
```

## Error Handling

| Issue | Solution |
|-------|----------|
| Login failed | Clear session, run `login` command |
| Post failed | Check content length, special characters |
| Rate limited | Wait 24 hours, reduce posting frequency |
| Session expired | Re-run `login` command |

## Testing

```bash
# Test connection
python scripts/linkedin_poster.py test-connection

# Validate post content
python scripts/linkedin_poster.py validate --file Needs_Action/LINKEDIN_post_001.md

# Dry run (no actual post)
python scripts/linkedin_poster.py post --dry-run --file Needs_Action/LINKEDIN_post_001.md
```

## Analytics Tracking

```markdown
## Post Performance (Updated Weekly)

| Metric | Value |
|--------|-------|
| Impressions | 1,234 |
| Reactions | 45 |
| Comments | 12 |
| Clicks | 23 |
| Engagement Rate | 6.5% |

*Last updated: 2026-03-30*
```

## Security

### Credential Storage

- **NEVER** store LinkedIn password in vault
- Use browser session cookies
- Store session in `~/.linkedin_session/`
- Rotate session monthly

### Posting Limits

```python
# Built-in rate limiting
MAX_POSTS_PER_DAY = 3
MAX_POSTS_PER_WEEK = 15
MIN_INTERVAL_MINUTES = 30
```

## Example Workflow

### AI Generates Weekly Update Post

```
1. Orchestrator runs Friday 5 PM
   ↓
2. Scans Done/ folder: 8 tasks completed
   ↓
3. Identifies highlights:
   - Client A invoice paid ($2000)
   - Project B launched
   - New lead from referral
   ↓
4. Creates draft:
   "Great week! 8 projects completed, 
    including [highlights]. Grateful for 
    our amazing clients! #Business #Growth"
   ↓
5. Moves to Pending_Approval/
   ↓
6. Monday 8 AM: Human reviews, approves
   ↓
7. Monday 9 AM: Auto-posts to LinkedIn
   ↓
8. Logs engagement metrics
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--vault` | `./AI_Employee_Vault` | Path to Obsidian vault |
| `--schedule` | `null` | ISO datetime for scheduled post |
| `--hashtags` | (auto) | Comma-separated hashtags |
| `--no-approval` | `False` | Skip approval workflow |
| `--dry-run` | `False` | Validate but don't post |
| `--verbose` | `False` | Enable debug logging |

## Compliance

⚠️ **Important:** LinkedIn's Terms of Service prohibit automated posting.

- Use responsibly for business accounts
- Consider LinkedIn Marketing API for production
- Rate limit to avoid account restrictions
- Always maintain human oversight

## Troubleshooting

### "Cannot find feed element"

LinkedIn changed UI. Update selector in `linkedin_poster.py`.

### "Session expired"

```bash
python scripts/linkedin_poster.py login
```

### "Post too long"

LinkedIn allows 3000 characters. Trim content or split into thread.

---

*LinkedIn Auto-Post v0.1 - Silver Tier Component*
*Part of Personal AI Employee Hackathon*
