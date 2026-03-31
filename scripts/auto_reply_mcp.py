#!/usr/bin/env python3
"""
Auto Reply with MCP - Automatic Email Processing

This script:
1. Finds all approved emails
2. Auto-drafts replies
3. Sends via Gmail API
4. Moves to Done/

Usage:
    python auto_reply_mcp.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.email_sender import EmailSender, extract_draft


def auto_draft_reply(email_content: str) -> str:
    """Auto-generate reply draft based on email content.
    
    Returns ONLY the email content, no instructions.
    """
    
    # Extract original email body
    body = ""
    if '## Email Content' in email_content:
        start = email_content.find('## Email Content')
        content_start = email_content.find('---', start)
        if content_start != -1:
            content_start = email_content.find('---', content_start + 3)
        if content_start != -1:
            content_end = email_content.find('---', content_start + 3)
            if content_end == -1:
                content_end = email_content.find('##', content_start)
            body = email_content[content_start:content_end].strip()
            body = body.strip('-').strip()
    
    body_lower = body.lower()
    
    # Generate reply based on content
    if any(word in body_lower for word in ['invoice', 'payment', 'bill', 'receipt']):
        return """Thank you for your inquiry.

I've received your request regarding the invoice/payment. I'll process this and get back to you within 24 hours with the details.

If you need any immediate assistance, please don't hesitate to reach out.

Best regards"""
    
    elif any(word in body_lower for word in ['greeting', 'hello', 'hi ', 'hey', 'kaifa', 'how are you']):
        return """Hello!

Thank you for reaching out. I hope you're doing well!

I'm doing great, thank you for asking. How can I help you today?

Best regards"""
    
    elif any(word in body_lower for word in ['meeting', 'call', 'schedule', 'zoom', 'teams']):
        return """Thank you for the meeting request.

I'd be happy to schedule a call. Please let me know your availability for this week, and I'll send over a calendar invitation.

Looking forward to speaking with you.

Best regards"""
    
    elif any(word in body_lower for word in ['interested', 'pricing', 'demo', 'quote', 'proposal']):
        return """Thank you for your interest in our services!

I'd love to learn more about your needs and provide you with the right solution. Could you please share:
1. Your specific requirements
2. Timeline
3. Budget range (if comfortable)

Once I have this information, I'll prepare a customized proposal for you.

Best regards"""
    
    elif any(word in body_lower for word in ['security', 'alert', 'password', 'login']):
        return """Thank you for the security notification.

I've received this alert and will review it. If any action is required, I'll take care of it promptly.

For security purposes, please don't send sensitive information via email.

Best regards"""
    
    elif any(word in body_lower for word in ['weather']):
        return """Hello!

Thanks for reaching out! I'm doing well, thank you.

Regarding the weather - I don't have real-time weather data, but you can check the current weather in your area by:
- Searching "weather" on Google
- Using a weather app like Weather.com or AccuWeather
- Asking a voice assistant like Siri or Google Assistant

Is there anything else I can help you with?

Best regards"""
    
    else:
        return """Thank you for your email.

I've received your message and will respond as soon as possible.

Best regards"""


def main():
    """Process all approved emails automatically."""
    
    vault_path = Path('AI_Employee_Vault').absolute()
    approved = vault_path / 'Approved'
    done = vault_path / 'Done'
    
    if not approved.exists():
        print("No Approved folder")
        sys.exit(1)
    
    # Initialize email sender
    sender = EmailSender(str(vault_path))
    
    if not sender.service:
        print("Gmail authentication failed")
        sys.exit(1)
    
    # Find email files
    email_files = list(approved.glob('EMAIL_*.md'))
    
    if not email_files:
        print("No emails to process")
        sys.exit(1)
    
    print()
    print("=" * 70)
    print("Auto Reply MCP - Automatic Email Processing")
    print("=" * 70)
    print()
    print(f"Found {len(email_files)} email(s) to process")
    print()
    
    sent_count = 0
    failed_count = 0
    
    for email_file in email_files:
        print(f"Processing: {email_file.name}")
        
        content = email_file.read_text(encoding='utf-8')
        
        # Check if draft already exists
        if '## Reply Draft' in content:
            print("  ✓ Draft already exists")
            draft = extract_draft(content)
        else:
            print("  🤖 Auto-drafting reply...")
            draft = auto_draft_reply(content)
            
            # Add draft to file (WITHOUT the instructions - those stay in file only)
            draft_section = f"""
## Reply Draft (Auto-Generated by MCP)

{draft}

---
*Generated at: {datetime.now().isoformat()}*

## Send Instructions (NOT sent in email)

This file will be auto-processed. The draft above will be sent via Gmail API.
"""
            # Append draft to file (before the last ---)
            if '---' in content:
                last_dash = content.rfind('---')
                content = content[:last_dash] + draft_section + "---\n"
            else:
                content += draft_section
            
            email_file.write_text(content, encoding='utf-8')
        
        # Extract metadata
        gmail_id = None
        sender_email = ""
        subject = ""
        
        for line in content.split('\n'):
            if 'gmail_id:' in line:
                gmail_id = line.split(':')[1].strip().strip('"')
            if 'sender:' in line:
                sender_email = line.split(':')[1].strip().strip('"')
            if 'subject:' in line:
                subject = line.split(':')[1].strip().strip('"')
        
        # Send email
        print(f"  📤 Sending to: {sender_email}")
        
        success = sender.send_reply(email_file, draft)
        
        if success:
            # Mark as read
            if gmail_id:
                sender.mark_as_read(gmail_id)
            
            # Move to Done
            done.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            done_path = done / f"{timestamp}_{email_file.name}"
            
            # Update content
            content = content.replace('status: pending', 'status: sent')
            content += f"\n*Sent at: {datetime.now().isoformat()}*\n"
            done_path.write_text(content, encoding='utf-8')
            email_file.unlink()
            
            print(f"  ✓ Sent! Moved to Done/")
            sent_count += 1
        else:
            print(f"  ✗ Failed to send")
            failed_count += 1
        
        print()
    
    print("=" * 70)
    print(f"Results: {sent_count} sent, {failed_count} failed")
    print("=" * 70)


if __name__ == '__main__':
    main()
