#!/usr/bin/env python3
"""
Get LinkedIn Access Token for API posting

Run this once to authorize your app and get an access token.
"""

import sys
import webbrowser
from pathlib import Path
from urllib.parse import urlencode

# Try to load dotenv
try:
    from dotenv import load_dotenv, set_key
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    print("Install python-dotenv: pip install python-dotenv")

import os


def get_access_token():
    """Guide user through getting LinkedIn access token."""
    
    # Load credentials from .env
    env_file = Path('.env')
    
    if HAS_DOTENV and env_file.exists():
        load_dotenv(env_file)
    
    client_id = os.getenv('LINKEDIN_CLIENT_ID', '')
    client_secret = os.getenv('LINKEDIN_CLIENT_SECRET', '')
    
    print("=" * 70)
    print("LinkedIn Access Token Generator")
    print("=" * 70)
    print()
    
    # Get credentials if not in .env
    if not client_id:
        print("Enter your LinkedIn App credentials:")
        print("(Get these from https://www.linkedin.com/developers/)")
        print()
        client_id = input("Client ID: ").strip()
        client_secret = input("Client Secret: ").strip()
        
        if HAS_DOTENV:
            set_key(str(env_file), 'LINKEDIN_CLIENT_ID', client_id)
            set_key(str(env_file), 'LINKEDIN_CLIENT_SECRET', client_secret)
            print(f"✓ Credentials saved to {env_file}")
    
    # Build authorization URL
    redirect_uri = 'https://www.linkedin.com/oauth/v2/authorization'
    scope = 'w_member_social r_basicprofile r_emailaddress'
    
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode({
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': scope,
        'state': 'ai_employee_auth'
    })}"
    
    print()
    print("Step 1: Authorize the app")
    print("-" * 70)
    print()
    print("Opening authorization URL in your browser...")
    print()
    
    # Open browser
    webbrowser.open(auth_url)
    
    print("1. Click 'Allow' to authorize the app")
    print("2. You'll be redirected to a URL")
    print("3. Copy the 'code=' parameter from that URL")
    print()
    
    authorization_code = input("Paste the authorization code here: ").strip()
    
    if not authorization_code:
        print("✗ No code provided. Exiting.")
        sys.exit(1)
    
    print()
    print("Step 2: Exchange code for access token")
    print("-" * 70)
    print()
    print("Now run this curl command to get your access token:")
    print()
    print(f"""curl -X POST "https://www.linkedin.com/oauth/v2/accessToken" \\
  -d "grant_type=authorization_code" \\
  -d "code={authorization_code}" \\
  -d "redirect_uri={redirect_uri}" \\
  -d "client_id={client_id}" \\
  -d "client_secret={client_secret}"
""")
    print()
    print("Or use this Python script:")
    print()
    print(f"""import requests

response = requests.post("https://www.linkedin.com/oauth/v2/accessToken", data={{
    "grant_type": "authorization_code",
    "code": "{authorization_code}",
    "redirect_uri": "{redirect_uri}",
    "client_id": "{client_id}",
    "client_secret": "{client_secret}"
}})

print(response.json())
# Copy the "access_token" value
""")
    print()
    
    access_token = input("Paste your access token here: ").strip()
    
    if access_token and HAS_DOTENV:
        set_key(str(env_file), 'LINKEDIN_ACCESS_TOKEN', access_token)
        print(f"✓ Access token saved to {env_file}")
        print()
        print("=" * 70)
        print("SUCCESS! You can now use LinkedIn API posting")
        print("=" * 70)
        print()
        print("Run: python scripts\\linkedin_api_post.py post")
    
    return access_token


if __name__ == '__main__':
    get_access_token()
