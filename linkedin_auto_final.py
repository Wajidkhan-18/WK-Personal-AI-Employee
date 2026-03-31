#!/usr/bin/env python3
"""
LinkedIn Auto-Post - Connects to YOUR already-logged-in Chrome

This connects to your existing Chrome browser where you're already logged in.
No need to login again!

Usage:
    1. Close all Chrome windows first
    2. Run this script
    3. It will open Chrome with your session
    4. Auto-posts to LinkedIn
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && playwright install chromium")
    sys.exit(1)


def main():
    vault_path = Path('AI_Employee_Vault').absolute()
    approved = vault_path / 'Approved'
    
    # Find post to publish
    if not approved.exists():
        print("No Approved folder.")
        return
    
    approved_posts = list(approved.glob('LINKEDIN_*.md'))
    if not approved_posts:
        print("No posts in Approved folder.")
        return
    
    # Get post content
    post_file = approved_posts[0]
    content = post_file.read_text(encoding='utf-8')
    
    if '## Post Content' in content:
        start = content.find('## Post Content') + len('## Post Content')
        end = content.find('---', start)
        post_text = content[start:end].strip()
    else:
        print("No post content found")
        return
    
    print("=" * 70)
    print("LinkedIn Auto-Post - Using Your Browser Session")
    print("=" * 70)
    print()
    print("Content to post:")
    print("-" * 70)
    print(post_text)
    print("-" * 70)
    print()
    
    # Use Chrome's default user data directory
    chrome_path = r"C:\Users\adnanlaptop\AppData\Local\Google\Chrome\User Data"
    
    print("🚀 Opening Chrome with YOUR session...")
    print()
    print("IMPORTANT: If Chrome opens with login page, close it and:")
    print("1. Open Chrome normally")
    print("2. Go to linkedin.com and login")
    print("3. Close Chrome")
    print("4. Run this script again")
    print()
    
    with sync_playwright() as p:
        # Launch Chrome with your user data
        browser = p.chromium.launch_persistent_context(
            chrome_path,
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu',
                '--start-maximized'
            ],
            timeout=120000
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        print("📍 Going to LinkedIn...")
        page.goto('https://www.linkedin.com', wait_until='domcontentloaded', timeout=60000)
        
        # Wait for page
        page.wait_for_timeout(10000)
        
        # Check if logged in
        print("🔍 Checking if logged in...")
        try:
            profile = page.query_selector('.global-nav__me')
            if profile:
                print("✓ You are logged in!")
            else:
                print("⚠️ Not logged in. Please login and run again.")
                browser.close()
                return
        except:
            print("⚠️ Could not detect login")
            browser.close()
            return
        
        # Click Start a post
        print()
        print("🖱️ Clicking 'Start a post'...")
        
        post_btn = page.query_selector('[data-control-name="topbar_post_update"]')
        if post_btn:
            post_btn.click()
            page.wait_for_timeout(5000)
            print("✓ Clicked!")
        else:
            print("⚠️ Button not found, waiting...")
            page.wait_for_timeout(15000)
        
        # Enter content
        print()
        print("⌨️ Entering content...")
        
        editor = page.query_selector('[role="textbox"][contenteditable="true"]')
        if editor:
            editor.fill('')
            page.wait_for_timeout(1000)
            editor.fill(post_text)
            page.wait_for_timeout(3000)
            print("✓ Content entered!")
        else:
            print("⚠️ Editor not found")
            page.wait_for_timeout(15000)
            editor = page.query_selector('[role="textbox"][contenteditable="true"]')
            if editor:
                editor.fill(post_text)
                print("✓ Content entered!")
        
        # Click Post
        print()
        print("🖱️ Clicking 'Post'...")
        
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
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            done_path = done / f"{timestamp}_{post_file.name}"
            
            try:
                post_file.rename(done_path)
                print(f"✓ Moved to Done/")
            except:
                pass
            
            browser.close()
            print()
            print("Done! Check your LinkedIn profile!")
        else:
            print("⚠️ Post button not found")
            print("Please click Post manually in the browser")
            browser.close()


if __name__ == '__main__':
    main()
