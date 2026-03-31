#!/usr/bin/env python3
"""
LinkedIn Watcher - Monitors LinkedIn for notifications and messages.

This watcher uses Playwright to automate LinkedIn and detect:
- New connection requests
- Messages
- Post engagement (likes, comments)
- Job alerts
- Mentions

Creates action files in the Needs_Action folder for Qwen Code to process.

WARNING: LinkedIn's ToS prohibits automated access. Use responsibly
for business accounts only. Consider LinkedIn Marketing API for production.

Usage:
    python linkedin_watcher.py
    python linkedin_watcher.py --vault /path/to/vault
    python linkedin_watcher.py --interval 180
    python linkedin_watcher.py --no-headless
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Try to import Playwright
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Run:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)

from base_watcher import BaseWatcher


class LinkedInWatcher(BaseWatcher):
    """
    Watcher that monitors LinkedIn for notifications and messages.
    
    When an important notification is detected, this watcher:
    1. Extracts the notification content
    2. Identifies the sender/type
    3. Creates an action file in Needs_Action
    4. Tracks processed notifications to avoid duplicates
    """

    # Notification types to monitor
    NOTIFICATION_TYPES = {
        'message': ['sent you a message', 'messaged you'],
        'connection': ['invited you to connect', 'wants to connect'],
        'engagement': ['liked your post', 'commented on', 'shared your post'],
        'mention': ['mentioned you', 'tagged you'],
        'job': ['job you may be interested', 'hiring'],
    }

    def __init__(self, vault_path: str, check_interval: int = 300,
                 headless: bool = True,
                 session_path: Optional[str] = None):
        """
        Initialize the LinkedIn watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 300 = 5 min)
            headless: Run browser without UI (default: True)
            session_path: Path to store browser session
        """
        super().__init__(vault_path, check_interval)

        self.headless = headless
        self.session_path = Path(session_path) if session_path else Path.home() / '.linkedin_session'
        self.session_path.mkdir(parents=True, exist_ok=True)

        # Track processed notifications
        self.processed_ids: set = set()
        self._load_state()

        self.logger.info(f"Session path: {self.session_path}")
        self.logger.info(f"Headless mode: {self.headless}")
        self.logger.info(f"Check interval: {check_interval}s")

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check LinkedIn for new notifications.

        Returns:
            List of notification dicts
        """
        notifications = []

        try:
            with sync_playwright() as p:
                # Launch browser with persistent context
                # For first login (--no-headless), give user 5 minutes to log in
                browser = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=self.headless,
                    args=['--disable-blink-features=AutomationControlled'],
                    timeout=300000  # 5 minutes for first login
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Navigate to LinkedIn
                page.goto('https://www.linkedin.com', wait_until='networkidle', timeout=120000)

                # Wait for page to load - increased timeout for slow connections
                try:
                    page.wait_for_selector('.global-nav', timeout=120000)
                except Exception as e:
                    self.logger.warning(f"Navigation may have failed: {e}")
                    # Don't close immediately - let user finish login
                    page.wait_for_timeout(60000)  # Wait 1 more minute
                    browser.close()
                    return []

                # For first-time login, wait longer for user to complete login
                if not self.headless:
                    self.logger.info("Interactive mode: Waiting for user to log in (2 minutes)...")
                    page.wait_for_timeout(120000)  # Wait 2 minutes for user to log in
                else:
                    # Headless mode - just wait for dynamic content
                    page.wait_for_timeout(5000)

                # Check for notifications bell
                try:
                    notifications_icon = page.query_selector('.global-nav__me--notifications')
                    if notifications_icon:
                        count_text = notifications_icon.inner_text()
                        # Extract number from text like "99+"
                        import re
                        count_match = re.search(r'(\d+)', count_text)
                        if count_match:
                            count = int(count_match.group(1))
                            self.logger.info(f"Found {count} notification(s)")
                except Exception as e:
                    self.logger.debug(f"Could not check notification count: {e}")

                # Try to navigate to notifications page
                try:
                    page.goto('https://www.linkedin.com/notifications/', wait_until='networkidle')
                    page.wait_for_timeout(2000)

                    # Find notification items
                    notification_items = page.query_selector_all('li.notification-item')

                    for item in notification_items[:10]:  # Limit to 10
                        try:
                            # Extract notification data
                            title_elem = item.query_selector('.notification-item__title')
                            title = title_elem.inner_text() if title_elem else ''

                            link_elem = item.query_selector('a.notification-item__link')
                            link = link_elem.get_attribute('href') if link_elem else ''

                            time_elem = item.query_selector('time')
                            timestamp = time_elem.get_attribute('datetime') if time_elem else datetime.now().isoformat()

                            # Determine notification type
                            notif_type = self._classify_notification(title)

                            if notif_type and link:
                                notifications.append({
                                    'title': title,
                                    'link': f'https://www.linkedin.com{link}',
                                    'type': notif_type,
                                    'timestamp': timestamp,
                                    'id': f"{notif_type}:{timestamp}:{link}"
                                })
                        except Exception as e:
                            self.logger.debug(f"Error extracting notification: {e}")
                            continue

                except Exception as e:
                    self.logger.warning(f"Could not access notifications page: {e}")

                # Check for new messages
                try:
                    page.goto('https://www.linkedin.com/messaging/', wait_until='networkidle')
                    page.wait_for_timeout(2000)

                    # Find conversation items
                    conversations = page.query_selector_all('.msg-conversation-card')

                    for conv in conversations[:5]:  # Limit to 5
                        try:
                            name_elem = conv.query_selector('.msg-conversation-card__name')
                            name = name_elem.inner_text() if name_elem else 'Unknown'

                            last_msg_elem = conv.query_selector('.msg-conversation-card__last-message')
                            last_message = last_msg_elem.inner_text() if last_msg_elem else ''

                            time_elem = conv.query_selector('.msg-conversation-card__timestamp')
                            msg_time = time_elem.get_attribute('datetime') if time_elem else datetime.now().isoformat()

                            # Check if unread
                            is_unread = 'aria-label' in conv.get_attributes() and 'unread' in conv.get_attribute('aria-label').lower()

                            if is_unread and last_message:
                                notifications.append({
                                    'type': 'message',
                                    'from': name,
                                    'message': last_message,
                                    'timestamp': msg_time,
                                    'link': f'https://www.linkedin.com/messaging/',
                                    'id': f"message:{msg_time}:{name}"
                                })
                        except Exception as e:
                            self.logger.debug(f"Error extracting message: {e}")
                            continue

                except Exception as e:
                    self.logger.warning(f"Could not access messaging: {e}")

                browser.close()

                # Filter out already processed
                new_notifications = [n for n in notifications if n['id'] not in self.processed_ids]

                if new_notifications:
                    self.logger.info(f"Found {len(new_notifications)} new notification(s)")

                return new_notifications

        except Exception as e:
            self.logger.error(f"Error checking LinkedIn: {e}")
            return []

    def _classify_notification(self, title: str) -> Optional[str]:
        """
        Classify notification by type.

        Args:
            title: Notification title text

        Returns:
            Notification type string
        """
        title_lower = title.lower()

        for notif_type, keywords in self.NOTIFICATION_TYPES.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return notif_type

        return 'other'

    def _detect_priority(self, notif_type: str, content: str = '') -> str:
        """
        Detect priority level from notification.

        Args:
            notif_type: Notification type
            content: Notification content

        Returns:
            Priority level: 'high', 'normal', or 'low'
        """
        # Messages and connection requests are high priority
        if notif_type in ['message', 'connection']:
            return 'high'

        # Engagement is normal priority
        if notif_type == 'engagement':
            return 'normal'

        # Job alerts and mentions are normal/low
        if notif_type in ['job', 'mention']:
            return 'normal'

        return 'low'

    def _extract_sender_info(self, notification: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract sender information from notification.

        Args:
            notification: Notification dict

        Returns:
            Dict with sender info
        """
        if notification['type'] == 'message':
            return {
                'name': notification.get('from', 'Unknown'),
                'title': '',
                'company': ''
            }

        # For other types, would need to fetch profile page
        return {
            'name': 'Unknown',
            'title': '',
            'company': ''
        }

    def create_action_file(self, notification: Dict[str, Any]) -> Optional[Path]:
        """
        Create an action file for the LinkedIn notification.

        Args:
            notification: Notification dict

        Returns:
            Path to created action file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_id = self.sanitize_filename(notification['id'][:50])

            # Detect priority
            priority = self._detect_priority(notification['type'])

            # Get sender info
            sender = self._extract_sender_info(notification)

            # Generate action file content
            frontmatter = self.generate_frontmatter(
                item_type="linkedin_notification",
                notification_type=f'"{notification["type"]}"',
                from_name=f'"{sender["name"]}"',
                received=f'"{notification["timestamp"]}"',
                priority=f'"{priority}"',
                status='"pending"',
                linkedin_url=f'"{notification.get("link", "")}"'
            )

            # Build suggested actions
            actions = self._get_suggested_actions(notification, priority)

            # Format content based on type
            if notification['type'] == 'message':
                content_text = f"**Message:** {notification.get('message', '')}\n"
            else:
                content_text = f"**Notification:** {notification.get('title', '')}\n"

            content = f'''{frontmatter}

## LinkedIn Notification

**Type:** {notification['type'].title()}
**From:** {sender['name']}
**Received:** {notification['timestamp']}
**URL:** {notification.get('link', 'N/A')}

---

{content_text}

## Suggested Actions

{chr(10).join([f"- [ ] {action}" for action in actions])}

## Context

- **Priority:** {priority.upper()}
- **Notification Type:** {notification['type']}
- **Requires Response:** {notification['type'] in ['message', 'connection']}

## Reply Draft

*Draft your response here (requires approval before sending)*

---

## Notes

*Add any notes about this notification below*

---

*Detected by LinkedInWatcher at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
'''

            # Write action file
            action_filename = f"LINKEDIN_{timestamp}_{safe_id}.md"
            action_path = self.needs_action / action_filename
            action_path.write_text(content, encoding='utf-8')

            # Mark as processed
            self.processed_ids.add(notification['id'])
            self._save_state()

            self.logger.info(f"Created action file for: {notification['type']} from {sender['name']}")
            return action_path

        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            return None

    def _get_suggested_actions(self, notification: Dict[str, Any], priority: str) -> List[str]:
        """
        Get suggested actions based on notification type.

        Args:
            notification: Notification dict
            priority: Detected priority level

        Returns:
            List of suggested action strings
        """
        notif_type = notification['type']

        base_actions = [
            "Review notification details",
        ]

        type_actions = {
            'message': [
                "Read full message",
                "Draft response (requires approval before sending)",
                "Check sender profile for context"
            ],
            'connection': [
                "Review sender profile",
                "Accept or decline connection request",
                "Send personalized welcome message (requires approval)"
            ],
            'engagement': [
                "View post engagement",
                "Thank person for engagement (optional)",
                "Track metrics for briefing"
            ],
            'mention': [
                "Review mention context",
                "Consider responding or sharing",
                "Check if requires action"
            ],
            'job': [
                "Review job details",
                "Save if interested",
                "Update career goals if relevant"
            ],
            'other': [
                "Review and categorize",
                "Take action if needed"
            ]
        }

        actions = base_actions + type_actions.get(notif_type, [])

        # Add urgency for high priority
        if priority == 'high':
            actions.insert(0, "⚠️ HIGH PRIORITY - Review within 2 hours")

        return actions


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='LinkedIn Watcher for AI Employee')
    parser.add_argument('vault_path', nargs='?', default='AI_Employee_Vault',
                        help='Path to the Obsidian vault')
    parser.add_argument('--interval', '-i', type=int, default=300,
                        help='Check interval in seconds (default: 300)')
    parser.add_argument('--no-headless', '-n', action='store_true',
                        help='Run browser with UI (for first login)')
    parser.add_argument('--session-path', '-s', type=str,
                        help='Path to store browser session')
    parser.add_argument('--dry-run', '-d', action='store_true',
                        help='Detect but don\'t create files')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    if not PLAYWRIGHT_AVAILABLE:
        print("Error: Playwright not installed")
        print("Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    vault_path = Path(args.vault_path).absolute()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    watcher = LinkedInWatcher(
        str(vault_path),
        check_interval=args.interval,
        headless=not args.no_headless,
        session_path=args.session_path
    )

    print(f"💼 LinkedIn Watcher starting...")
    print(f"   Vault: {vault_path}")
    print(f"   Check interval: {args.interval}s ({args.interval/60:.1f} min)")
    print(f"   Headless: {not args.no_headless}")

    if args.no_headless:
        print("\n📱 First run: Log in to LinkedIn in the browser")
        print("   Session will be saved for future runs")

    # Run watcher
    if args.dry_run:
        print("\n🔍 Dry run mode - detecting but not creating files")
        notifications = watcher.check_for_updates()
        print(f"\nFound {len(notifications)} new notification(s):")
        for n in notifications:
            print(f"  - [{n['type']}] {n.get('title', n.get('message', ''))[:60]}")
    else:
        watcher.run()


if __name__ == "__main__":
    main()
