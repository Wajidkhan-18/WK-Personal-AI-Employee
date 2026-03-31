#!/usr/bin/env python3
"""
Email MCP Server - Automatic Email Replies

This MCP server:
1. Reads approved email files
2. Drafts automatic replies using AI
3. Sends emails via Gmail API
4. Moves files to Done/

Usage:
    python server.py
"""

import sys
import os
import json
import base64
from pathlib import Path
from datetime import datetime
from email.message import EmailMessage

# MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP SDK not installed. Run: pip install mcp")
    sys.exit(1)

# Gmail API
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

# Create server
server = Server("email-mcp")

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', 'AI_Employee_Vault'))
TOKEN_PATH = Path(os.getenv('GMAIL_TOKEN_PATH', VAULT_PATH / '.gmail_token.json'))

# Gmail service
gmail_service = None


def authenticate_gmail():
    """Authenticate with Gmail API."""
    global gmail_service
    
    try:
        if not TOKEN_PATH.exists():
            return False
        
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify'
        ])
        
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        
        gmail_service = build('gmail', 'v1', credentials=creds)
        return True
        
    except Exception as e:
        print(f"Authentication error: {e}", file=sys.stderr)
        return False


def extract_draft_from_file(file_path: Path) -> dict:
    """Extract email draft information from action file."""
    
    content = file_path.read_text(encoding='utf-8')
    
    # Extract metadata from frontmatter
    metadata = {}
    in_frontmatter = False
    
    for line in content.split('\n'):
        if line.strip() == '---':
            if not in_frontmatter:
                in_frontmatter = True
            else:
                break
            continue
        
        if in_frontmatter and ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip().strip('"')
    
    # Extract draft from Reply Draft section
    draft_text = ""
    if '## Reply Draft' in content:
        start = content.find('## Reply Draft')
        draft_start = content.find('---', start)
        if draft_start != -1:
            draft_start = content.find('---', draft_start + 3)
        if draft_start != -1:
            draft_end = content.find('---', draft_start + 3)
            if draft_end == -1:
                draft_end = content.find('**To Send', draft_start)
            if draft_end == -1:
                draft_end = len(content)
            draft_text = content[draft_start:draft_end].strip()
            draft_text = draft_text.strip('-').strip()
    
    return {
        'to': metadata.get('sender', ''),
        'subject': metadata.get('subject', ''),
        'thread_id': metadata.get('thread_id', ''),
        'gmail_id': metadata.get('gmail_id', ''),
        'draft': draft_text,
        'file_path': str(file_path)
    }


def send_email(to: str, subject: str, body: str, thread_id: str = None) -> dict:
    """Send email via Gmail API."""
    
    if not gmail_service:
        return {'success': False, 'error': 'Not authenticated'}
    
    try:
        # Create message
        message = EmailMessage()
        message['To'] = to
        message['Subject'] = subject
        message['From'] = 'me'
        message.set_content(body)
        
        # Encode
        encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Send
        send_body = {'raw': encoded}
        if thread_id:
            send_body['threadId'] = thread_id
        
        result = gmail_service.users().messages().send(
            userId='me',
            body=send_body
        ).execute()
        
        return {
            'success': True,
            'message_id': result['id'],
            'thread_id': result.get('threadId', '')
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def mark_as_read(gmail_id: str) -> bool:
    """Mark email as read."""
    
    if not gmail_service:
        return False
    
    try:
        gmail_service.users().messages().modify(
            userId='me',
            id=gmail_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        return True
    except:
        return False


def move_to_done(file_path: Path) -> Path:
    """Move processed file to Done folder."""
    
    done_folder = VAULT_PATH / 'Done'
    done_folder.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    done_path = done_folder / f"{timestamp}_{file_path.name}"
    
    # Update status
    content = file_path.read_text(encoding='utf-8')
    content = content.replace('status: pending', 'status: sent')
    content += f"\n*Sent at: {datetime.now().isoformat()}*\n"
    
    done_path.write_text(content, encoding='utf-8')
    file_path.unlink()
    
    return done_path


@server.list_tools()
async def list_tools():
    """List available email tools."""
    
    return [
        Tool(
            name="send_email_reply",
            description="Send an email reply from an approved action file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the approved email action file"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="list_approved_emails",
            description="List all approved email files ready for processing",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="draft_auto_reply",
            description="Automatically draft a reply to an email using AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_content": {
                        "type": "string",
                        "description": "Original email content"
                    },
                    "tone": {
                        "type": "string",
                        "description": "Reply tone: friendly, professional, casual",
                        "default": "friendly"
                    }
                },
                "required": ["email_content"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    
    if name == "list_approved_emails":
        approved = VAULT_PATH / 'Approved'
        if not approved.exists():
            return [TextContent(type="text", text="No Approved folder found")]
        
        emails = list(approved.glob('EMAIL_*.md'))
        if not emails:
            return [TextContent(type="text", text="No emails in Approved folder")]
        
        result = "Approved emails ready for processing:\n\n"
        for email in emails:
            content = email.read_text()
            subject = ""
            sender = ""
            for line in content.split('\n')[:20]:
                if 'subject:' in line.lower():
                    subject = line.split(':')[1].strip().strip('"')
                if 'sender:' in line.lower():
                    sender = line.split(':')[1].strip().strip('"')
            result += f"- {email.name}\n  From: {sender}\n  Subject: {subject}\n\n"
        
        return [TextContent(type="text", text=result)]
    
    elif name == "draft_auto_reply":
        # Simple auto-draft based on email content
        email_content = arguments.get('email_content', '')
        tone = arguments.get('tone', 'friendly')
        
        # Generate simple reply
        if 'invoice' in email_content.lower() or 'payment' in email_content.lower():
            reply = "Thank you for your inquiry.\n\nI'll process your request and get back to you shortly.\n\nBest regards"
        elif 'greeting' in email_content.lower() or 'hello' in email_content.lower():
            reply = "Hello!\n\nThank you for reaching out. I hope you're doing well!\n\nBest regards"
        else:
            reply = "Thank you for your email.\n\nI've received your message and will respond soon.\n\nBest regards"
        
        return [TextContent(type="text", text=f"Auto-drafted reply:\n\n{reply}")]
    
    elif name == "send_email_reply":
        file_path = Path(arguments.get('file_path', ''))
        
        if not file_path.exists():
            return [TextContent(type="text", text=f"File not found: {file_path}")]
        
        # Authenticate
        if not authenticate_gmail():
            return [TextContent(type="text", text="Gmail authentication failed")]
        
        # Extract draft
        email_data = extract_draft_from_file(file_path)
        
        if not email_data['draft']:
            return [TextContent(type="text", text="No draft found in file")]
        
        # Send email
        result = send_email(
            to=email_data['to'],
            subject=f"Re: {email_data['subject']}",
            body=email_data['draft'],
            thread_id=email_data.get('thread_id', '')
        )
        
        if result['success']:
            # Mark as read
            if email_data.get('gmail_id'):
                mark_as_read(email_data['gmail_id'])
            
            # Move to Done
            done_path = move_to_done(file_path)
            
            return [TextContent(
                type="text",
                text=f"✓ Email sent!\nMessage ID: {result['message_id']}\nMoved to: {done_path}"
            )]
        else:
            return [TextContent(type="text", text=f"Failed to send: {result['error']}")]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    
    print("Email MCP Server starting...", file=sys.stderr)
    print(f"Vault: {VAULT_PATH}", file=sys.stderr)
    print(f"Token: {TOKEN_PATH}", file=sys.stderr)
    
    # Authenticate
    if authenticate_gmail():
        print("✓ Gmail authenticated", file=sys.stderr)
    else:
        print("✗ Gmail authentication failed", file=sys.stderr)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
