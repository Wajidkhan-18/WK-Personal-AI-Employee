#!/usr/bin/env python3
"""
LinkedIn Poster V2 - Working Command Line Version

Usage:
    python linkedin_poster_v2.py --post "Your post content" --hashtags AI automation testing --wait 5

This will:
1. Open browser
2. Go to LinkedIn
3. Wait for you to login (if needed)
4. Click "Start a post"
5. Type your content
6. Click "Post"
7. Done!
"""

import argparse
import sys
import time
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright")
    print("Then: playwright install chromium")
    sys.exit(1)


SESSION_PATH = Path.home() / '.li_session_v2'


def post_to_linkedin(content: str, hashtags: list, wait_time: int):
    """Post to LinkedIn using Playwright."""
    
    full_text = content + "\n\n" + " ".join([f"#{tag}" for tag in hashtags])
    
    print()
    print("=" * 70)
    print("LinkedIn Poster V2")
    print("=" * 70)
    print()
    print(f"Post: {content[:60]}...")
    print(f"Hashtags: {' '.join(hashtags)}")
    print(f"Wait: {wait_time}s")
    print()
    print("=" * 70)
    print()
    
    with sync_playwright() as p:
        # Launch browser
        print("🚀 Opening browser...")
        browser = p.chromium.launch_persistent_context(
            SESSION_PATH,
            headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            timeout=300000
        )
        
        page = browser.pages[0]
        
        # Go to LinkedIn
        print("📍 Navigating to LinkedIn...")
        page.goto('https://www.linkedin.com', timeout=120000, wait_until='domcontentloaded')
        
        # Initial wait
        print(f"⏳ Waiting {wait_time} seconds...")
        page.wait_for_timeout(wait_time * 1000)
        
        # Check if logged in
        print("🔍 Checking login...")
        logged_in = page.query_selector('.global-nav__me') is not None
        
        if not logged_in:
            print()
            print("⚠️  NOT LOGGED IN")
            print()
            print("👉 PLEASE LOGIN IN THE BROWSER NOW")
            print("⏳ Waiting 90 seconds...")
            print()
            
            for i in range(18):
                page.wait_for_timeout(5000)
                
                if page.query_selector('.global-nav__me'):
                    print("✓ Logged in detected!")
                    logged_in = True
                    break
                
                if (i + 1) % 3 == 0:
                    print(f"  Waiting... ({(i+1)*5}s)")
            
            if not logged_in:
                print()
                print("⏱️  Timeout - please login and run again")
                browser.close()
                return False
        
        # Wait for page to stabilize
        page.wait_for_timeout(5000)
        
        # Click "Start a post"
        print()
        print("🖱️  Clicking 'Start a post'...")
        
        post_btn = page.query_selector('[data-control-name="topbar_post_update"]')
        if post_btn:
            post_btn.click()
            page.wait_for_timeout(5000)
            print("✓ Clicked!")
        else:
            print("⚠️  Button not found, waiting...")
            page.wait_for_timeout(15000)
        
        # Enter content
        print()
        print("⌨️  Entering content...")
        
        editor = page.query_selector('[role="textbox"][contenteditable="true"]')
        if editor:
            try:
                editor.fill('')
                page.wait_for_timeout(1000)
                editor.fill(full_text)
                page.wait_for_timeout(3000)
                print("✓ Content entered!")
            except Exception as e:
                print(f"⚠️  Could not auto-enter: {e}")
                print("  Please paste content manually")
                page.wait_for_timeout(30000)
        else:
            print("⚠️  Editor not found, waiting...")
            page.wait_for_timeout(15000)
            editor = page.query_selector('[role="textbox"][contenteditable="true"]')
            if editor:
                editor.fill(full_text)
                print("✓ Content entered!")
        
        # Click Post
        print()
        print("🖱️  Clicking 'Post'...")
        
        submit = page.query_selector('button:has-text("Post")')
        if submit:
            try:
                submit.click()
                page.wait_for_timeout(10000)
                print()
                print("=" * 70)
                print("✅ POST SUBMITTED SUCCESSFULLY!")
                print("=" * 70)
                browser.close()
                return True
            except Exception as e:
                print(f"⚠️  Click failed: {e}")
                print("  Please click Post manually in the browser")
                page.wait_for_timeout(30000)
        else:
            print("⚠️  Post button not found")
            print("  Please click Post manually")
            page.wait_for_timeout(30000)
        
        browser.close()
        print()
        print("Done!")
        return True


def main():
    parser = argparse.ArgumentParser(
        description='LinkedIn Poster V2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python linkedin_poster_v2.py --post "Hello LinkedIn!" --hashtags AI automation
    python linkedin_poster_v2.py -p "My post" -t "tech coding" -w 10
        """
    )
    
    parser.add_argument(
        '--post', '-p',
        type=str,
        required=True,
        help='Post content'
    )
    
    parser.add_argument(
        '--hashtags', '-t',
        type=str,
        default='AI automation',
        help='Hashtags (space separated)'
    )
    
    parser.add_argument(
        '--wait', '-w',
        type=int,
        default=5,
        help='Wait time before posting (seconds)'
    )
    
    args = parser.parse_args()
    
    # Parse hashtags
    hashtags = args.hashtags.split()
    
    # Post
    success = post_to_linkedin(args.post, hashtags, args.wait)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
