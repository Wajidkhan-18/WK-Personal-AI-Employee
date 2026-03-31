#!/usr/bin/env python3
"""
Email Sender - Sends email replies via Gmail API

Reads draft replies from action files and sends them via Gmail API.

Usage:
    python email_sender.py
"""

import sys
import base64
from pathlib import Path
from datetime import datetime
from email.message import EmailMessage

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("Gmail libraries not installed.")
    print("Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)


class EmailSender:
    """Send emails via Gmail API."""
    
    def __init__(self, vault_path: str):
        """Initialize email sender with vault path."""
        self.vault_path = Path(vault_path)
        self.token_path = self.vault_path / '.gmail_token.json'
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API."""
        try:
            if not self.token_path.exists():
                print("❌ Gmail token not found.")
                print("Run: python scripts\\gmail_watcher.py VAULT --authenticate")
                return False
            
            creds = Credentials.from_authorized_user_file(self.token_path, [
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.modify'
            ])
            
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            self.service = build('gmail', 'v1', credentials=creds)
            print("✓ Gmail API authenticated")
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def send_reply(self, original_email_file: Path, draft: str) -> bool:
        """
        Send a reply to an email.
        
        Args:
            original_email_file: Path to the action file
            draft: Reply draft text
            
        Returns:
            True if sent successfully
        """
        try:
            # Read original email metadata
            content = original_email_file.read_text(encoding='utf-8')
            
            # Extract headers from frontmatter
            thread_id = None
            sender = ""
            subject = ""
            
            if 'thread_id:' in content:
                for line in content.split('\n'):
                    if 'thread_id:' in line:
                        thread_id = line.split(':')[1].strip().strip('"')
                    if 'sender:' in line:
                        sender = line.split(':')[1].strip().strip('"')
                    if 'subject:' in line:
                        subject = line.split(':')[1].strip().strip('"')
            
            # Create reply message
            message = EmailMessage()
            
            # Set headers
            message['To'] = sender
            message['Subject'] = f"Re: {subject}"
            message['From'] = 'me'
            
            # Set reply body
            message.set_content(draft)
            
            # Encode message
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Create send body
            send_body = {'raw': encoded_message}
            
            # Add thread ID if available (for proper threading)
            if thread_id:
                send_body['threadId'] = thread_id
            
            # Send via Gmail API
            sent_message = self.service.users().messages().send(
                userId='me',
                body=send_body
            ).execute()
            
            print(f"✓ Email sent! Message ID: {sent_message['id']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send: {e}")
            return False
    
    def mark_as_read(self, gmail_id: str) -> bool:
        """Mark email as read."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=gmail_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            print(f"⚠️ Could not mark as read: {e}")
            return False


def extract_draft(content: str) -> str:
    """Extract reply draft from action file content.
    
    Only extracts the actual email content, NOT the instructions.
    """

    # Look for Reply Draft section
    if '## Reply Draft' not in content:
        return ""

    start = content.find('## Reply Draft')

    # Find the horizontal rules that wrap the actual draft
    draft_start = content.find('---', start)
    if draft_start == -1:
        return ""
    
    # Move past the first ---
    draft_start = content.find('---', draft_start + 3)
    if draft_start == -1:
        return ""
    
    # Find end of draft (next --- that's followed by **To Send** or similar)
    draft_end = content.find('---', draft_start + 3)
    if draft_end == -1:
        return ""
    
    # Extract draft between the two --- markers
    draft = content[draft_start:draft_end].strip()
    
    # Remove any leading/trailing horizontal rules
    draft = draft.strip('-').strip()
    
    # Remove any instruction sections (Option A, Option B, etc.)
    if '**To Send' in draft:
        draft = draft.split('**To Send')[0].strip()
    if 'Option A' in draft:
        draft = draft.split('Option A')[0].strip()
    if 'Option B' in draft:
        draft = draft.split('Option B')[0].strip()
    
    # Remove any "Ready to send" headers
    if '**Ready to send' in draft:
        draft = draft.split('**Ready to send')[1].strip()
    
    # Clean up
    draft = draft.strip()
    draft = draft.strip('-').strip()
    
    return draft


def main():
    """Main entry point."""
    vault_path = Path('AI_Employee_Vault').absolute()
    
    if not vault_path.exists():
        print("Vault not found")
        sys.exit(1)
    
    approved = vault_path / 'Approved'
    done = vault_path / 'Done'
    
    if not approved.exists():
        print("No Approved folder")
        sys.exit(1)
    
    # Initialize sender
    sender = EmailSender(str(vault_path))
    
    if not sender.service:
        print("Cannot send emails - authentication failed")
        sys.exit(1)
    
    # Find email files with drafts
    email_files = list(approved.glob('EMAIL_*.md'))
    
    if not email_files:
        print("No emails to process")
        sys.exit(1)
    
    print()
    print("=" * 70)
    print("Email Sender - Sending Replies")
    print("=" * 70)
    print()
    print(f"Found {len(email_files)} email(s) in Approved/")
    print()
    
    sent_count = 0
    
    for email_file in email_files:
        content = email_file.read_text(encoding='utf-8')
        
        # Extract draft
        draft = extract_draft(content)
        
        if not draft:
            print(f"⚠️  No draft found in {email_file.name}")
            continue
        
        # Extract Gmail ID
        gmail_id = None
        if 'gmail_id:' in content:
            for line in content.split('\n'):
                if 'gmail_id:' in line:
                    gmail_id = line.split(':')[1].strip().strip('"')
                    break
        
        print(f"Processing: {email_file.name}")
        print(f"Draft preview: {draft[:80]}...")
        print()
        
        # Ask for confirmation
        response = input("Send this reply? (y/n): ").strip().lower()
        
        if response != 'y':
            print("Skipped")
            print()
            continue
        
        # Send email
        success = sender.send_reply(email_file, draft)
        
        if success:
            sent_count += 1
            
            # Mark original as read
            if gmail_id:
                sender.mark_as_read(gmail_id)
            
            # Move to Done
            done.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            done_path = done / f"{timestamp}_{email_file.name}"
            
            # Update file with sent status
            content = content.replace('status: pending', 'status: sent')
            content += f"\n*Reply sent at {datetime.now().isoformat()}*\n"
            done_path.write_text(content, encoding='utf-8')
            email_file.unlink()
            
            print(f"✓ Moved to Done/")
        
        print()
    
    print("=" * 70)
    print(f"Sent {sent_count}/{len(email_files)} email(s)")
    print("=" * 70)


if __name__ == '__main__':
    main()
