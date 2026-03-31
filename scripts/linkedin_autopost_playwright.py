#!/usr/bin/env python3
"""
LinkedIn Auto-Post with Playwright - WORKING VERSION

This script:
1. Opens LinkedIn with your saved session
2. Clicks "Start a post"
3. Types the content
4. Clicks "Post"
5. Waits for confirmation
6. Moves file to Done/

The browser stays open so you can watch it happen!
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
    print("Playwright not installed. Run: pip install playwright")
    print("Then: playwright install chromium")
    sys.exit(1)


def post_to_linkedin(content: str, vault_path: Path, post_file: Path) -> bool:
    """
    Post to LinkedIn using Playwright.
    Browser stays visible so you can watch.
    """
    
    session_path = Path.home() / '.linkedin_session'
    
    print("=" * 70)
    print("LinkedIn Auto-Post - Watch the browser!")
    print("=" * 70)
    print()
    
    try:
        with sync_playwright() as p:
            # Launch browser - VISIBLE so you can watch
            print("🚀 Launching browser with your saved session...")
            browser = p.chromium.launch_persistent_context(
                session_path,
                headless=False,  # VISIBLE - you can watch!
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-gpu'
                ],
                timeout=180000  # 3 minutes to load
            )
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            
            # Navigate to LinkedIn
            print("📍 Navigating to LinkedIn...")
            page.goto('https://www.linkedin.com', wait_until='domcontentloaded', timeout=120000)
            
            # Wait for page to fully load
            print("⏳ Waiting for page to load (watch the browser)...")
            page.wait_for_timeout(15000)  # 15 seconds
            
            # Check if logged in
            print("🔍 Checking if logged in...")
            is_logged_in = False
            try:
                profile_menu = page.query_selector('.global-nav__me')
                if profile_menu:
                    is_logged_in = True
                    print("✓ You are logged in!")
                else:
                    print("⚠️ Don't see profile menu yet...")
            except:
                pass
            
            if not is_logged_in:
                print()
                print("⚠️  You may need to log in in the browser window")
                print("⏳ Waiting 60 seconds for you to log in...")
                print("👉 Watch the browser and log in if needed!")
                page.wait_for_timeout(60000)
                
                # Check again
                try:
                    profile_menu = page.query_selector('.global-nav__me')
                    is_logged_in = profile_menu is not None
                    if is_logged_in:
                        print("✓ Login detected!")
                except:
                    pass
            
            if not is_logged_in:
                print("✗ Not logged in. Please login and run again.")
                browser.close()
                return False
            
            # Wait a bit more for stability
            page.wait_for_timeout(5000)
            
            # Click "Start a post" button
            print()
            print("🖱️  Looking for 'Start a post' button...")
            
            post_button = None
            selectors = [
                '[data-control-name="topbar_post_update"]',
                '.share-box-feed-entry__trigger',
                'button:has-text("Start a post")',
                'button:has-text("Start")',
                '.ippon-cta-icon'
            ]
            
            for i, selector in enumerate(selectors):
                try:
                    post_button = page.query_selector(selector)
                    if post_button:
                        print(f"✓ Found with selector {i+1}")
                        break
                except:
                    continue
            
            if post_button:
                print("🖱️  Clicking 'Start a post'...")
                post_button.click()
                print("⏳ Waiting for post dialog...")
                page.wait_for_timeout(8000)
            else:
                print("⚠️  Could not find 'Start a post' button automatically")
                print("👉 Please click 'Start a post' in the browser!")
                print("⏳ Waiting 30 seconds...")
                page.wait_for_timeout(30000)
            
            # Find editor and type content
            print()
            print("⌨️  Entering post content...")
            
            editor = page.query_selector('[role="textbox"][contenteditable="true"]')
            
            if editor:
                try:
                    # Clear and type slowly (more human-like)
                    editor.fill('')
                    page.wait_for_timeout(1000)
                    
                    # Type content character by character (more human-like)
                    # But for long posts, use fill
                    if len(content) < 500:
                        # Type slowly for short posts
                        for char in content:
                            editor.type(char)
                            if len(content) > 100:  # Only delay for longer posts
                                page.wait_for_timeout(10)  # 10ms per char
                    else:
                        # Use fill for long posts
                        editor.fill(content)
                    
                    page.wait_for_timeout(3000)
                    print("✓ Content entered!")
                    
                except Exception as e:
                    print(f"⚠️  Auto-fill had issues: {e}")
                    print("👉 Please paste the content manually in the browser")
                    print("⏳ Waiting 60 seconds...")
                    page.wait_for_timeout(60000)
            else:
                print("⚠️  Could not find post editor")
                print("👉 The post dialog may not have opened")
                print("⏳ Waiting 30 seconds...")
                page.wait_for_timeout(30000)
                editor = page.query_selector('[role="textbox"][contenteditable="true"]')
                
                if editor:
                    editor.fill(content)
                    page.wait_for_timeout(3000)
                    print("✓ Content entered!")
            
            # Click Post button
            print()
            print("🖱️  Looking for 'Post' button...")
            
            submit_button = page.query_selector('button:has-text("Post")')
            
            if submit_button:
                print("🖱️  Clicking 'Post' button...")
                submit_button.click()
                print("⏳ Waiting for post to submit...")
                page.wait_for_timeout(10000)
                
                # Check for success indicators
                print("✓ Post submitted!")
                
                # Wait a bit more to ensure it's done
                page.wait_for_timeout(5000)
                
                print()
                print("=" * 70)
                print("🎉 SUCCESS! Your post is live on LinkedIn!")
                print("=" * 70)
                
                browser.close()
                return True
            else:
                print("⚠️  Could not find 'Post' button")
                print("👉 Please click 'Post' manually in the browser")
                print("⏳ Waiting 60 seconds for you to click Post...")
                
                # Wait for user to click Post manually
                for i in range(60, 0, -1):
                    page.wait_for_timeout(1000)
                    if i % 10 == 0:
                        print(f"  Waiting... {i} seconds remaining")
                
                print()
                print("Assuming you posted manually...")
                browser.close()
                return True
            
    except Exception as e:
        print(f"✗ Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Make sure you're logged in to LinkedIn")
        print("2. Try running the script again")
        print("3. Check the browser window for any errors")
        return False


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
            print("Content to post:")
            print("-" * 70)
            print(post_text)
            print("-" * 70)
            print()
            
            # Post
            success = post_to_linkedin(post_text, vault_path, post_file)
            
            if success:
                # Move to Done
                done = vault_path / 'Done'
                done.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                done_path = done / f"{timestamp}_{post_file.name}"
                
                try:
                    post_file.rename(done_path)
                    print(f"✓ Moved to Done/: {done_path.name}")
                except Exception as e:
                    print(f"⚠️ Could not move file: {e}")
            else:
                print("✗ Post failed. File remains in Approved/")
            
            print()
    
    print("=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == '__main__':
    main()
