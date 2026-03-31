#!/usr/bin/env python3
"""
LinkedIn Auto-Post with Playwright - FINAL WORKING VERSION

This opens browser, you login once, then it auto-posts.
Browser stays visible so you can watch everything.
"""

import sys
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
    
    if not approved.exists():
        print("No Approved folder.")
        return
    
    approved_posts = list(approved.glob('LINKEDIN_*.md'))
    
    if not approved_posts:
        print("No posts in Approved.")
        return
    
    print("=" * 70)
    print("LinkedIn Auto-Post - Playwright")
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
            print("IMPORTANT:")
            print("1. Browser will open")
            print("2. If you see login → Log in to LinkedIn")
            print("3. When you see your feed → Script will auto-post")
            print("4. Watch the browser - everything happens automatically!")
            print()
            
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    session_path,
                    headless=False,  # VISIBLE
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--start-maximized'
                    ],
                    timeout=600000  # 10 minutes
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                print("📍 Going to LinkedIn...")
                page.goto('https://www.linkedin.com', wait_until='domcontentloaded', timeout=120000)
                
                # Wait for login - check every 5 seconds
                print()
                print("⏳ Waiting for you to login (max 2 minutes)...")
                print("👉 Look at the browser and login if needed!")
                print()
                
                logged_in = False
                for i in range(24):  # 24 x 5 seconds = 2 minutes
                    page.wait_for_timeout(5000)
                    
                    try:
                        # Check for profile menu (indicates logged in)
                        profile = page.query_selector('.global-nav__me')
                        if profile:
                            print("✓ Logged in detected!")
                            logged_in = True
                            break
                        
                        # Also check URL
                        if 'feed' in page.url or 'mynetwork' in page.url:
                            print("✓ On feed page - logged in!")
                            logged_in = True
                            break
                            
                    except:
                        pass
                    
                    if (i + 1) % 6 == 0:
                        print(f"  Still waiting... ({(i+1)*5}s)")
                
                if not logged_in:
                    print()
                    print("⚠️ Timeout - not logged in")
                    print("Please login in the browser and run script again")
                    browser.close()
                    return
                
                # Wait a bit for page to stabilize
                page.wait_for_timeout(5000)
                
                # Click "Start a post"
                print()
                print("🖱️  Clicking 'Start a post'...")
                
                post_clicked = False
                selectors = [
                    '[data-control-name="topbar_post_update"]',
                    '.share-box-feed-entry__trigger',
                    'button:has-text("Start a post")',
                    'button:has-text("Start")'
                ]
                
                for sel in selectors:
                    try:
                        btn = page.query_selector(sel)
                        if btn:
                            btn.click()
                            print("✓ Clicked!")
                            post_clicked = True
                            break
                    except:
                        continue
                
                if not post_clicked:
                    print("⚠️  Could not click automatically")
                    print("  Please click 'Start a post' in browser")
                    print("  Waiting 30 seconds...")
                    page.wait_for_timeout(30000)
                
                # Wait for dialog
                page.wait_for_timeout(5000)
                
                # Enter content
                print()
                print("⌨️  Entering content...")
                
                editor = page.query_selector('[role="textbox"][contenteditable="true"]')
                if editor:
                    try:
                        editor.fill('')
                        page.wait_for_timeout(1000)
                        editor.fill(post_text)
                        page.wait_for_timeout(3000)
                        print("✓ Content entered!")
                    except Exception as e:
                        print(f"⚠️  Could not auto-enter: {e}")
                        print("  Please paste content manually")
                        print("  Waiting 60 seconds...")
                        page.wait_for_timeout(60000)
                else:
                    print("⚠️  Editor not found")
                    print("  Waiting for editor...")
                    page.wait_for_timeout(30000)
                    editor = page.query_selector('[role="textbox"][contenteditable="true"]')
                    if editor:
                        editor.fill(post_text)
                        print("✓ Content entered!")
                
                # Click Post button
                print()
                print("🖱️  Clicking 'Post'...")
                
                submit = page.query_selector('button:has-text("Post")')
                if submit:
                    try:
                        submit.click()
                        page.wait_for_timeout(10000)
                        print()
                        print("=" * 70)
                        print("🎉 POST SUBMITTED SUCCESSFULLY!")
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
                        
                    except Exception as e:
                        print(f"⚠️  Click failed: {e}")
                        print("  Please click Post manually")
                        page.wait_for_timeout(60000)
                else:
                    print("⚠️  Post button not found")
                    print("  Please click Post manually")
                    page.wait_for_timeout(60000)
                
                browser.close()
                print()
                print("Done!")


if __name__ == '__main__':
    main()
