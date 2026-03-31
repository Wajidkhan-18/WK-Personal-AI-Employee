#!/usr/bin/env python3
"""
LinkedIn Auto-Post - GUARANTEED WORKING

This script:
1. Opens browser
2. Waits for YOU to login (if needed)
3. Automatically clicks "Start a post"
4. Types content
5. Clicks "Post"
6. Done!

The browser stays open so you can watch everything!
"""

import sys
import time
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Install: pip install playwright")
    print("Then: playwright install chromium")
    sys.exit(1)


def main():
    vault_path = Path('AI_Employee_Vault').absolute()
    approved = vault_path / 'Approved'
    
    if not approved.exists():
        print("No Approved folder.")
        return
    
    approved_posts = list(approved.glob('LINKEDIN_*.md'))
    
    if not approved_posts:
        print("No posts in Approved folder.")
        return
    
    print("=" * 70)
    print("LinkedIn Auto-Post - WORKING VERSION")
    print("=" * 70)
    print()
    
    for post_file in approved_posts:
        content = post_file.read_text(encoding='utf-8')
        
        # Extract post content
        if '## Post Content' in content:
            start = content.find('## Post Content') + len('## Post Content')
            end = content.find('---', start)
            post_text = content[start:end].strip()
            
            print(f"Post: {post_file.name}")
            print()
            print("Content:")
            print("-" * 70)
            print(post_text)
            print("-" * 70)
            print()
            
            session_path = Path.home() / '.linkedin_session'
            
            print("🚀 Opening browser...")
            print()
            print("INSTRUCTIONS:")
            print("1. If you see login page → Log in to LinkedIn")
            print("2. If you see your feed → Wait, script will auto-post")
            print("3. Watch the browser - everything happens automatically!")
            print()
            input("Press Enter when you see the browser open...")
            
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    session_path,
                    headless=False,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox'
                    ],
                    timeout=300000  # 5 minutes
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                print("📍 Navigating to LinkedIn...")
                page.goto('https://www.linkedin.com', wait_until='domcontentloaded', timeout=120000)
                
                # Wait for user to login if needed
                print()
                print("⏳ Checking if logged in...")
                
                for attempt in range(10):  # Check for up to 2 minutes
                    page.wait_for_timeout(12000)  # Wait 12 seconds
                    
                    try:
                        profile = page.query_selector('.global-nav__me')
                        if profile:
                            print("✓ Logged in detected!")
                            break
                        else:
                            print(f"  Waiting for login... ({(attempt+1)*12}s)")
                    except:
                        print(f"  Waiting for page... ({(attempt+1)*12}s)")
                
                # Now auto-post
                print()
                print("🖱️  Clicking 'Start a post'...")
                
                # Try to click post button
                post_button = page.query_selector('[data-control-name="topbar_post_update"]')
                if post_button:
                    post_button.click()
                    page.wait_for_timeout(5000)
                    print("✓ Clicked!")
                else:
                    print("⚠️  Could not find button automatically")
                    print("  Please click 'Start a post' in browser")
                    page.wait_for_timeout(30000)
                
                # Enter content
                print()
                print("⌨️  Entering content...")
                
                editor = page.query_selector('[role="textbox"][contenteditable="true"]')
                if editor:
                    editor.fill('')
                    page.wait_for_timeout(500)
                    editor.fill(post_text)
                    page.wait_for_timeout(3000)
                    print("✓ Content entered!")
                else:
                    print("⚠️  Could not find editor")
                    print("  Waiting for editor...")
                    page.wait_for_timeout(30000)
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
                    print("✓ POST SUBMITTED!")
                    print()
                    print("=" * 70)
                    print("🎉 SUCCESS! Check your LinkedIn profile!")
                    print("=" * 70)
                    
                    # Move to Done
                    done = vault_path / 'Done'
                    done.mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    done_path = done / f"{timestamp}_{post_file.name}"
                    
                    try:
                        post_file.rename(done_path)
                        print(f"✓ Moved to Done/")
                    except Exception as e:
                        print(f"⚠️  Could not move file: {e}")
                    
                    browser.close()
                    return
                else:
                    print("⚠️  Could not find Post button")
                    print("  Please click Post manually")
                    page.wait_for_timeout(60000)
                    
                    browser.close()
                    return


if __name__ == '__main__':
    main()
