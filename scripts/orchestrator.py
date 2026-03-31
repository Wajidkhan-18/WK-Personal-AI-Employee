#!/usr/bin/env python3
"""
Orchestrator - Master process for the AI Employee.

The orchestrator:
1. Monitors the Needs_Action folder for pending items
2. Moves items to Pending_Approval for human review
3. After approval (moved to Approved), processes items
4. Moves completed items to Done folder
5. Updates the Dashboard.md with status

Workflow:
  Drop → Needs_Action → Pending_Approval → [User approves] → Approved → Done

Usage:
    python orchestrator.py /path/to/vault

For continuous operation:
    python orchestrator.py /path/to/vault --continuous
"""

import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import re
import json

from base_watcher import BaseWatcher


class Orchestrator:
    """
    Main orchestrator for the AI Employee system.

    Coordinates between watchers, AI assistants, and the vault.
    Implements approval workflow:
    - Files detected → Needs_Action
    - AI analyzes → Pending_Approval (for human review)
    - User moves to Approved → Execute
    - Complete → Done
    """

    def __init__(self, vault_path: str, check_interval: int = 30):
        """
        Initialize the orchestrator.

        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 30)
        """
        self.vault_path = Path(vault_path).absolute()
        self.check_interval = check_interval

        # Vault folders
        self.inbox = self.vault_path / 'Inbox'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.logs = self.vault_path / 'Logs'
        self.dashboard = self.vault_path / 'Dashboard.md'

        # Ensure all folders exist
        for folder in [self.inbox, self.needs_action, self.pending_approval, 
                       self.approved, self.done, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)

        # Set up logging
        self._setup_logging()

        # Track processed files
        self.processed_files: set = set()

        # Statistics
        self.stats = {
            'files_processed': 0,
            'tasks_completed': 0,
            'approvals_pending': 0,
            'errors': 0,
            'last_run': None
        }

        self.logger.info(f"Orchestrator initialized for vault: {self.vault_path}")
        self.logger.info("Workflow: Needs_Action -> Pending_Approval -> Approved -> Done")

    def _setup_logging(self):
        """Configure logging."""
        import logging

        log_file = self.logs / f'{datetime.now().strftime("%Y-%m-%d")}_orchestrator.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('Orchestrator')

    def get_pending_items(self, folder: str = 'needs_action') -> List[Path]:
        """
        Get all pending action files in a specific folder.

        Args:
            folder: Which folder to check ('needs_action', 'pending_approval', 'approved')

        Returns:
            List of paths to pending action files
        """
        pending = []
        folder_map = {
            'needs_action': self.needs_action,
            'pending_approval': self.pending_approval,
            'approved': self.approved
        }
        
        target_folder = folder_map.get(folder, self.needs_action)

        try:
            for filepath in target_folder.iterdir():
                if filepath.is_file() and filepath.suffix == '.md':
                    if filepath not in self.processed_files:
                        pending.append(filepath)
        except Exception as e:
            self.logger.error(f"Error scanning {folder}: {e}")

        return pending

    def analyze_action_file(self, action_file: Path) -> Dict[str, Any]:
        """
        Analyze an action file to determine type and priority.

        Args:
            action_file: Path to the action file

        Returns:
            Dictionary with analysis results
        """
        try:
            content = action_file.read_text(encoding='utf-8')

            analysis = {
                'type': 'unknown',
                'priority': 'normal',
                'requires_approval': False,
                'actions': []
            }

            # Parse frontmatter
            if '---' in content:
                frontmatter_end = content.find('---', 3)
                if frontmatter_end > 0:
                    frontmatter = content[4:frontmatter_end].strip()

                    # Extract type
                    if 'type:' in frontmatter:
                        match = re.search(r'type:\s*(\w+)', frontmatter)
                        if match:
                            analysis['type'] = match.group(1)

                    # Extract priority
                    if 'priority:' in frontmatter:
                        match = re.search(r'priority:\s*(\w+)', frontmatter)
                        if match:
                            analysis['priority'] = match.group(1)

            # Check if approval required based on content
            content_lower = content.lower()
            approval_keywords = ['payment', 'approve', 'authorization', 'transfer', 'invoice', 'send email']
            for keyword in approval_keywords:
                if keyword in content_lower:
                    analysis['requires_approval'] = True
                    break

            # Extract suggested actions
            action_matches = re.findall(r'- \[ \]\s*(.+)', content)
            analysis['actions'] = action_matches

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing action file: {e}")
            return {
                'type': 'unknown',
                'priority': 'normal',
                'requires_approval': False,
                'actions': [],
                'error': str(e)
            }

    def move_to_pending_approval(self, action_file: Path) -> Optional[Path]:
        """
        Move an action file from Needs_Action to Pending_Approval.

        Args:
            action_file: Path to the action file

        Returns:
            Path to the moved file, or None if failed
        """
        try:
            dest = self.pending_approval / action_file.name
            shutil.move(str(action_file), str(dest))
            self.logger.info(f"Moved to Pending_Approval: {action_file.name}")
            return dest
        except Exception as e:
            self.logger.error(f"Error moving to Pending_Approval: {e}")
            return None

    def move_to_approved(self, action_file: Path) -> Optional[Path]:
        """
        Move an approved file from Pending_Approval to Approved.

        Args:
            action_file: Path to the action file

        Returns:
            Path to the moved file, or None if failed
        """
        try:
            dest = self.approved / action_file.name
            shutil.move(str(action_file), str(dest))
            self.logger.info(f"Moved to Approved: {action_file.name}")
            return dest
        except Exception as e:
            self.logger.error(f"Error moving to Approved: {e}")
            return None

    def move_to_done(self, action_file: Path) -> Optional[Path]:
        """
        Move a completed action file to the Done folder.

        Args:
            action_file: Path to the action file to move

        Returns:
            Path to the moved file, or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = self.done / f"{timestamp}_{action_file.name}"
            shutil.move(str(action_file), str(dest))
            self.logger.info(f"Moved to Done: {action_file.name}")
            return dest
        except Exception as e:
            self.logger.error(f"Error moving file to Done: {e}")
            return None

    def sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as a filename."""
        invalid_chars = '<>:"/\\|？*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name[:100] if len(name) > 100 else name

    def prepare_for_ai_processing(self, action_files: List[Path]) -> bool:
        """
        Prepare action files for AI processing (Qwen Code or any AI assistant).

        This method marks files as ready for AI processing and creates a summary.

        Args:
            action_files: List of action files to process

        Returns:
            True if preparation was successful
        """
        if not action_files:
            return True

        self.logger.info(f"Prepared {len(action_files)} action file(s) for AI processing")

        # Build the list of files to process
        files_list = "\n".join([f"- `{f.name}`" for f in action_files])

        # Create a processing instruction file for the AI
        instruction = f"""# AI Employee - Action Files Ready for Processing

## Files to Process

{files_list}

## Instructions for AI Assistant

For each action file:
1. Read the file content and understand what needs to be done
2. Execute the required actions (file operations, analysis, etc.)
3. Update Dashboard.md with progress
4. When complete, move the action file to /Done folder
5. Log all actions taken

Follow the rules in Company_Handbook.md.

---
*Generated by Orchestrator at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

        try:
            # Write instruction file for AI to read
            instruction_file = self.vault_path / '_AI_PROCESSING_INSTRUCTIONS.md'
            instruction_file.write_text(instruction, encoding='utf-8')
            self.logger.info(f"Created processing instructions: {instruction_file}")

            # Mark files as ready
            for f in action_files:
                self.processed_files.add(f)
            self.stats['tasks_completed'] += len(action_files)
            return True

        except Exception as e:
            self.logger.error(f"Error preparing files: {e}")
            self.stats['errors'] += 1
            return False

    def update_dashboard(self):
        """Update the Dashboard.md with current status."""
        try:
            # Count items in each folder
            needs_action_count = len(list(self.needs_action.glob('*.md')))
            pending_approval_count = len(list(self.pending_approval.glob('*.md')))
            approved_count = len(list(self.approved.glob('*.md')))
            done_count = len(list(self.done.glob('*.md')))

            # Get today's date
            today = datetime.now().strftime("%Y-%m-%d")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Update status indicators
            needs_action_status = "✅ Clear" if needs_action_count == 0 else f"⚠️ {needs_action_count} need action"
            pending_approval_status = "✅ Clear" if pending_approval_count == 0 else f"🔔 {pending_approval_count} awaiting review"
            approved_status = "✅ Clear" if approved_count == 0 else f"✅ {approved_count} ready"

            # Get inbox summary
            inbox_items = list(self.inbox.glob('*'))
            if inbox_items:
                inbox_summary = "\n".join([f"- 📄 {f.name}" for f in inbox_items[:10]])
                if len(inbox_items) > 10:
                    inbox_summary += f"\n- ... and {len(inbox_items) - 10} more"
            else:
                inbox_summary = "*No new items*"

            # Get needs action summary
            needs_action_items = list(self.needs_action.glob('*.md'))
            if needs_action_items:
                needs_action_list = "\n".join([f"- ⏳ {f.name}" for f in needs_action_items[:10]])
            else:
                needs_action_list = "*No items requiring action*"

            # Get pending approvals
            pending_approval_items = list(self.pending_approval.glob('*.md'))
            if pending_approval_items:
                pending_approval_list = "\n".join([f"- 🔔 {f.name}" for f in pending_approval_items[:10]])
            else:
                pending_approval_list = "*No items awaiting approval*"

            # Get approved items
            approved_items = list(self.approved.glob('*.md'))
            if approved_items:
                approved_list = "\n".join([f"- ✅ {f.name}" for f in approved_items[:10]])
            else:
                approved_list = "*No items ready for execution*"

            # Alerts
            alerts = []
            if needs_action_count > 0:
                alerts.append(f"⚠️ {needs_action_count} item(s) need attention")
            if pending_approval_count > 0:
                alerts.append(f"🔔 {pending_approval_count} item(s) awaiting your review")
            if approved_count > 0:
                alerts.append(f"✅ {approved_count} item(s) approved and ready")
            if not alerts:
                alerts = ["✅ All systems operational"]
            alerts_text = "\n".join(alerts)

            # Build dashboard content (always regenerate, don't use template)
            content = f"""---
last_updated: {datetime.now().isoformat()}
status: active
tier: bronze_v0.1
---

# 📊 AI Employee Dashboard

## 🎯 Quick Status

| Metric | Value | Status |
|--------|-------|--------|
| Needs Action | {needs_action_count} | {needs_action_status} |
| Pending Approval | {pending_approval_count} | {pending_approval_status} |
| Approved (Ready) | {approved_count} | {approved_status} |
| Tasks Completed | {done_count} | - |

## 👁️ Active Watchers

| Watcher | Status | Last Check |
|---------|--------|------------|
| Filesystem | ✅ Ready | {timestamp} |

## 📥 Inbox Summary

{inbox_summary}

## ⏳ Needs Action

{needs_action_list}

## 🔔 Pending Approval (Awaiting Human Review)

{pending_approval_list}

## ✅ Approved (Ready for Execution)

{approved_list}

## 💰 Financial Snapshot

| Period | Revenue | Expenses | Net |
|--------|---------|----------|-----|
| This Week | $0 | $0 | $0 |
| This Month | $0 | $0 | $0 |

## 🚀 Active Projects

| Project | Status | Due Date | Progress |
|---------|--------|----------|----------|
| AI Employee Setup | In Progress | - | 100% |

## 📋 Recent Activity

| Timestamp | Action | Status |
|-----------|--------|--------|
| {timestamp} | Orchestrator cycle | ✅ |

## 🔔 Alerts

{alerts_text}

---

*Last generated: {today}*
*AI Employee v0.1 (Bronze Tier)*

## 📝 Workflow Status

Drop/ → Filesystem Watcher → Inbox/
       ↓
Needs_Action/ → Orchestrator → Pending_Approval/
       ↓
[User Review: Move to Approved/ or Reject]
       ↓
Approved/ → AI Processing → Done/

## 🤖 Bronze Tier Status

| Component | Status |
|-----------|--------|
| Filesystem Watcher | ✅ Working |
| Orchestrator | ✅ Working |
| Approval Workflow | ✅ Working |
| Dashboard | ✅ Updated |
| Qwen Code Integration | ✅ Ready |

---

*Processed by AI Employee at {timestamp}*
"""

            # Write updated dashboard
            self.dashboard.write_text(content, encoding='utf-8')
            self.logger.info("Dashboard updated")

        except Exception as e:
            self.logger.error(f"Error updating dashboard: {e}")

    def run_cycle(self):
        """Run one processing cycle."""
        self.logger.info("Starting processing cycle")

        # Step 1: Move items from Needs_Action to Pending_Approval
        needs_action_items = self.get_pending_items('needs_action')
        if needs_action_items:
            self.logger.info(f"Found {len(needs_action_items)} item(s) in Needs_Action")
            for item in needs_action_items:
                self.move_to_pending_approval(item)

        # Step 2: Check for items user moved from Pending_Approval to Approved
        # (User approves by manually moving files to Approved folder)
        approved_items = self.get_pending_items('approved')
        if approved_items:
            self.logger.info(f"Found {len(approved_items)} approved item(s) ready for processing")
            # Prepare for AI processing
            success = self.prepare_for_ai_processing(approved_items)
            if success:
                self.logger.info("Approved files ready for AI processing")

        # Update dashboard
        self.update_dashboard()

        self.stats['last_run'] = datetime.now()
        self.logger.info("Cycle complete")

    def run_continuous(self):
        """Run continuously with specified interval."""
        self.logger.info(f"Starting continuous mode (interval: {self.check_interval}s)")

        try:
            while True:
                self.run_cycle()
                import time
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info("Stopping orchestrator")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <vault_path> [--continuous] [--interval <seconds>]")
        sys.exit(1)

    vault_path = sys.argv[1]
    continuous = '--continuous' in sys.argv

    # Parse interval
    interval = 30
    if '--interval' in sys.argv:
        try:
            idx = sys.argv.index('--interval')
            interval = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            pass

    orchestrator = Orchestrator(vault_path, check_interval=interval)

    if continuous:
        orchestrator.run_continuous()
    else:
        orchestrator.run_cycle()


if __name__ == '__main__':
    main()
