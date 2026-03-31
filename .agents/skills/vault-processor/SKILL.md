---
name: vault-processor
description: |
  Process files in the AI Employee Obsidian vault. Read action files from
  Needs_Action folder, execute tasks, update Dashboard.md, and move completed
  items to Done. Use for processing file drops, emails, messages, and other
  actionable items in the vault.
---

# Vault Processor Skill

Process action files in the AI Employee Obsidian vault system.

## Usage

When Claude Code detects action files in the vault:

1. **Read** files from `/Needs_Action` folder
2. **Execute** the required actions based on file type
3. **Update** Dashboard.md with progress
4. **Move** completed files to `/Done` folder
5. **Log** all actions taken

## File Types

### file_drop

Files dropped into the Inbox for processing:

```markdown
---
type: file_drop
original_name: "document.pdf"
file_size: 1024000
priority: "normal"
---
```

**Actions:**
- Read and analyze file contents
- Categorize based on content
- Extract actionable information
- Move to appropriate folder or request clarification

### email

Email messages requiring action:

```markdown
---
type: email
from: "sender@example.com"
subject: "Meeting Request"
priority: "high"
---
```

**Actions:**
- Draft response following Company_Handbook.md rules
- Flag for human approval before sending
- Create follow-up reminders if needed

### whatsapp

WhatsApp messages requiring action:

```markdown
---
type: whatsapp
from: "+1234567890"
message: "Urgent: Need invoice"
priority: "high"
---
```

**Actions:**
- Analyze message for keywords (urgent, invoice, payment)
- Draft response
- Create action items
- Flag for approval if needed

## Workflow

### 1. Read Action Files

```bash
# List pending action files
ls Needs_Action/*.md
```

### 2. Process Each File

For each action file:
1. Read the frontmatter to understand type and priority
2. Read the content for details
3. Execute required actions
4. Update Dashboard.md
5. Move to Done when complete

### 3. Update Dashboard

After processing, update Dashboard.md:
- Increment task counters
- Add entries to Recent Activity
- Clear processed items from lists
- Update timestamp

### 4. Log Actions

Create log entry in `/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "2026-03-26T10:30:00Z",
  "action_type": "file_process",
  "file": "FILE_20260326_103000_document.md",
  "result": "success",
  "notes": "File categorized and moved to Projects folder"
}
```

## Example Session

```bash
# Process all pending action files
claude --prompt "Process all files in Needs_Action folder"

# Claude should:
# 1. Read each .md file
# 2. Understand the required action
# 3. Execute (file ops, analysis, drafting)
# 4. Update Dashboard.md
# 5. Move completed files to Done/
```

## Rules

Always follow Company_Handbook.md:
- Never send emails/messages without approval
- Flag payments > $100 for approval
- Log all actions
- Ask when uncertain

## Completion Signal

When all files are processed, output:

```
<promise>TASK_COMPLETE</promise>
```

This signals the Ralph Wiggum loop that processing is done.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| File already moved | Check if another process handled it |
| Missing permissions | Verify vault path is accessible |
| Claude not responding | Check claude --version |
| Dashboard not updating | Ensure write permissions |
