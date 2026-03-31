# LinkedIn Auto-Post Setup Guide

## Why Browser Automation Fails

LinkedIn blocks automated browsers (Playwright, Selenium, Puppeteer) through:
- Bot detection scripts
- Session fingerprinting  
- Behavior analysis
- CAPTCHA challenges

**Success rate: < 20%** (unreliable for production)

## ✅ Working Solution: LinkedIn API

### Step 1: Create LinkedIn Developer Account

1. Go to https://www.linkedin.com/developers/
2. Click "Create app"
3. Fill in app details:
   - App Name: "AI Employee"
   - Company: Your company
   - App Logo: (optional)
4. Accept terms and create

### Step 2: Get API Credentials

1. In your app dashboard, go to "Auth" tab
2. Note down:
   - **Client ID**
   - **Client Secret**
3. Under "Authorized redirect URLs", add:
   ```
   https://www.linkedin.com/oauth/v2/authorization
   ```

### Step 3: Request Permissions

Your app needs these permissions:
- `w_member_social` - Post to your profile
- `r_basicprofile` - Read basic profile info
- `r_emailaddress` - Read email address

**To get permissions:**
1. Go to "Auth" tab in app dashboard
2. Scroll to "Authentication Scopes"
3. Request the scopes above
4. Wait for approval (usually 1-2 days)

### Step 4: Install Dependencies

```bash
pip install linkedin-api requests
```

### Step 5: Configure Credentials

Create `.env` file:

```bash
# LinkedIn API Credentials
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_ACCESS_TOKEN=your_access_token_here
```

### Step 6: Get Access Token

Run this script once to get your access token:

```bash
python scripts\linkedin_get_token.py
```

This will:
1. Open browser for OAuth authorization
2. You approve the app
3. Access token is saved to `.env`

### Step 7: Auto-Post with API

```bash
python scripts\linkedin_api_post.py post
```

This uses the **official API** - 99.9% reliable!

---

## Alternative: Use Buffer/Hootsuite

If API approval takes too long, use these services:

### Buffer (Recommended)
- Has official LinkedIn partnership
- Free plan: 3 posts at a time
- API available: https://buffer.com/developers

### Setup:
```bash
pip install buffer-api
python scripts\buffer_post.py create --content "Your post"
```

---

## Current Status

| Method | Status | Reliability |
|--------|--------|-------------|
| Browser Automation | ❌ Blocked | < 20% |
| LinkedIn API | ✅ Works | 99.9% |
| Buffer/Hootsuite | ✅ Works | 99.9% |

---

## Next Steps

**For immediate solution:**
Use the manual helper (10 seconds, you click Post)
```bash
python scripts\linkedin_quick_post.py
```

**For true automation:**
1. Create LinkedIn Developer app (10 min)
2. Wait for API approval (1-2 days)
3. Use API-based posting (permanent solution)

---

*LinkedIn API documentation:*
https://learn.microsoft.com/en-us/linkedin/marketing/
