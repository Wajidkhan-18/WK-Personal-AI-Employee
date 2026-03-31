#!/usr/bin/env python3
"""
LinkedIn API Auto-Poster - Posts using official LinkedIn API

This is the RELIABLE way to auto-post to LinkedIn.
Requires LinkedIn Developer App and access token.

Setup:
1. Create app at https://www.linkedin.com/developers/
2. Get client ID, secret, and access token
3. Run: python scripts\linkedin_get_token.py
4. Then run this script
"""

import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# Try to load dotenv
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

try:
    import os
except ImportError:
    pass


def get_access_token():
    """Get LinkedIn access token from environment or .env"""
    
    # Try .env file first
    if HAS_DOTENV:
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file)
            token = os.getenv('LINKEDIN_ACCESS_TOKEN', '')
            if token:
                return token
    
    # Try environment variable
    token = os.getenv('LINKEDIN_ACCESS_TOKEN', '')
    if token:
        return token
    
    return None


def post_to_linkedin_api(text: str) -> dict:
    """
    Post to LinkedIn using official API.
    
    Args:
        text: Post content
        
    Returns:
        dict with API response
    """
    
    access_token = get_access_token()
    
    if not access_token:
        return {
            'success': False,
            'error': 'No access token found. Run: python scripts\\linkedin_get_token.py'
        }
    
    # LinkedIn API endpoint for creating posts
    # Using UGC Posts API
    url = "https://api.linkedin.com/v2/ugcPosts"
    
    headers = {
        'X-Restli-Protocol-Version': '2.0.0',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    # Build post payload
    # Note: This posts to the authenticated user's profile
    payload = {
        "author": "urn:li:person:ME",  # Will be replaced with actual person URN
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": text
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        return {
            'success': True,
            'post_id': result.get('id', 'unknown'),
            'response': result
        }
        
    except requests.exceptions.HTTPError as e:
        error_detail = str(e)
        if e.response is not None:
            try:
                error_json = e.response.json()
                error_detail = error_json.get('message', str(e))
            except:
                pass
        
        return {
            'success': False,
            'error': f'API Error: {error_detail}',
            'status_code': e.response.status_code if e.response else None
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def get_person_urn(access_token: str) -> str:
    """Get the authenticated user's LinkedIn URN"""
    
    url = "https://api.linkedin.com/v2/me"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get('id', '')
    except:
        return 'ME'


def main():
    vault_path = Path('AI_Employee_Vault').absolute()
    approved = vault_path / 'Approved'
    
    if not approved.exists():
        print("No Approved folder found.")
        return
    
    approved_posts = list(approved.glob('LINKEDIN_*.md'))
    
    if not approved_posts:
        print("No LinkedIn posts in Approved folder.")
        return
    
    print("=" * 70)
    print("LinkedIn API Auto-Poster")
    print("=" * 70)
    print()
    
    # Check for access token
    access_token = get_access_token()
    
    if not access_token:
        print("❌ No LinkedIn access token found!")
        print()
        print("Setup instructions:")
        print("1. Go to https://www.linkedin.com/developers/")
        print("2. Create an app")
        print("3. Get Client ID and Client Secret")
        print("4. Run: python scripts\\linkedin_get_token.py")
        print()
        return
    
    print("✓ Access token found")
    print()
    
    print(f"Found {len(approved_posts)} approved post(s)")
    print()
    
    for post_file in approved_posts:
        content = post_file.read_text(encoding='utf-8')
        
        # Extract post content
        if '## Post Content' in content:
            start = content.find('## Post Content') + len('## Post Content')
            end = content.find('---', start)
            post_text = content[start:end].strip()
            
            print(f"Processing: {post_file.name}")
            print()
            print("Content:")
            print("-" * 70)
            print(post_text)
            print("-" * 70)
            print()
            
            # Post via API
            print("Posting via LinkedIn API...")
            result = post_to_linkedin_api(post_text)
            
            if result['success']:
                print(f"✓ Posted successfully!")
                print(f"  Post ID: {result.get('post_id', 'unknown')}")
                
                # Move to Done
                done = vault_path / 'Done'
                done.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                done_path = done / f"{timestamp}_{post_file.name}"
                
                try:
                    post_file.rename(done_path)
                    print(f"✓ Moved to Done/")
                except Exception as e:
                    print(f"⚠️ Could not move file: {e}")
            else:
                print(f"✗ Post failed: {result.get('error', 'Unknown error')}")
                print()
                print("Troubleshooting:")
                print("- Check if access token is valid (not expired)")
                print("- Verify app has w_member_social permission")
                print("- Run: python scripts\\linkedin_get_token.py to refresh token")
            
            print()
    
    print("=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == '__main__':
    main()
