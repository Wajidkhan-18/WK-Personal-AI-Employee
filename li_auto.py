#!/usr/bin/env python3
"""
LinkedIn Auto-Post - Uses YOUR Chrome where you're ALREADY logged in

This connects to your running Chrome or starts it with your profile.
No need to login again!

Run: python li_auto.py
"""

import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("pip install playwright && playwright install chromium")
    sys.exit(1)


# Your Chrome profile - where you're already logged in to LinkedIn
CHROME_PROFILE = r"C:\Users\adnanlaptop\AppData\Local\Google\Chrome\User Data\Default"
CHROME_EXE = r"C:\Users\adnanlaptop\AppData\Local\Google\Chrome\Application\chrome.exe"


def main():
    vault_path = Path('AI_Employee_Vault').absolute()
    approved = vault_path / 'Approved'
    
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
    print("LinkedIn Auto-Post - Using YOUR Chrome Session")
    print("=" * 70)
    print()
    print("Content:")
    print(post_text)
    print()
    print("=" * 70)
    print()
    
    # Close any running Chrome
    print("⏹️  Closing Chrome...")
    subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], 
                   capture_output=True, timeout=5)
    time.sleep(2)
    
    print("🚀 Opening Chrome with YOUR profile...")
    print("   (where you're already logged in to LinkedIn)")
    print()
    
    with sync_playwright() as p:
        # Launch Chrome with YOUR profile
        browser = p.chromium.launch_persistent_context(
            CHROME_PROFILE,
            headless=False,
            executable_path=CHROME_EXE,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-plugins',
            ],
            timeout=180000
        )
        
        page = browser.pages[0]
        
        print("📍 Going to LinkedIn...")
        page.goto('https://www.linkedin.com', timeout=90000, wait_until='domcontentloaded')
        
        # Wait for page
        print("⏳ Waiting for page to load...")
        page.wait_for_timeout(15000)
        
        # CHECK: Are you logged in?
        print("🔍 Checking if logged in...")
        
        is_logged_in = False
        
        # Check for profile menu
        try:
            profile = page.query_selector('.global-nav__me')
            if profile:
                is_logged_in = True
                print("✓ YES - You are logged in!")
        except:
            pass
        
        # Check URL
        if not is_logged_in and 'feed' in page.url:
            is_logged_in = True
            print("✓ YES - On feed page!")
        
        if not is_logged_in:
            print("✗ Not detecting login")
            print()
            print("⚠️  Are you logged in to LinkedIn in Chrome?")
            print()
            print("If YES: Wait 30 seconds for page to fully load...")
            page.wait_for_timeout(30000)
            
            # Check again
            try:
                if page.query_selector('.global-nav__me'):
                    is_logged_in = True
                    print("✓ Login detected!")
            except:
                pass
            
            if not is_logged_in:
                print()
                print("⚠️  Please login to LinkedIn in the browser")
                print("  Then run this script again")
                browser.close()
                sys.exit(1)
        
        # AUTO POST
        print()
        print("=" * 70)
        print("🚀 Starting auto-post...")
        print("=" * 70)
        print()
        
        # Click Start a post
        print("🖱️  1/3 Clicking 'Start a post'...")
        btn = page.query_selector('[data-control-name="topbar_post_update"]')
        if btn:
            btn.click()
            page.wait_for_timeout(5000)
            print("✓ Clicked!")
        else:
            print("⚠️  Waiting for button...")
            page.wait_for_timeout(10000)
            btn = page.query_selector('[data-control-name="topbar_post_update"]')
            if btn:
                btn.click()
                print("✓ Clicked!")
        
        # Enter content
        print()
        print("🖱️  2/3 Entering content...")
        editor = page.query_selector('[role="textbox"][contenteditable="true"]')
        if editor:
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
        print("🖱️  3/3 Clicking 'Post'...")
        submit = page.query_selector('button:has-text("Post")')
        if submit:
            submit.click()
            page.wait_for_timeout(10000)
            print()
            print("=" * 70)
            print("🎉 POST SUBMITTED!")
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
                print(f"⚠️  Could not move: {e}")
            
            browser.close()
            print()
            print("✅ DONE! Check your LinkedIn!")
        else:
            print("⚠️  Post button not found")
            print("  Please click Post manually")
            page.wait_for_timeout(30000)
            browser.close()


if __name__ == '__main__':
    main()
