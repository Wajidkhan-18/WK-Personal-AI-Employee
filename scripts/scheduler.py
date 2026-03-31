#!/usr/bin/env python3
"""
Scheduler - Task Scheduler for AI Employee.

This script integrates with system schedulers (cron on Linux/Mac,
Task Scheduler on Windows) to run periodic tasks:
- Daily briefings
- Weekly audits
- Periodic watcher health checks
- Scheduled post publishing

Usage:
    python scheduler.py install    # Install scheduled tasks
    python scheduler.py run        # Run all scheduled tasks now
    python scheduler.py status     # Show scheduled tasks
    python scheduler.py remove     # Remove scheduled tasks
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any


class AIScheduler:
    """Scheduler for AI Employee tasks."""

    def __init__(self, vault_path: str):
        """
        Initialize scheduler.

        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = Path(vault_path).absolute()
        self.scripts_dir = Path(__file__).parent
        self.logs_dir = self.vault_path / 'Logs'
        self.briefings_dir = self.vault_path / 'Briefings'

        # Ensure directories exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.briefings_dir.mkdir(parents=True, exist_ok=True)

        # Scheduled tasks configuration
        self.tasks = [
            {
                'name': 'daily_briefing',
                'description': 'Generate daily CEO briefing',
                'schedule': '08:00',  # 8 AM daily
                'command': f'python "{self.scripts_dir / "orchestrator.py"}" "{self.vault_path}"',
                'platform': 'all',
            },
            {
                'name': 'weekly_audit',
                'description': 'Weekly business audit',
                'schedule': 'Sunday 07:00',  # Sunday 7 AM
                'command': f'python "{self.scripts_dir / "weekly_audit.py"}" "{self.vault_path}"',
                'platform': 'all',
            },
            {
                'name': 'health_check',
                'description': 'Watcher health check',
                'schedule': '*/30 * * * *',  # Every 30 minutes
                'command': f'python "{self.scripts_dir / "health_check.py"}" "{self.vault_path}"',
                'platform': 'all',
            },
            {
                'name': 'linkedin_post',
                'description': 'Publish scheduled LinkedIn posts',
                'schedule': '09:00',  # 9 AM daily
                'command': f'python "{self.scripts_dir / "linkedin_poster.py"}" post --vault "{self.vault_path}"',
                'platform': 'all',
            },
        ]

        print(f"📅 AI Employee Scheduler")
        print(f"   Vault: {self.vault_path}")
        print(f"   Tasks configured: {len(self.tasks)}")

    def install(self) -> bool:
        """
        Install scheduled tasks based on platform.

        Returns:
            True if installation successful
        """
        platform = sys.platform

        if platform == 'win32':
            return self._install_windows()
        elif platform == 'darwin':
            return self._install_macos()
        else:
            return self._install_linux()

    def _install_windows(self) -> bool:
        """Install tasks using Windows Task Scheduler."""
        print("\n🪟 Installing Windows Task Scheduler tasks...")

        try:
            for task in self.tasks:
                task_name = f"AI_Employee_{task['name']}"
                
                # Create PowerShell command to create scheduled task
                ps_command = f'''
$action = New-ScheduledTaskAction -Execute "python" -Argument "{task['command'].split('python ')[1]}"
$trigger = New-ScheduledTaskTrigger -Daily -At {task['schedule'].split(':')[0]}:{task['schedule'].split(':')[1]}
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest
Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
                '''.strip()

                result = subprocess.run(
                    ['powershell', '-Command', ps_command],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    print(f"  ✓ Installed: {task_name}")
                else:
                    print(f"  ✗ Failed: {task_name} - {result.stderr}")

            print("\n✅ Windows Task Scheduler installation complete!")
            print("   Run 'schtasks /query | findstr AI_Employee' to verify")
            return True

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    def _install_macos(self) -> bool:
        """Install tasks using launchd (macOS)."""
        print("\n🍎 Installing launchd agents (macOS)...")

        try:
            launchd_dir = Path.home() / 'Library' / 'LaunchAgents'
            launchd_dir.mkdir(parents=True, exist_ok=True)

            for task in self.tasks:
                if task['name'] == 'health_check':
                    # Skip cron-style tasks for launchd
                    continue

                task_name = f"com.aiemployee.{task['name']}"
                plist_file = launchd_dir / f"{task_name}.plist"

                # Parse time
                hour, minute = map(int, task['schedule'].split(':'))

                # Create launchd plist
                plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{task_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{task['command'].split('python ')[1].split()[0]}</string>
        <string>{self.vault_path}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Minute</key>
        <integer>{minute}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{self.logs_dir / f'{task["name"]}.log'}</string>
    <key>StandardErrorPath</key>
    <string>{self.logs_dir / f'{task["name"]}_error.log'}</string>
</dict>
</plist>
'''
                plist_file.write_text(plist_content)

                # Load the agent
                subprocess.run(['launchctl', 'load', '-w', str(plist_file)], check=True)
                print(f"  ✓ Installed: {task_name}")

            print("\n✅ launchd installation complete!")
            print("   Run 'launchctl list | grep aiemployee' to verify")
            return True

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    def _install_linux(self) -> bool:
        """Install tasks using cron (Linux)."""
        print("\n🐧 Installing cron jobs (Linux)...")

        try:
            # Get current crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_crontab = result.stdout if result.returncode == 0 else ''

            # Add AI Employee tasks
            new_entries = []
            for task in self.tasks:
                schedule = task['schedule']
                command = f"{task['command']} >> {self.logs_dir / f'{task['name']}.log'} 2>&1"
                comment = f"# AI Employee: {task['description']}"
                new_entries.append(f"{comment}\n{schedule} {command}")

            # Combine with existing crontab
            # Remove old AI Employee entries first
            lines = [l for l in current_crontab.split('\n') if 'AI Employee' not in l]
            new_crontab = '\n'.join(lines + new_entries)

            # Install new crontab
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)

            print("  ✓ Cron jobs installed")
            print("\n✅ Cron installation complete!")
            print("   Run 'crontab -l' to verify")
            return True

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False

    def remove(self) -> bool:
        """Remove scheduled tasks."""
        platform = sys.platform

        if platform == 'win32':
            return self._remove_windows()
        elif platform == 'darwin':
            return self._remove_macos()
        else:
            return self._remove_linux()

    def _remove_windows(self) -> bool:
        """Remove Windows scheduled tasks."""
        print("\n🪟 Removing Windows Task Scheduler tasks...")

        for task in self.tasks:
            task_name = f"AI_Employee_{task['name']}"
            subprocess.run(['schtasks', '/delete', '/tn', task_name, '/f'],
                          capture_output=True)
            print(f"  ✓ Removed: {task_name}")

        print("\n✅ All tasks removed!")
        return True

    def _remove_macos(self) -> bool:
        """Remove macOS launchd agents."""
        print("\n🍎 Removing launchd agents...")

        launchd_dir = Path.home() / 'Library' / 'LaunchAgents'

        for task in self.tasks:
            task_name = f"com.aiemployee.{task['name']}"
            plist_file = launchd_dir / f"{task_name}.plist"

            if plist_file.exists():
                subprocess.run(['launchctl', 'unload', '-w', str(plist_file)])
                plist_file.unlink()
                print(f"  ✓ Removed: {task_name}")

        print("\n✅ All agents removed!")
        return True

    def _remove_linux(self) -> bool:
        """Remove Linux cron jobs."""
        print("\n🐧 Removing cron jobs...")

        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_crontab = result.stdout if result.returncode == 0 else ''

        # Remove AI Employee entries
        lines = [l for l in current_crontab.split('\n') if 'AI Employee' not in l]
        new_crontab = '\n'.join(lines)

        if new_crontab.strip():
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
        else:
            subprocess.run(['crontab', '-r'])

        print("  ✓ Cron jobs removed")
        print("\n✅ All jobs removed!")
        return True

    def status(self):
        """Show status of scheduled tasks."""
        print("\n📅 Scheduled Tasks Status\n")
        print(f"{'Task':<20} {'Schedule':<20} {'Description':<30}")
        print("-" * 70)

        for task in self.tasks:
            print(f"{task['name']:<20} {task['schedule']:<20} {task['description']:<30}")

        print("\nPlatform:", sys.platform)
        if sys.platform == 'win32':
            print("Use 'schtasks /query | findstr AI_Employee' to see Windows tasks")
        elif sys.platform == 'darwin':
            print("Use 'launchctl list | grep aiemployee' to see macOS agents")
        else:
            print("Use 'crontab -l' to see Linux cron jobs")

    def run_now(self, task_name: str = None):
        """
        Run scheduled tasks immediately.

        Args:
            task_name: Specific task to run, or None for all
        """
        tasks_to_run = [t for t in self.tasks if t['name'] == task_name] if task_name else self.tasks

        for task in tasks_to_run:
            print(f"\n▶️ Running: {task['name']}")
            try:
                result = subprocess.run(
                    task['command'],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )

                if result.returncode == 0:
                    print(f"  ✓ Success: {task['name']}")
                else:
                    print(f"  ✗ Failed: {task['name']}")
                    print(f"    Error: {result.stderr}")

                # Log result
                self._log_task(task['name'], result.returncode == 0, result.stdout + result.stderr)

            except subprocess.TimeoutExpired:
                print(f"  ✗ Timeout: {task['name']}")
            except Exception as e:
                print(f"  ✗ Error: {task['name']} - {e}")

    def _log_task(self, task_name: str, success: bool, output: str):
        """Log task execution result."""
        log_file = self.logs_dir / f'scheduler_{datetime.now().strftime("%Y-%m-%d")}.json'

        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except:
                logs = []

        logs.append({
            'timestamp': datetime.now().isoformat(),
            'task': task_name,
            'success': success,
            'output': output[:1000]  # Truncate long outputs
        })

        log_file.write_text(json.dumps(logs, indent=2))


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='AI Employee Scheduler')
    parser.add_argument('command', choices=['install', 'run', 'status', 'remove'],
                       help='Command to execute')
    parser.add_argument('--vault', '-v', default='AI_Employee_Vault',
                       help='Path to Obsidian vault')
    parser.add_argument('--task', '-t', help='Specific task to run')

    args = parser.parse_args()

    vault_path = Path(args.vault).absolute()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    scheduler = AIScheduler(str(vault_path))

    if args.command == 'install':
        success = scheduler.install()
        sys.exit(0 if success else 1)

    elif args.command == 'remove':
        success = scheduler.remove()
        sys.exit(0 if success else 1)

    elif args.command == 'status':
        scheduler.status()

    elif args.command == 'run':
        scheduler.run_now(args.task)


if __name__ == '__main__':
    main()
