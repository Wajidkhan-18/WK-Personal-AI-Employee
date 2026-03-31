#!/usr/bin/env node

/**
 * Email MCP Server
 * 
 * Model Context Protocol server for sending emails via Gmail API.
 * Implements human-in-the-loop approval workflow.
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');
const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

// Configuration
const GMAIL_CLIENT_ID = process.env.GMAIL_CLIENT_ID;
const GMAIL_CLIENT_SECRET = process.env.GMAIL_CLIENT_SECRET;
const GMAIL_REDIRECT_URI = process.env.GMAIL_REDIRECT_URI || 'http://localhost:8080';
const TOKEN_PATH = process.env.GMAIL_TOKEN_PATH || path.join(__dirname, 'token.json');
const VAULT_PATH = process.env.VAULT_PATH || './AI_Employee_Vault';

// Validate configuration
if (!GMAIL_CLIENT_ID || !GMAIL_CLIENT_SECRET) {
  console.error('Error: GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be set');
  process.exit(1);
}

// OAuth2 client setup
const oauth2Client = new google.auth.OAuth2(
  GMAIL_CLIENT_ID,
  GMAIL_CLIENT_SECRET,
  GMAIL_REDIRECT_URI
);

// Load or refresh token
let credentials = null;
if (fs.existsSync(TOKEN_PATH)) {
  try {
    const token = JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf8'));
    oauth2Client.setCredentials(token);
    credentials = token;
    console.error('Loaded Gmail credentials');
  } catch (err) {
    console.error('Error loading token:', err.message);
  }
}

// Gmail service
const gmail = google.gmail({ version: 'v1', auth: oauth2Client });

// Create MCP server
const server = new Server(
  {
    name: 'email-mcp',
    version: '0.1.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'send_email',
        description: 'Send an email via Gmail. Requires human approval for external emails.',
        inputSchema: {
          type: 'object',
          properties: {
            to: { type: 'string', description: 'Recipient email address' },
            subject: { type: 'string', description: 'Email subject' },
            body: { type: 'string', description: 'Email body (plain text or HTML)' },
            cc: { type: 'string', description: 'CC recipients' },
            bcc: { type: 'string', description: 'BCC recipients' },
            attachments: {
              type: 'array',
              items: { type: 'string' },
              description: 'File paths to attach'
            },
            requires_approval: {
              type: 'boolean',
              description: 'Whether this email requires human approval',
              default: true
            }
          },
          required: ['to', 'subject', 'body'],
        },
      },
      {
        name: 'draft_email',
        description: 'Create a draft email without sending (for review)',
        inputSchema: {
          type: 'object',
          properties: {
            to: { type: 'string', description: 'Recipient email address' },
            subject: { type: 'string', description: 'Email subject' },
            body: { type: 'string', description: 'Email body' },
            cc: { type: 'string', description: 'CC recipients' },
            attachments: {
              type: 'array',
              items: { type: 'string' },
              description: 'File paths to attach'
            }
          },
          required: ['to', 'subject', 'body'],
        },
      },
      {
        name: 'search_emails',
        description: 'Search Gmail for emails matching a query',
        inputSchema: {
          type: 'object',
          properties: {
            query: { type: 'string', description: 'Gmail search query' },
            max_results: { type: 'number', description: 'Maximum results to return', default: 10 }
          },
          required: ['query'],
        },
      },
      {
        name: 'mark_as_read',
        description: 'Mark an email as read',
        inputSchema: {
          type: 'object',
          properties: {
            email_id: { type: 'string', description: 'Gmail message ID' }
          },
          required: ['email_id'],
        },
      },
    ],
  };
});

// Tool execution handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'send_email':
        return await sendEmail(args);
      
      case 'draft_email':
        return await draftEmail(args);
      
      case 'search_emails':
        return await searchEmails(args);
      
      case 'mark_as_read':
        return await markAsRead(args);
      
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

/**
 * Send an email
 */
async function sendEmail({ to, subject, body, cc, bcc, attachments, requires_approval = true }) {
  // Check if approval is required
  if (requires_approval) {
    // Create approval request file
    const approvalFile = createApprovalFile({ to, subject, body, cc, bcc, attachments });
    return {
      content: [
        {
          type: 'text',
          text: `Approval required. File created: ${approvalFile}\n` +
                `Move this file to /Approved to send the email.`,
        },
      ],
    };
  }

  // Create message
  const message = createMessage(to, subject, body, cc, bcc, attachments);

  // Send via Gmail API
  const response = await gmail.users.messages.send({
    userId: 'me',
    requestBody: message,
  });

  // Log action
  logAction('email_send', { to, subject, messageId: response.data.id });

  return {
    content: [
      {
        type: 'text',
        text: `Email sent successfully! Message ID: ${response.data.id}`,
      },
    ],
  };
}

/**
 * Create a draft email
 */
async function draftEmail({ to, subject, body, cc, attachments }) {
  const message = createMessage(to, subject, body, cc, null, attachments);

  const response = await gmail.users.drafts.create({
    userId: 'me',
    requestBody: message,
  });

  return {
    content: [
      {
        type: 'text',
        text: `Draft created successfully! Draft ID: ${response.data.id}\n` +
              `Review and send from Gmail: https://mail.google.com/mail/u/0/#drafts`,
      },
    ],
  };
}

/**
 * Search emails
 */
async function searchEmails({ query, max_results = 10 }) {
  const response = await gmail.users.messages.list({
    userId: 'me',
    q: query,
    maxResults: max_results,
  });

  const messages = response.data.messages || [];
  
  if (messages.length === 0) {
    return {
      content: [
        {
          type: 'text',
          text: 'No emails found matching your query.',
        },
      ],
    };
  }

  // Fetch full details for each message
  const results = [];
  for (const msg of messages.slice(0, 5)) { // Limit to 5 full messages
    const full = await gmail.users.messages.get({
      userId: 'me',
      id: msg.id,
      format: 'metadata',
      metadataHeaders: ['From', 'To', 'Subject', 'Date'],
    });
    
    const headers = full.data.payload.headers;
    results.push({
      id: msg.id,
      from: headers.find(h => h.name === 'From')?.value,
      to: headers.find(h => h.name === 'To')?.value,
      subject: headers.find(h => h.name === 'Subject')?.value,
      date: headers.find(h => h.name === 'Date')?.value,
    });
  }

  return {
    content: [
      {
        type: 'text',
        text: `Found ${messages.length} emails. Showing first ${results.length}:\n\n` +
              results.map(r => 
                `From: ${r.from}\nSubject: ${r.subject}\nDate: ${r.date}\n---`
              ).join('\n'),
      },
    ],
  };
}

/**
 * Mark email as read
 */
async function markAsRead({ email_id }) {
  await gmail.users.messages.modify({
    userId: 'me',
    id: email_id,
    requestBody: {
      removeLabelIds: ['UNREAD'],
    },
  });

  return {
    content: [
      {
        type: 'text',
        text: `Email ${email_id} marked as read.`,
      },
    ],
  };
}

/**
 * Create MIME message for Gmail API
 */
function createMessage(to, subject, body, cc, bcc, attachments) {
  let message = '';
  
  // Headers
  message += `To: ${to}\n`;
  message += `Subject: ${subject}\n`;
  
  if (cc) {
    message += `CC: ${cc}\n`;
  }
  
  if (bcc) {
    message += `BCC: ${bcc}\n`;
  }
  
  message += `MIME-Version: 1.0\n`;
  message += `Content-Type: multipart/mixed; boundary="BOUNDARY"\n\n`;
  
  // Body
  message += `--BOUNDARY\n`;
  message += `Content-Type: text/plain; charset="UTF-8"\n\n`;
  message += `${body}\n\n`;
  
  // Attachments
  if (attachments && attachments.length > 0) {
    for (const filePath of attachments) {
      if (fs.existsSync(filePath)) {
        const filename = path.basename(filePath);
        const content = fs.readFileSync(filePath).toString('base64');
        const mimeType = getMimeType(filePath);
        
        message += `--BOUNDARY\n`;
        message += `Content-Type: ${mimeType}; name="${filename}"\n`;
        message += `Content-Disposition: attachment; filename="${filename}"\n`;
        message += `Content-Transfer-Encoding: base64\n\n`;
        message += `${content}\n\n`;
      } else {
        console.error(`Attachment not found: ${filePath}`);
      }
    }
  }
  
  message += `--BOUNDARY--`;
  
  // Encode for Gmail API
  const encoded = Buffer.from(message)
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
  
  return { raw: encoded };
}

/**
 * Get MIME type for file extension
 */
function getMimeType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const mimeTypes = {
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.txt': 'text/plain',
    '.csv': 'text/csv',
  };
  return mimeTypes[ext] || 'application/octet-stream';
}

/**
 * Create approval request file
 */
function createApprovalFile({ to, subject, body, cc, bcc, attachments }) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `EMAIL_APPROVAL_${timestamp}.md`;
  const filePath = path.join(VAULT_PATH, 'Pending_Approval', filename);
  
  const content = `---
type: approval_request
action: send_email
created: ${new Date().toISOString()}
status: pending
---

## Email Approval Required

**To:** ${to}
${cc ? `**CC:** ${cc}` : ''}
**Subject:** ${subject}

## Email Body

${body}

${attachments && attachments.length > 0 ? `## Attachments\n\n${attachments.map(a => `- ${a}`).join('\n')}` : ''}

## To Approve

Move this file to \`/Approved\` folder.

## To Reject

Move this file to \`/Rejected\` folder with reason.

---

*Created by Email MCP at ${new Date().toLocaleString()}*
`;

  // Ensure directory exists
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  
  fs.writeFileSync(filePath, content, 'utf8');
  return filePath;
}

/**
 * Log action to vault
 */
function logAction(actionType, details) {
  const logFile = path.join(VAULT_PATH, 'Logs', `${new Date().toISOString().split('T')[0]}_email.json`);
  
  let logs = [];
  if (fs.existsSync(logFile)) {
    try {
      logs = JSON.parse(fs.readFileSync(logFile, 'utf8'));
    } catch (e) {
      logs = [];
    }
  }
  
  logs.push({
    timestamp: new Date().toISOString(),
    action_type: actionType,
    ...details,
  });
  
  const dir = path.dirname(logFile);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  
  fs.writeFileSync(logFile, JSON.stringify(logs, null, 2), 'utf8');
}

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Email MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
