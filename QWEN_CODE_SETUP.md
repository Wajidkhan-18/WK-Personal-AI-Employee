# AI Employee with Qwen Code - Complete Setup

**This system is built specifically for Qwen Code as the AI reasoning engine.**

---

## 🎯 Overview

The AI Employee system uses **Qwen Code** for all AI processing tasks:
- Reading and analyzing action files
- Creating plans for complex tasks
- Processing emails and messages
- Generating responses
- Moving files between folders
- Updating the Dashboard

---

## 📦 Installation

### 1. Install Qwen Code

Follow the official Qwen Code installation guide:
- GitHub: https://github.com/QwenLM/Qwen
- Documentation: https://qwen.readthedocs.io/

### 2. Verify Installation

```bash
qwen --version
```

### 3. Configure for AI Employee

No special configuration needed! Qwen Code works with the file system directly.

---

## 🚀 Using Qwen Code with AI Employee

### Manual Processing

```bash
# Navigate to vault
cd AI_Employee_Vault

# Process all pending action files
qwen --prompt "Process all files in Needs_Action folder. Follow the Company_Handbook.md rules."

# Process with specific instructions
qwen --prompt "Review the email in Needs_Action/ and draft a response. Save the draft in the file."
```

### Continuous Processing (with Ralph Wiggum Loop)

For multi-step tasks that require iteration:

```bash
# Start Ralph loop for autonomous completion
/ralph-loop "Process all files in Needs_Action, move completed to Done" \
  --completion-promise "TASK_COMPLETE" \
  --max-iterations 10
```

### Common Qwen Code Commands

```bash
# Process a specific file
qwen --prompt "Read Needs_Action/EMAIL_*.md and create a draft response"

# Update dashboard
qwen --prompt "Update Dashboard.md with current status from all folders"

# Generate weekly briefing
qwen --prompt "Review Done/ folder and create a weekly summary in Briefings/"

# Process approval requests
qwen --prompt "Check Pending_Approval/ folder and summarize items awaiting approval"
```

---

## 📁 File Workflow with Qwen Code

```
1. Watcher detects new item (file, email, message)
   ↓
2. Creates action file in Needs_Action/
   ↓
3. Orchestrator analyzes and creates Plan.md (if complex)
   ↓
4. Qwen Code processes the action file:
   - Reads the content
   - Executes required actions
   - Documents progress
   ↓
5. Qwen Code moves file to Done/ when complete
   ↓
6. Dashboard.md is updated automatically
```

---

## 🔗 Qwen Code + MCP Servers

Qwen Code can use MCP servers for extended capabilities:

### Email MCP Server

```bash
# Start the email MCP server
node scripts/email-mcp-server.js --credentials scripts/credentials.json

# Qwen Code can now use:
# - send_email: Send emails (with approval)
# - create_draft_email: Create Gmail drafts
# - search_emails: Search Gmail
```

### Browser MCP Server (Playwright)

```bash
# Start Playwright MCP server
npx @playwright/mcp@latest --port 8808 --shared-browser-context

# Qwen Code can now:
# - Navigate websites
# - Fill forms
# - Click buttons
# - Take screenshots
```

---

## 📝 Example Qwen Code Prompts

### Email Processing

```
Read the email in Needs_Action/EMAIL_*.md and:
1. Summarize the sender's request
2. Draft a professional response
3. Save the draft in the same file
4. Move to Pending_Approval/ if action required
```

### File Processing

```
Process all files in Needs_Action/:
1. Read each file's content
2. Categorize by type (email, file_drop, message)
3. Execute the suggested actions
4. Move completed files to Done/
5. Update Dashboard.md with progress
```

### Plan Execution

```
Review the plan in Plans/PLAN_*.md:
1. Check each phase completion status
2. Execute pending actions
3. Document progress in the Execution Log section
4. Move to Done/ when all phases complete
```

### Weekly Briefing

```
Generate a weekly briefing:
1. Review all files in Done/ from this week
2. Count completed tasks by type
3. Check Accounting/ for revenue data
4. Create summary in Briefings/ folder
5. Include proactive suggestions
```

---

## 🛠️ Qwen Code Configuration

### System Prompt (Optional)

Create `.qwen/instructions.md` in your vault:

```markdown
# AI Employee Instructions

You are an AI Employee assistant. Follow these rules:

1. Always read Company_Handbook.md before processing
2. Check approval thresholds before any financial action
3. Document all actions taken in each file
4. Move files to appropriate folders after processing
5. Update Dashboard.md after each task
6. Ask for approval when uncertain
```

### Custom Commands

Create shortcuts for common tasks:

```bash
# Alias for processing
alias ai-process="cd AI_Employee_Vault && qwen --prompt 'Process Needs_Action/'"

# Alias for dashboard update
alias ai-dashboard="cd AI_Employee_Vault && qwen --prompt 'Update Dashboard.md'"
```

---

## 🧪 Testing Qwen Code Integration

### Test 1: Basic File Processing

```bash
# Create test file
echo "Test: Process this document" > AI_Employee_Vault/Drop/test.txt

# Run orchestrator
python scripts/orchestrator.py AI_Employee_Vault

# Process with Qwen Code
cd AI_Employee_Vault
qwen --prompt "Process the file in Needs_Action/"

# Check results
ls Done/
```

### Test 2: Plan Generation

```bash
# Create complex action file
cat > AI_Employee_Vault/Needs_Action/TEST_COMPLEX.md << EOF
---
type: complex_task
priority: high
---

## Task

Process this complex task.

## Actions

- [ ] Step 1: Analyze
- [ ] Step 2: Execute
- [ ] Step 3: Review
- [ ] Step 4: Document
EOF

# Run orchestrator (creates plan)
python scripts/orchestrator.py AI_Employee_Vault

# Check Plans/ folder
ls Plans/
```

### Test 3: Dashboard Update

```bash
# Process with Qwen Code
cd AI_Employee_Vault
qwen --prompt "Update Dashboard.md with current folder status"

# Check Dashboard.md in Obsidian
```

---

## 🆘 Troubleshooting

### "Qwen Code not found"

```bash
# Check installation
which qwen
qwen --version

# Reinstall if needed
# Follow https://github.com/QwenLM/Qwen installation guide
```

### "Qwen Code can't read files"

```bash
# Check file permissions
ls -la AI_Employee_Vault/

# Ensure you're in the correct directory
cd AI_Employee_Vault
pwd
```

### "Qwen Code makes wrong decisions"

1. Review Company_Handbook.md rules
2. Add more specific instructions in prompts
3. Use Human-in-the-Loop for sensitive actions
4. Check if action files have clear instructions

---

## 📚 Resources

- **Qwen Code Docs:** https://qwen.readthedocs.io/
- **Qwen GitHub:** https://github.com/QwenLM/Qwen
- **Agent Skills:** https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview

---

## 🎯 Next Steps

1. ✅ Install Qwen Code
2. ✅ Test basic file processing
3. ✅ Configure MCP servers (optional)
4. ✅ Set up continuous processing loop
5. ✅ Integrate with watchers

---

*Qwen Code Integration Guide - AI Employee v0.2 (Silver Tier)*
