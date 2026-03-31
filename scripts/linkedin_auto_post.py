#!/usr/bin/env python3
"""
LinkedIn Auto-Poster - Attempt automated posting
With retry logic and better error handling
"""

import sys
import time
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Run: pip install playwright")
    sys.exit(1)


def post_to_linkedin(content: str, vault_path: Path, post_file: Path) -> bool:
    """
    Post to LinkedIn with retry logic.
    Returns True if successful.
    """
    
    session_path = Path.home() / '.linkedin_session'
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            print(f"\nAttempt {attempt + 1}/{max_retries}")
            print("-" * 50)
            
            with sync_playwright() as p:
                print("Launching browser...")
                browser = p.chromium.launch_persistent_context(
                    session_path,
                    headless=False,  # Keep visible for debugging
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox'
                    ],
                    timeout=120000
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                # Navigate to LinkedIn
                print("Navigating to LinkedIn...")
                try:
                    page.goto('https://www.linkedin.com', 
                             wait_until='domcontentloaded', 
                             timeout=90000)
                except PlaywrightTimeout:
                    print("⚠️ LinkedIn loading slow, continuing anyway...")
                
                # Wait for page to stabilize
                print("Waiting for page to load...")
                page.wait_for_timeout(10000)  # 10 seconds
                
                # Check if logged in
                is_logged_in = False
                try:
                    profile_menu = page.query_selector('.global-nav__me')
                    if profile_menu:
                        is_logged_in = True
                        print("✓ Logged in detected")
                except:
                    pass
                
                if not is_logged_in:
                    print("⚠️ May not be logged in. Please login in the browser.")
                    print("Waiting 60 seconds for manual login...")
                    page.wait_for_timeout(60000)
                    
                    # Check again
                    profile_menu = page.query_selector('.global-nav__me')
                    is_logged_in = profile_menu is not None
                
                if not is_logged_in:
                    print("✗ Not logged in. Aborting.")
                    browser.close()
                    return False
                
                # Try to click "Start a post"
                print("Looking for 'Start a post' button...")
                post_button = None
                
                selectors = [
                    '[data-control-name="topbar_post_update"]',
                    '.share-box-feed-entry__trigger',
                    'button:has-text("Start a post")',
                    'button:has-text("Start")'
                ]
                
                for selector in selectors:
                    try:
                        post_button = page.query_selector(selector)
                        if post_button:
                            print(f"  Found with selector: {selector}")
                            break
                    except:
                        continue
                
                if not post_button:
                    print("⚠️ Could not find 'Start a post' button")
                    print("Waiting 30 seconds for you to click it manually...")
                    page.wait_for_timeout(30000)
                else:
                    print("Clicking 'Start a post'...")
                    post_button.click()
                    page.wait_for_timeout(5000)
                
                # Find editor and type content
                print("Entering post content...")
                editor = page.query_selector('[role="textbox"][contenteditable="true"]')
                
                if not editor:
                    print("⚠️ Could not find editor. Waiting 30 seconds...")
                    page.wait_for_timeout(30000)
                    editor = page.query_selector('[role="textbox"][contenteditable="true"]')
                
                if editor:
                    try:
                        editor.fill('')
                        page.wait_for_timeout(500)
                        editor.fill(content)
                        page.wait_for_timeout(3000)
                        print("✓ Content entered")
                    except Exception as e:
                        print(f"⚠️ Could not auto-fill content: {e}")
                        print("Please paste the content manually")
                        print("Waiting 60 seconds...")
                        page.wait_for_timeout(60000)
                else:
                    print("✗ Could not find editor")
                    browser.close()
                    return False
                
                # Click Post button
                print("Looking for 'Post' button...")
                submit_button = page.query_selector('button:has-text("Post")')
                
                if submit_button:
                    print("Clicking 'Post'...")
                    submit_button.click()
                    page.wait_for_timeout(5000)
                    print("✓ Post submitted!")
                    
                    # Wait for confirmation
                    page.wait_for_timeout(5000)
                    
                    browser.close()
                    return True
                else:
                    print("⚠️ Could not find 'Post' button")
                    print("Please click Post manually")
                    print("Waiting 60 seconds...")
                    page.wait_for_timeout(60000)
                    
                    browser.close()
                    return True  # Assume user posted manually
            
        except Exception as e:
            print(f"✗ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print("Retrying...")
                time.sleep(5)
            else:
                return False
    
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
    
    print("=" * 70)
    print("LinkedIn Auto-Poster")
    print("=" * 70)
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
