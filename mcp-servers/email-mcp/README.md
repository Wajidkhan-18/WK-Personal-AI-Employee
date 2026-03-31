# Email MCP Server

Model Context Protocol (MCP) server for sending emails via Gmail API.

## Installation

```bash
cd mcp-servers/email-mcp
npm install
```

## Configuration

Create `.env` file:

```bash
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REDIRECT_URI=http://localhost:8080
GMAIL_TOKEN_PATH=/path/to/token.json
```

## Usage

### Start Server

```bash
# Development mode
npm start

# Production mode
node index.js
```

### Claude Code Configuration

Add to `~/.config/claude-code/mcp.json`:

```json
{
  "servers": [
    {
      "name": "email",
      "command": "node",
      "args": ["/path/to/email-mcp/index.js"],
      "env": {
        "GMAIL_CLIENT_ID": "your_client_id",
        "GMAIL_CLIENT_SECRET": "your_client_secret"
      }
    }
  ]
}
```

## Available Tools

### `send_email`

Send an email via Gmail.

**Parameters:**
- `to` (string): Recipient email address
- `subject` (string): Email subject
- `body` (string): Email body (plain text or HTML)
- `cc` (string, optional): CC recipients
- `bcc` (string, optional): BCC recipients
- `attachments` (array, optional): File paths to attach

**Example:**

```json
{
  "to": "client@example.com",
  "subject": "Invoice #1234",
  "body": "Please find attached your invoice.",
  "attachments": ["/path/to/invoice.pdf"]
}
```

### `draft_email`

Create a draft email (doesn't send).

**Parameters:** Same as `send_email`

**Returns:** Draft ID for later review/sending

### `search_emails`

Search Gmail for emails.

**Parameters:**
- `query` (string): Gmail search query
- `max_results` (number, optional): Max results (default: 10)

**Example:**

```json
{
  "query": "is:unread from:client@example.com",
  "max_results": 5
}
```

### `mark_as_read`

Mark email as read.

**Parameters:**
- `email_id` (string): Gmail message ID

## Human-in-the-Loop

For sensitive actions, the MCP server requires approval:

1. Claude creates approval file in `Pending_Approval/`
2. Human moves file to `Approved/`
3. Orchestrator triggers MCP to execute
4. Result logged to `Done/`

## Error Handling

| Error | Code | Action |
|-------|------|--------|
| Auth failed | 401 | Re-authenticate |
| Rate limit | 429 | Wait and retry |
| Invalid email | 400 | Check format |
| Attachment missing | 404 | Verify path |

## Logs

Logs written to:
- `mcp-servers/email-mcp/logs/`
- Console (stderr)

## Security

- **NEVER** commit `.env` files
- Store credentials in system keychain
- Rotate credentials monthly
- Audit all sent emails

## Testing

```bash
# Test connection
npm test

# Send test email
node test.js --to test@example.com --subject "Test"
```

---

*Email MCP Server v0.1 - Silver Tier Component*
