#!/usr/bin/env python3
"""
Weekly Audit - Generate weekly business audit and CEO briefing.

This script analyzes the past week's activities:
- Completed tasks from Done/ folder
- Financial transactions from Accounting/
- Communication patterns from Gmail/WhatsApp logs
- Social media posts from LinkedIn

Generates a comprehensive CEO Briefing in Obsidian.

Usage:
    python weekly_audit.py /path/to/vault
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any


class WeeklyAudit:
    """Generate weekly business audit."""

    def __init__(self, vault_path: str):
        """
        Initialize weekly audit.

        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = Path(vault_path).absolute()
        self.done_folder = self.vault_path / 'Done'
        self.accounting_folder = self.vault_path / 'Accounting'
        self.logs_folder = self.vault_path / 'Logs'
        self.briefings_folder = self.vault_path / 'Briefings'
        self.business_goals = self.vault_path / 'Business_Goals.md'

        # Ensure briefings folder exists
        self.briefings_folder.mkdir(parents=True, exist_ok=True)

        # Calculate date range (last 7 days)
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=7)

        print(f"📊 Weekly Audit")
        print(f"   Vault: {self.vault_path}")
        print(f"   Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")

    def run(self) -> Path:
        """
        Run weekly audit and generate briefing.

        Returns:
            Path to generated briefing file
        """
        print("\n🔍 Starting weekly audit...")

        # Collect data
        completed_tasks = self._analyze_completed_tasks()
        financial_summary = self._analyze_finances()
        communication_summary = self._analyze_communications()
        subscription_audit = self._audit_subscriptions()

        # Generate briefing
        briefing_path = self._generate_briefing(
            completed_tasks=completed_tasks,
            financial_summary=financial_summary,
            communication_summary=communication_summary,
            subscription_audit=subscription_audit
        )

        print(f"\n✅ Weekly audit complete!")
        print(f"   Briefing saved to: {briefing_path}")
        return briefing_path

    def _analyze_completed_tasks(self) -> Dict[str, Any]:
        """Analyze completed tasks from Done/ folder."""
        print("\n📋 Analyzing completed tasks...")

        tasks = []
        if self.done_folder.exists():
            for file in self.done_folder.glob('*.md'):
                # Get file modification time
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if self.start_date <= mtime <= self.end_date:
                    tasks.append({
                        'file': file.name,
                        'completed': mtime,
                        'type': self._extract_task_type(file)
                    })

        print(f"   Found {len(tasks)} completed tasks")
        return {
            'count': len(tasks),
            'tasks': tasks,
            'by_type': self._group_by_type(tasks)
        }

    def _extract_task_type(self, filepath: Path) -> str:
        """Extract task type from filename."""
        name = filepath.stem.lower()
        if 'email' in name:
            return 'email'
        elif 'whatsapp' in name:
            return 'whatsapp'
        elif 'file' in name:
            return 'file'
        elif 'invoice' in name or 'payment' in name:
            return 'financial'
        elif 'linkedin' in name:
            return 'social'
        else:
            return 'other'

    def _group_by_type(self, tasks: List[Dict]) -> Dict[str, int]:
        """Group tasks by type."""
        groups = {}
        for task in tasks:
            task_type = task['type']
            groups[task_type] = groups.get(task_type, 0) + 1
        return groups

    def _analyze_finances(self) -> Dict[str, Any]:
        """Analyze financial transactions."""
        print("\n💰 Analyzing finances...")

        revenue = 0.0
        expenses = 0.0
        transactions = []

        # Look for transaction logs
        if self.accounting_folder.exists():
            for file in self.accounting_folder.glob('*.md'):
                content = file.read_text()
                # Simple parsing - look for amounts
                if 'revenue' in content.lower() or 'income' in content.lower():
                    revenue += self._extract_amounts(content)
                elif 'expense' in content.lower() or 'payment' in content.lower():
                    expenses += self._extract_amounts(content)

        print(f"   Revenue: ${revenue:.2f}")
        print(f"   Expenses: ${expenses:.2f}")

        return {
            'revenue': revenue,
            'expenses': expenses,
            'net': revenue - expenses,
            'transactions': transactions
        }

    def _extract_amounts(self, content: str) -> float:
        """Extract dollar amounts from content."""
        import re
        amounts = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', content)
        total = 0.0
        for amount in amounts:
            try:
                total += float(amount.replace(',', ''))
            except:
                pass
        return total

    def _analyze_communications(self) -> Dict[str, Any]:
        """Analyze communication patterns."""
        print("\n📧 Analyzing communications...")

        emails = 0
        messages = 0

        # Count email logs
        if self.logs_folder.exists():
            for log_file in self.logs_folder.glob('*GmailWatcher.log'):
                content = log_file.read_text()
                emails += content.count('Created action file')

            for log_file in self.logs_folder.glob('*WhatsAppWatcher.log'):
                content = log_file.read_text()
                messages += content.count('Created action file')

        print(f"   Emails processed: {emails}")
        print(f"   Messages processed: {messages}")

        return {
            'emails': emails,
            'messages': messages,
            'total': emails + messages
        }

    def _audit_subscriptions(self) -> List[Dict[str, Any]]:
        """Audit subscriptions for cost optimization."""
        print("\n🔄 Auditing subscriptions...")

        # This would integrate with actual subscription tracking
        # For now, return placeholder
        return [
            {
                'name': 'Example SaaS',
                'cost': 29.99,
                'last_used': '2026-03-25',
                'status': 'active',
                'recommendation': 'Keep - recently used'
            }
        ]

    def _generate_briefing(self, **kwargs) -> Path:
        """Generate CEO briefing document."""
        print("\n📝 Generating CEO Briefing...")

        completed_tasks = kwargs['completed_tasks']
        financial_summary = kwargs['financial_summary']
        communication_summary = kwargs['communication_summary']
        subscription_audit = kwargs['subscription_audit']

        # Calculate metrics
        net_revenue = financial_summary['net']
        total_tasks = completed_tasks['count']
        total_communications = communication_summary['total']

        # Determine tone based on performance
        if net_revenue > 0:
            tone = "positive"
            tone_text = "Strong performance with positive revenue."
        elif net_revenue == 0:
            tone = "neutral"
            tone_text = "Steady operations, focus on growth."
        else:
            tone = "cautious"
            tone_text = "Review expenses and identify optimization opportunities."

        # Generate content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        week_number = self.end_date.isocalendar()[1]

        content = f'''---
generated: {datetime.now().isoformat()}
period_start: {self.start_date.strftime("%Y-%m-%d")}
period_end: {self.end_date.strftime("%Y-%m-%d")}
week_number: {week_number}
status: draft
---

# Monday Morning CEO Briefing

**Week {week_number}, 2026**  
**Generated:** {timestamp}

---

## Executive Summary

{tone_text}

| Metric | Value | Status |
|--------|-------|--------|
| Revenue | ${financial_summary['revenue']:.2f} | {"✅" if financial_summary['revenue'] > 0 else "⚠️"} |
| Expenses | ${financial_summary['expenses']:.2f} | {"✅" if financial_summary['expenses'] < financial_summary['revenue'] else "⚠️"} |
| Net | ${net_revenue:.2f} | {"✅" if net_revenue >= 0 else "🔴"} |
| Tasks Completed | {total_tasks} | {"✅" if total_tasks > 0 else "⚠️"} |
| Communications | {total_communications} | {"✅" if total_communications > 0 else "⚠️"} |

---

## Revenue Analysis

### This Week
- **Total Revenue:** ${financial_summary['revenue']:.2f}
- **Total Expenses:** ${financial_summary['expenses']:.2f}
- **Net Profit:** ${net_revenue:.2f}

### Trends
*Add revenue trend analysis here*

---

## Completed Tasks

**Total:** {total_tasks} tasks completed this week

### By Category
'''

        # Add task breakdown
        for task_type, count in completed_tasks['by_type'].items():
            content += f"- **{task_type.title()}:** {count}\n"

        content += f'''
### Notable Completions
*Add highlights from completed tasks*

---

## Communications

### Volume
- **Emails Processed:** {communication_summary['emails']}
- **Messages Processed:** {communication_summary['messages']}
- **Total:** {total_communications}

### Response Time
*Add response time metrics here*

### Pending Responses
*List items awaiting response*

---

## Subscription Audit

| Service | Cost | Last Used | Status | Recommendation |
|---------|------|-----------|--------|----------------|
'''

        for sub in subscription_audit:
            content += f"| {sub['name']} | ${sub['cost']:.2f} | {sub['last_used']} | {sub['status']} | {sub['recommendation']} |\n"

        content += f'''
---

## Bottlenecks Identified

| Issue | Impact | Suggested Action |
|-------|--------|------------------|
| *Add bottlenecks here* | - | - |

---

## Proactive Suggestions

### Cost Optimization
*Add cost-saving recommendations*

### Revenue Opportunities
*Add revenue-generating suggestions*

### Process Improvements
*Add efficiency recommendations*

---

## Upcoming Deadlines

| Deadline | Type | Days Remaining |
|----------|------|----------------|
| *Add deadlines here* | - | - |

---

## Action Items for CEO

- [ ] Review revenue report
- [ ] Approve pending payments in /Pending_Approval
- [ ] Review subscription recommendations
- [ ] Address identified bottlenecks

---

*Generated by AI Employee v0.1 (Silver Tier)*  
*Next briefing: {(self.end_date + timedelta(days=7)).strftime("%Y-%m-%d")}*
'''

        # Write briefing
        filename = f"Weekly_Briefing_{week_number}_2026.md"
        briefing_path = self.briefings_folder / filename
        briefing_path.write_text(content, encoding='utf-8')

        return briefing_path


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python weekly_audit.py /path/to/vault")
        sys.exit(1)

    vault_path = sys.argv[1]
    vault_path = Path(vault_path).absolute()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    audit = WeeklyAudit(str(vault_path))
    audit.run()


if __name__ == '__main__':
    main()
