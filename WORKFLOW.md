# 🔄 AI Employee - Complete Workflow

## The Proper Flow (As Per Hackathon Document)

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLETE WORKFLOW                            │
└─────────────────────────────────────────────────────────────────┘

1. DROP FILE
   Inbox/ or Drop/
   │
   ▼
2. FILESYSTEM WATCHER (Python)
   Detects file → Creates action file
   │
   ▼
3. NEEDS_ACTION/
   Action file waiting for processing
   │
   ▼
4. ORCHESTRATOR (Python)
   Prepares files for AI processing
   │
   ▼
5. QWEN CODE (AI)
   Reads action files → Creates PLAN
   │
   ▼
6. PLANS/
   Plan created with recommended actions
   │
   ▼
7. PENDING_APPROVAL/
   Plan moved here for YOUR approval
   │
   ▼
8. 👈 HUMAN APPROVAL (YOU)
   Review plan → Approve or Reject
   │
   ├─────▶ If Approved: Move to Approved/
   │         │
   │         ▼
   │     Execute plan
   │         │
   │         ▼
   │     Move to Done/ ✅
   │
   └─────▶ If Rejected: Move to Rejected/
             │
             ▼
         Revise or Cancel ❌

```

---

## 📋 Current State (Live Example)

### Files in System Right Now:

| Location | Files | Status |
|----------|-------|--------|
| `Inbox/` | test.txt, new_test.txt | ✅ Original files |
| `Needs_Action/` | FILE_*.md (2 files) | ⏳ Action files |
| `Plans/` | - | (plan was here) |
| `Pending_Approval/` | PLAN_20260327_010000_test_files.md | 🔔 **AWAITING YOUR APPROVAL** |
| `Approved/` | - | (empty) |
| `Done/` | - | (empty) |

---

## 🎯 YOUR Turn: Approve the Plan

### What You Need to Do:

1. **Open Obsidian**
2. **Navigate to:** `Pending_Approval/PLAN_20260327_010000_test_files.md`
3. **Read the plan** - It contains:
   - Analysis of both test files
   - Recommended actions (categorize as Test Data)
   - Suggested folder (Archive/Test/)

4. **Make a decision:**

   **✅ To Approve:**
   ```
   Move file from: Pending_Approval/PLAN_*.md
   Move file to:   Approved/PLAN_*.md
   ```

   **❌ To Reject:**
   ```
   Move file from: Pending_Approval/PLAN_*.md
   Move file to:   Rejected/PLAN_*.md
   ```

   **✏️ To Modify:**
   ```
   1. Edit the plan in Obsidian
   2. Change the recommended actions
   3. Save the file
   4. Then approve or reject
   ```

---

## 📖 Step-by-Step Workflow

### Step 1: Drop File

```bash
# You create a file
echo "Meeting notes" > AI_Employee_Vault\Inbox\meeting.txt
```

### Step 2: Watcher Detects

```bash
# Start the watcher (runs continuously)
python scripts\filesystem_watcher.py AI_Employee_Vault --interval 2
```

**Output:**
```
✓ Found 1 new item(s)
✓ Created action file: FILE_20260327_120000_meeting.md
```

### Step 3: Orchestrator Prepares

```bash
python scripts\orchestrator.py AI_Employee_Vault
```

**Output:**
```
✓ Found 1 pending item(s)
✓ Prepared 1 action file(s) for AI processing
✓ Created processing instructions
```

### Step 4: Qwen Code Creates Plan

Qwen Code (me) reads the action files and creates a plan:

```markdown
---
type: plan
status: pending_approval
---

# Plan: Process Meeting Notes

## Steps
- [ ] Read meeting.txt
- [ ] Extract action items
- [ ] Create summary
- [ ] Move to Projects/ folder

## Approval Required
⚠️ Please approve before proceeding
```

### Step 5: Plan Moves to Pending_Approval

Plan is moved to `Pending_Approval/` folder

### Step 6: Human Reviews (YOU!)

**You open Obsidian and:**
- Read the plan
- Check if actions make sense
- Approve or reject

### Step 7: Execute Plan

**If Approved:**
```bash
# You move file to Approved/
move Pending_Approval\PLAN_*.md Approved\
```

**Qwen Code then:**
- Executes the plan
- Moves files as recommended
- Updates Dashboard
- Moves plan to Done/

**If Rejected:**
```bash
# You move file to Rejected/
move Pending_Approval\PLAN_*.md Rejected\
```

---

## ✅ Complete Example

### Test Files Workflow (Current)

```
1. You dropped: test.txt → Inbox/
                new_test.txt → Inbox/

2. Watcher created: FILE_*.md → Needs_Action/

3. Orchestrator: Created _AI_PROCESSING_INSTRUCTIONS.md

4. Qwen Code: 
   - Read files
   - Analyzed content
   - Created PLAN → Pending_Approval/

5. NOW: Waiting for YOUR approval! 👈

6. NEXT (after you approve):
   - Execute plan
   - Move files to Archive/Test/
   - Update Dashboard
   - Move to Done/
```

---

## 🎯 Why This Workflow?

### Benefits:

| Step | Purpose |
|------|---------|
| **Needs_Action** | Centralized queue for all pending work |
| **Plans** | AI thinks before acting - creates structured plan |
| **Pending_Approval** | Human-in-the-loop - you control what happens |
| **Approved** | Clear signal: "Go ahead" |
| **Done** | Audit trail - see what was completed |

### Safety:

- AI **never** acts without approval on sensitive actions
- You **always** see the plan before execution
- Files **never** deleted without your OK
- Full **audit trail** in Done/ folder

---

## 📊 Folder Purpose Summary

| Folder | Purpose | Who Writes |
|--------|---------|------------|
| `Inbox/` | Drop zone for new files | You / Watcher |
| `Drop/` | Automated drop zone | You / External |
| `Needs_Action/` | Pending action files | Watcher |
| `Plans/` | AI-created plans | Qwen Code |
| `Pending_Approval/` | Awaiting your decision | Qwen Code |
| `Approved/` | Ready to execute | You |
| `Rejected/` | Declined actions | You |
| `Done/` | Completed actions | Qwen Code |
| `Logs/` | System logs | Python scripts |

---

## 🚀 Next Steps

### Right Now:

1. **Open Obsidian**
2. **Go to:** `Pending_Approval/PLAN_20260327_010000_test_files.md`
3. **Read the plan**
4. **Approve or reject**

### After Approval:

Tell Qwen Code (me):

> "I approved the plan. Please execute it."

I will then:
- Execute the approved actions
- Move files as planned
- Update Dashboard
- Move everything to Done/

---

*Workflow Documentation - AI Employee v0.1 (Bronze Tier)*
*Created: 2026-03-27*
