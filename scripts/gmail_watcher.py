#!/usr/bin/env python3
"""
Gmail Watcher - Monitors Gmail for new and important emails.

This watcher uses the Gmail API to poll for new emails and creates
action files in the Needs_Action folder for Claude Code to process.

Features:
- OAuth2 authentication
- Priority detection based on keywords
- Duplicate prevention
- Attachment handling
- Email categorization

Usage:
    python gmail_watcher.py
    python gmail_watcher.py --vault /path/to/vault
    python gmail_watcher.py --interval 60
    python gmail_watcher.py --authenticate
"""

import sys
import os
import json
import base64
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from email.parser import BytesParser
from email.policy import default

# Try to import Google libraries
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("Gmail libraries not installed. Run:")
    print("  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

from base_watcher import BaseWatcher


class GmailWatcher(BaseWatcher):
    """
    Watcher that monitors Gmail for new emails.
    
    When a new email is detected, this watcher:
    1. Fetches the email content
    2. Detects priority and category
    3. Creates an action file in Needs_Action
    4. Tracks the Gmail ID to avoid duplicates
    """

    # Gmail API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify',
    ]

    # Priority keywords
    PRIORITY_KEYWORDS = {
        'high': ['urgent', 'asap', 'immediate', 'priority', 'important'],
        'billing': ['invoice', 'payment', 'bill', 'receipt', 'billing', 'account'],
        'meeting': ['meeting', 'call', 'schedule', 'zoom', 'teams', 'conference'],
        'lead': ['pricing', 'quote', 'interested', 'demo', 'proposal', 'services'],
        'support': ['help', 'issue', 'problem', 'bug', 'error', 'support'],
    }

    # Category keywords
    CATEGORY_KEYWORDS = {
        'billing': ['invoice', 'payment', 'bill', 'receipt', 'billing'],
        'meeting': ['meeting', 'call', 'schedule', 'zoom', 'teams', 'calendar'],
        'lead': ['pricing', 'quote', 'interested', 'demo', 'proposal', 'buy'],
        'support': ['help', 'issue', 'problem', 'bug', 'error', 'broken'],
        'newsletter': ['newsletter', 'digest', 'update', 'subscription'],
    }

    def __init__(self, vault_path: str, credentials_path: Optional[str] = None, 
                 check_interval: int = 120, unread_only: bool = True,
                 label: str = 'INBOX'):
        """
        Initialize the Gmail watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            credentials_path: Path to Gmail credentials.json
            check_interval: Seconds between checks (default: 120)
            unread_only: Only check unread emails (default: True)
            label: Gmail label/folder to monitor (default: INBOX)
        """
        super().__init__(vault_path, check_interval)

        # Set up credentials path
        if credentials_path:
            self.credentials_path = Path(credentials_path)
        else:
            # Default locations
            possible_paths = [
                Path('credentials.json'),
                Path.home() / '.config' / 'gmail' / 'credentials.json',
                Path(__file__).parent.parent / 'credentials.json',
            ]
            for path in possible_paths:
                if path.exists():
                    self.credentials_path = path
                    break
            else:
                self.credentials_path = Path('credentials.json')

        self.token_path = self.vault_path / '.gmail_token.json'
        self.unread_only = unread_only
        self.label = label

        # Initialize Gmail service
        self.service = None
        self._authenticate()

        # Track processed Gmail IDs
        self.processed_ids: set = set()
        self._load_state()

        self.logger.info(f"Monitoring label: {self.label}")
        self.logger.info(f"Unread only: {self.unread_only}")

    def _authenticate(self) -> bool:
        """
        Authenticate with Gmail API.

        Returns:
            True if authentication successful
        """
        try:
            creds = None

            # Load token if exists
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(
                    self.token_path, self.SCOPES
                )

            # Refresh or re-authenticate
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    self.logger.info("Refreshing expired token")
                    creds.refresh(Request())
                else:
                    self.logger.info("Starting new OAuth flow")
                    if not self.credentials_path.exists():
                        self.logger.error(
                            f"Credentials not found at {self.credentials_path}\n"
                            "Please download credentials.json from Google Cloud Console"
                        )
                        return False

                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=8080)

                # Save token
                self.token_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
                self.logger.info(f"Token saved to {self.token_path}")

            # Build service
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Gmail API authentication successful")
            return True

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False

    def _load_state(self):
        """Load processed Gmail IDs from state file."""
        super()._load_state()
        # Also track in processed_ids for backward compatibility
        self.processed_ids = self.processed_ids

    def _save_state(self):
        """Save processed Gmail IDs to state file."""
        super()._save_state()

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check Gmail for new emails.

        Returns:
            List of email message dicts
        """
        if not self.service:
            self.logger.error("Gmail service not initialized")
            return []

        try:
            # Build query
            query_parts = []
            if self.unread_only:
                query_parts.append('is:unread')
            query_parts.append(f'in:{self.label}')
            query = ' '.join(query_parts)

            # Fetch messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10
            ).execute()

            messages = results.get('messages', [])
            new_messages = []

            for msg in messages:
                msg_id = msg['id']
                if msg_id not in self.processed_ids:
                    # Fetch full message
                    full_msg = self.service.users().messages().get(
                        userId='me',
                        id=msg_id,
                        format='full'
                    ).execute()
                    new_messages.append(full_msg)

            self.logger.info(f"Found {len(new_messages)} new email(s)")
            return new_messages

        except HttpError as error:
            self.logger.error(f"Gmail API error: {error}")
            if error.resp.status == 401:
                self.logger.info("Attempting re-authentication")
                self._authenticate()
            return []
        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")
            return []

    def _parse_email(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a Gmail message into structured data.

        Args:
            message: Gmail API message object

        Returns:
            Dict with parsed email data
        """
        payload = message.get('payload', {})
        headers = {h['name']: h['value'] for h in payload.get('headers', [])}

        # Extract body
        body = ''
        attachments = []

        def extract_parts(parts):
            nonlocal body, attachments
            for part in parts:
                mime_type = part.get('mimeType', '')
                if mime_type == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                elif mime_type.startswith('multipart'):
                    extract_parts(part.get('parts', []))
                else:
                    # Attachment
                    filename = part.get('filename', 'attachment')
                    if filename:
                        attachments.append({
                            'filename': filename,
                            'mimeType': mime_type,
                            'size': part.get('body', {}).get('length', 0)
                        })

        if 'parts' in payload:
            extract_parts(payload['parts'])
        elif payload.get('mimeType') == 'text/plain':
            data = payload.get('body', {}).get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')

        # Use snippet if no body
        if not body:
            body = message.get('snippet', '')

        # Detect priority and category
        subject = headers.get('Subject', '')
        body_lower = (body + ' ' + subject).lower()

        priority = 'normal'
        for prio, keywords in self.PRIORITY_KEYWORDS.items():
            if any(kw in body_lower for kw in keywords):
                priority = 'high' if prio in ['high', 'billing'] else 'normal'
                break

        category = 'general'
        for cat, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in body_lower for kw in keywords):
                category = cat
                break

        return {
            'gmail_id': message['id'],
            'thread_id': message.get('threadId'),
            'from': headers.get('From', 'Unknown'),
            'to': headers.get('To', ''),
            'subject': subject,
            'date': headers.get('Date', ''),
            'body': body,
            'attachments': attachments,
            'priority': priority,
            'category': category,
            'labels': message.get('labelIds', []),
            'is_unread': 'UNREAD' in message.get('labelIds', [])
        }

    def _detect_sender_type(self, from_email: str) -> str:
        """
        Detect if sender is known contact, lead, or unknown.

        Args:
            from_email: Sender email address

        Returns:
            String indicating sender type
        """
        # Simple heuristic - could be enhanced with contact database
        if any(domain in from_email.lower() for domain in ['gmail.com', 'yahoo.com', 'hotmail.com']):
            return 'individual'
        elif any(domain in from_email.lower() for domain in ['info@', 'support@', 'noreply@']):
            return 'automated'
        else:
            return 'business'

    def create_action_file(self, message: Dict[str, Any]) -> Optional[Path]:
        """
        Create an action file for the email.

        Args:
            message: Parsed email data

        Returns:
            Path to created action file
        """
        try:
            # Parse email if not already parsed
            if 'gmail_id' not in message:
                email_data = self._parse_email(message)
            else:
                email_data = message

            gmail_id = email_data['gmail_id']
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Generate safe filename
            subject_safe = self.sanitize_filename(email_data['subject'][:50])
            from_safe = self.sanitize_filename(email_data['from'].split('<')[-1].strip('>').split('@')[0])

            # Create action file content
            frontmatter = self.generate_frontmatter(
                item_type="email",
                gmail_id=f'"{gmail_id}"',
                thread_id=f'"{email_data.get("thread_id", "")}"',
                sender=f'"{email_data["from"]}"',
                recipient=f'"{email_data["to"]}"',
                subject=f'"{email_data["subject"]}"',
                received=f'"{email_data["date"]}"',
                priority=f'"{email_data["priority"]}"',
                category=f'"{email_data["category"]}"',
                status='"pending"',
                labels=f'{json.dumps(email_data.get("labels", []))}'
            )

            # Build suggested actions based on category
            actions = self._get_suggested_actions(email_data)

            # Format attachments
            if email_data['attachments']:
                attachments_list = "\n".join([
                    f"- 📎 {att['filename']} ({att['mimeType']})"
                    for att in email_data['attachments']
                ])
            else:
                attachments_list = "*No attachments*"

            # Detect sender type
            sender_type = self._detect_sender_type(email_data['from'])

            content = f'''{frontmatter}

## Email Content

**From:** {email_data["from"]}
**To:** {email_data["to"]}
**Date:** {email_data["date"]}
**Subject:** {email_data["subject"]}

---

{email_data["body"]}

---

## Suggested Actions

{chr(10).join([f"- [ ] {action}" for action in actions])}

## Attachments

{attachments_list}

## Context

- **Sender Type:** {sender_type}
- **Category:** {email_data["category"]}
- **Priority:** {email_data["priority"]}
- **Is Unread:** {email_data["is_unread"]}

## Notes

*Add any notes about this email below*

---
*Detected by GmailWatcher at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
'''

            # Write action file
            action_filename = f"EMAIL_{timestamp}_{from_safe}_{subject_safe}.md"
            action_path = self.needs_action / action_filename
            action_path.write_text(content, encoding='utf-8')

            # Mark as processed
            self.processed_ids.add(gmail_id)
            self._save_state()

            self.logger.info(f"Created action file for email: {email_data['subject'][:50]}")
            return action_path

        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            return None

    def _get_suggested_actions(self, email_data: Dict[str, Any]) -> List[str]:
        """
        Get suggested actions based on email category.

        Args:
            email_data: Parsed email data

        Returns:
            List of suggested action strings
        """
        category = email_data.get('category', 'general')
        priority = email_data.get('priority', 'normal')

        base_actions = [
            "Review email content",
            "Draft response (requires approval before sending)"
        ]

        category_actions = {
            'billing': [
                "Generate invoice or payment request",
                "Check accounting records",
                "Send payment details (requires approval)"
            ],
            'meeting': [
                "Check calendar availability",
                "Draft meeting confirmation",
                "Create calendar event"
            ],
            'lead': [
                "Prepare pricing information",
                "Schedule follow-up call",
                "Send proposal/demo offer"
            ],
            'support': [
                "Investigate reported issue",
                "Draft troubleshooting steps",
                "Escalate if needed"
            ],
            'newsletter': [
                "Archive after reading",
                "Extract relevant information"
            ],
            'general': [
                "Categorize and file",
                "Respond if needed"
            ]
        }

        actions = base_actions + category_actions.get(category, [])

        # Add urgency for high priority
        if priority == 'high':
            actions.insert(0, "⚠️ HIGH PRIORITY - Respond within 2 hours")

        return actions

    def mark_as_read(self, gmail_id: str) -> bool:
        """
        Mark an email as read.

        Args:
            gmail_id: Gmail message ID

        Returns:
            True if successful
        """
        try:
            if self.service:
                self.service.users().messages().modify(
                    userId='me',
                    id=gmail_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
                self.logger.info(f"Marked email {gmail_id} as read")
                return True
        except Exception as e:
            self.logger.error(f"Error marking email as read: {e}")
        return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Gmail Watcher for AI Employee')
    parser.add_argument('vault_path', nargs='?', default='AI_Employee_Vault',
                        help='Path to the Obsidian vault')
    parser.add_argument('--credentials', '-c', help='Path to credentials.json')
    parser.add_argument('--interval', '-i', type=int, default=120,
                        help='Check interval in seconds')
    parser.add_argument('--unread-only', '-u', action='store_true', default=True,
                        help='Only check unread emails')
    parser.add_argument('--all-emails', '-a', action='store_true',
                        help='Check all emails (not just unread)')
    parser.add_argument('--label', '-l', default='INBOX',
                        help='Gmail label to monitor')
    parser.add_argument('--authenticate', action='store_true',
                        help='Run authentication flow only')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    if not GMAIL_AVAILABLE:
        print("Error: Gmail libraries not installed")
        print("Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        sys.exit(1)

    vault_path = Path(args.vault_path).absolute()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    # Handle authentication-only mode
    if args.authenticate:
        print("Running Gmail authentication...")
        watcher = GmailWatcher(
            str(vault_path),
            credentials_path=args.credentials,
            check_interval=args.interval,
            unread_only=not args.all_emails,
            label=args.label
        )
        if watcher.service:
            print("✓ Authentication successful!")
            sys.exit(0)
        else:
            print("✗ Authentication failed")
            sys.exit(1)

    # Create watcher
    watcher = GmailWatcher(
        str(vault_path),
        credentials_path=args.credentials,
        check_interval=args.interval,
        unread_only=not args.all_emails,
        label=args.label
    )

    if not watcher.service:
        print("Failed to initialize Gmail API")
        sys.exit(1)

    print(f"📧 Gmail Watcher starting...")
    print(f"   Vault: {vault_path}")
    print(f"   Label: {args.label}")
    print(f"   Check interval: {args.interval}s")
    print(f"   Unread only: {not args.all_emails}")

    # Run watcher
    watcher.run()


if __name__ == "__main__":
    main()
