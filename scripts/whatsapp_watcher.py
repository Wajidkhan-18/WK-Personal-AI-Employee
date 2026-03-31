#!/usr/bin/env python3
"""
WhatsApp Watcher - Monitors WhatsApp Web for messages containing priority keywords.

This watcher uses Playwright to automate WhatsApp Web and detect messages
that require action. Creates action files in the Needs_Action folder.

WARNING: This may violate WhatsApp's Terms of Service. Use only for
business accounts you own. Consider official WhatsApp Business API for production.

Usage:
    python whatsapp_watcher.py
    python whatsapp_watcher.py --vault /path/to/vault
    python whatsapp_watcher.py --interval 60
    python whatsapp_watcher.py --no-headless
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


class WhatsAppWatcher(BaseWatcher):
    """
    Watcher that monitors WhatsApp Web for priority messages.
    
    When a message containing priority keywords is detected, this watcher:
    1. Extracts the message content
    2. Identifies the sender
    3. Creates an action file in Needs_Action
    4. Tracks processed messages to avoid duplicates
    """

    # Default keywords to detect
    DEFAULT_KEYWORDS = [
        'urgent', 'asap', 'immediate', 'priority',
        'invoice', 'payment', 'billing', 'money', 'price',
        'help', 'need', 'problem', 'issue',
        'meeting', 'call', 'today', 'tomorrow',
        'contract', 'agreement', 'deal', 'order'
    ]

    def __init__(self, vault_path: str, check_interval: int = 30,
                 keywords: Optional[List[str]] = None,
                 headless: bool = True,
                 session_path: Optional[str] = None):
        """
        Initialize the WhatsApp watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 30)
            keywords: List of keywords to detect (default: DEFAULT_KEYWORDS)
            headless: Run browser without UI (default: True)
            session_path: Path to store browser session (default: ~/.whatsapp_session/)
        """
        super().__init__(vault_path, check_interval)

        self.keywords = keywords or self.DEFAULT_KEYWORDS
        self.headless = headless
        self.session_path = Path(session_path) if session_path else Path.home() / '.whatsapp_session'
        self.session_path.mkdir(parents=True, exist_ok=True)

        # Track processed messages
        self.processed_messages: set = set()
        self._load_state()

        self.logger.info(f"Keywords to detect: {', '.join(self.keywords)}")
        self.logger.info(f"Headless mode: {self.headless}")
        self.logger.info(f"Session path: {self.session_path}")

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check WhatsApp Web for new messages.

        Returns:
            List of message dicts containing sender, text, timestamp
        """
        messages = []

        try:
            with sync_playwright() as p:
                # Launch browser with persistent context
                browser = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=self.headless,
                    args=['--disable-blink-features=AutomationControlled']
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Navigate to WhatsApp Web
                page.goto('https://web.whatsapp.com', wait_until='networkidle')

                # Wait for chat list to load
                try:
                    page.wait_for_selector('[data-testid="chat-list"]', timeout=30000)
                except Exception as e:
                    self.logger.warning(f"Chat list not found - may need to scan QR code: {e}")
                    browser.close()
                    return []

                # Find unread chats
                unread_chats = page.query_selector_all('[aria-label*="unread"]')

                for chat in unread_chats:
                    try:
                        # Extract chat info
                        chat_name = chat.query_selector('[dir="auto"]')
                        name = chat_name.inner_text() if chat_name else "Unknown"

                        # Get last message
                        last_message = chat.query_selector('span[title*="ago"]')
                        message_text = last_message.inner_text() if last_message else ""

                        # Check for keywords
                        message_lower = message_text.lower()
                        matched_keywords = [kw for kw in self.keywords if kw in message_lower]

                        if matched_keywords:
                            messages.append({
                                'chat_name': name,
                                'message': message_text,
                                'matched_keywords': matched_keywords,
                                'timestamp': datetime.now().isoformat(),
                                'is_group': 'group' in chat.get_attribute('aria-label').lower()
                            })

                    except Exception as e:
                        self.logger.error(f"Error extracting chat: {e}")

                browser.close()

                if messages:
                    self.logger.info(f"Found {len(messages)} priority message(s)")

                return messages

        except Exception as e:
            self.logger.error(f"Error checking WhatsApp: {e}")
            return []

    def _detect_priority(self, keywords: List[str]) -> str:
        """
        Detect priority level from matched keywords.

        Args:
            keywords: List of matched keywords

        Returns:
            Priority level: 'high', 'normal', or 'low'
        """
        high_priority = ['urgent', 'asap', 'immediate', 'emergency', 'help']
        billing_keywords = ['invoice', 'payment', 'billing', 'money', 'price']

        for kw in keywords:
            if kw.lower() in high_priority:
                return 'high'
            if kw.lower() in billing_keywords:
                return 'high'

        return 'normal'

    def create_action_file(self, message: Dict[str, Any]) -> Optional[Path]:
        """
        Create an action file for the WhatsApp message.

        Args:
            message: Message dict with chat_name, message, matched_keywords

        Returns:
            Path to created action file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = self.sanitize_filename(message['chat_name'][:30])

            # Detect priority
            priority = self._detect_priority(message['matched_keywords'])

            # Generate action file content
            frontmatter = self.generate_frontmatter(
                item_type="whatsapp",
                chat_name=f'"{message["chat_name"]}"',
                message_text=f'"{message["message"]}"',
                received=f'"{message["timestamp"]}"',
                priority=f'"{priority}"',
                keywords=f'{json.dumps(message["matched_keywords"])}',
                is_group=f'"{message.get("is_group", False)}"',
                status='"pending"'
            )

            # Build suggested actions
            actions = self._get_suggested_actions(message, priority)

            content = f'''{frontmatter}

## WhatsApp Message

**From:** {message["chat_name"]}
**Received:** {message["timestamp"]}
**Type:** {"Group" if message.get("is_group") else "Individual"}

---

{message["message"]}

---

## Suggested Actions

{chr(10).join([f"- [ ] {action}" for action in actions])}

## Context

- **Priority:** {priority.upper()}
- **Matched Keywords:** {', '.join(message["matched_keywords"])}
- **Message Type:** {"Group" if message.get("is_group") else "Individual"}

## Reply Draft

*Draft your reply here (requires approval before sending)*

---

## Notes

*Add any notes about this message below*

---

*Detected by WhatsAppWatcher at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
'''

            # Write action file
            action_filename = f"WHATSAPP_{timestamp}_{safe_name}.md"
            action_path = self.needs_action / action_filename
            action_path.write_text(content, encoding='utf-8')

            # Mark as processed
            msg_id = f"{message['chat_name']}:{message['timestamp']}"
            self.processed_messages.add(msg_id)
            self._save_state()

            self.logger.info(f"Created action file for: {message['chat_name']}")
            return action_path

        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            return None

    def _get_suggested_actions(self, message: Dict[str, Any], priority: str) -> List[str]:
        """
        Get suggested actions based on message content.

        Args:
            message: Message dict
            priority: Detected priority level

        Returns:
            List of suggested action strings
        """
        actions = [
            "Review message content",
            "Draft response (requires approval before sending)"
        ]

        # Add specific actions based on keywords
        keywords_lower = [kw.lower() for kw in message['matched_keywords']]

        if any(kw in keywords_lower for kw in ['invoice', 'payment', 'billing', 'price']):
            actions.extend([
                "Check accounting records",
                "Generate invoice or payment details",
                "Send payment information (requires approval)"
            ])

        if any(kw in keywords_lower for kw in ['urgent', 'asap', 'immediate', 'help']):
            actions.insert(0, "⚠️ HIGH PRIORITY - Respond within 1 hour")

        if any(kw in keywords_lower for kw in ['meeting', 'call', 'today', 'tomorrow']):
            actions.extend([
                "Check calendar availability",
                "Schedule meeting/call"
            ])

        if any(kw in keywords_lower for kw in ['contract', 'agreement', 'deal', 'order']):
            actions.extend([
                "Review terms",
                "Prepare documentation",
                "Flag for legal review if needed"
            ])

        return actions


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='WhatsApp Watcher for AI Employee')
    parser.add_argument('vault_path', nargs='?', default='AI_Employee_Vault',
                        help='Path to the Obsidian vault')
    parser.add_argument('--interval', '-i', type=int, default=30,
                        help='Check interval in seconds')
    parser.add_argument('--keywords', '-k', type=str,
                        help='Comma-separated keywords to detect')
    parser.add_argument('--no-headless', '-n', action='store_true',
                        help='Run browser with UI (for QR code scanning)')
    parser.add_argument('--session-path', '-s', type=str,
                        help='Path to store browser session')
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

    # Parse keywords
    keywords = None
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(',')]

    watcher = WhatsAppWatcher(
        str(vault_path),
        check_interval=args.interval,
        keywords=keywords,
        headless=not args.no_headless,
        session_path=args.session_path
    )

    print(f"💬 WhatsApp Watcher starting...")
    print(f"   Vault: {vault_path}")
    print(f"   Check interval: {args.interval}s")
    print(f"   Keywords: {', '.join(watcher.keywords)}")
    print(f"   Headless: {not args.no_headless}")

    if args.no_headless:
        print("\n📱 First run: Scan QR code with WhatsApp mobile app")
        print("   Session will be saved for future runs")

    # Run watcher
    watcher.run()


if __name__ == "__main__":
    main()
