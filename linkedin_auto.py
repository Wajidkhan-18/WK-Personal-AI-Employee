#!/usr/bin/env python3
"""
LinkedIn Auto-Post - Checks if you're logged in, then posts

If already logged in → Auto posts immediately
If not logged in → Waits for login, then posts

Usage:
    python linkedin_auto.py
"""

import sys
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && playwright install chromium")
    sys.exit(1)


SESSION_PATH = Path.home() / '.li_session'


def main():
    vault_path = Path('AI_Employee_Vault').absolute()
    approved = vault_path / 'Approved'
    
    # Find post
    if not approved.exists():
        print("No Approved folder")
        sys.exit(1)
    
    posts = list(approved.glob('LINKEDIN_*.md'))
    if not posts:
        print("No posts in Approved")
        sys.exit(1)
    
    # Get content
    post_file = posts[0]
    content = post_file.read_text(encoding='utf-8')
    
    if '## Post Content' in content:
        start = content.find('## Post Content') + len('## Post Content')
        end = content.find('---', start)
        post_text = content[start:end].strip()
    else:
        print("Invalid post")
        sys.exit(1)
    
    print()
    print("=" * 70)
    print("LinkedIn Auto-Post")
    print("=" * 70)
    print()
    print("Content:")
    print(post_text)
    print()
    print("=" * 70)
    print()
    
    with sync_playwright() as p:
        # Open browser with saved session
        print("🚀 Opening browser with saved session...")
        browser = p.chromium.launch_persistent_context(
            SESSION_PATH,
            headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            timeout=180000
        )
        
        page = browser.pages[0]
        
        print("📍 Going to LinkedIn...")
        page.goto('https://www.linkedin.com', timeout=120000, wait_until='domcontentloaded')
        
        # Wait for page to fully load
        print("⏳ Waiting for page to load (15 seconds)...")
        page.wait_for_timeout(15000)
        
        # CHECK: Are you already logged in?
        print("🔍 Checking if already logged in...")
        
        is_logged_in = False
        
        # Method 1: Check for profile menu
        profile = page.query_selector('.global-nav__me')
        if profile:
            is_logged_in = True
            print("✓ YES - Profile menu detected!")
        
        # Method 2: Check URL
        if not is_logged_in and 'feed' in page.url:
            is_logged_in = True
            print("✓ YES - On feed page!")
        
        # Method 3: Check for "Start a post" button (only visible when logged in)
        if not is_logged_in:
            post_btn = page.query_selector('[data-control-name="topbar_post_update"]')
            if post_btn:
                is_logged_in = True
                print("✓ YES - Post button visible!")
        
        if not is_logged_in:
            print("✗ Not logged in yet")
            print()
            print("⚠️  PLEASE LOGIN NOW IN THE BROWSER")
            print("⏳ Waiting 90 seconds...")
            print()
            
            # Wait for login
            for i in range(18):
                page.wait_for_timeout(5000)
                
                # Check again
                if page.query_selector('.global-nav__me'):
                    print("✓ Login detected!")
                    is_logged_in = True
                    break
                
                if (i + 1) % 3 == 0:
                    print(f"  Waiting... ({(i+1)*5}s)")
            
            if not is_logged_in:
                print()
                print("⏱️  Timeout - please run again after logging in")
                browser.close()
                sys.exit(1)
        
        # YOU'RE LOGGED IN - NOW AUTO POST
        print()
        print("=" * 70)
        print("✅ Logged in - Starting auto-post...")
        print("=" * 70)
        print()
        
        # Click "Start a post"
        print("🖱️  Clicking 'Start a post'...")
        post_btn = page.query_selector('[data-control-name="topbar_post_update"]')
        if post_btn:
            post_btn.click()
            page.wait_for_timeout(5000)
            print("✓ Clicked!")
        else:
            print("⚠️  Waiting for button...")
            page.wait_for_timeout(10000)
            post_btn = page.query_selector('[data-control-name="topbar_post_update"]')
            if post_btn:
                post_btn.click()
                print("✓ Clicked!")
        
        # Wait for dialog
        page.wait_for_timeout(3000)
        
        # Enter content
        print()
        print("⌨️  Entering content...")
        editor = page.query_selector('[role="textbox"][contenteditable="true"]')
        
        if editor:
            editor.fill('')
            page.wait_for_timeout(1000)
            editor.fill(post_text)
            page.wait_for_timeout(3000)
            print("✓ Content entered!")
        else:
            print("⚠️  Waiting for editor...")
            page.wait_for_timeout(10000)
            editor = page.query_selector('[role="textbox"][contenteditable="true"]')
            if editor:
                editor.fill(post_text)
                print("✓ Content entered!")
        
        # Click Post
        print()
        print("🖱️  Clicking 'Post'...")
        submit = page.query_selector('button:has-text("Post")')
        
        if submit:
            submit.click()
            page.wait_for_timeout(10000)
            print()
            print("=" * 70)
            print("🎉 POST SUBMITTED SUCCESSFULLY!")
            print("=" * 70)
            
            # Move to Done
            done = vault_path / 'Done'
            done.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            done_path = done / f"{ts}_{post_file.name}"
            
            try:
                post_file.rename(done_path)
                print(f"✓ Moved to Done/")
            except Exception as e:
                print(f"⚠️  Could not move file: {e}")
            
            browser.close()
            print()
            print("✅ DONE! Check your LinkedIn profile!")
        else:
            print("⚠️  Post button not found")
            print("  Please click Post manually in the browser")
            page.wait_for_timeout(30000)
            browser.close()


if __name__ == '__main__':
    main()
