#!/usr/bin/env python3
"""
LinkedIn Auto-Post - Simple Working Version

Usage:
    python li_post_auto.py

Opens your Chrome, goes to LinkedIn, and posts.
"""

import sys
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("pip install playwright && playwright install chromium")
    sys.exit(1)


PROFILE = r"C:\Users\adnanlaptop\AppData\Local\Google\Chrome\User Data\Profile 2"
CHROME = r"C:\Users\adnanlaptop\AppData\Local\Google\Chrome\Application\chrome.exe"


def main():
    vault_path = Path('AI_Employee_Vault').absolute()
    approved = vault_path / 'Approved'
    
    if not approved.exists():
        print("No Approved folder")
        sys.exit(1)
    
    posts = list(approved.glob('LINKEDIN_*.md'))
    if not posts:
        print("No posts")
        sys.exit(1)
    
    post_file = posts[0]
    content = post_file.read_text(encoding='utf-8')
    
    if '## Post Content' in content:
        start = content.find('## Post Content') + len('## Post Content')
        end = content.find('---', start)
        post_text = content[start:end].strip()
    else:
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("LinkedIn Auto-Post")
    print("=" * 60)
    print()
    print(post_text[:80] + "...")
    print()
    print("=" * 60)
    print()
    
    with sync_playwright() as p:
        print("🚀 Opening Chrome Profile 2...")
        browser = p.chromium.launch_persistent_context(
            PROFILE,
            headless=False,
            executable_path=CHROME,
            args=['--disable-blink-features=AutomationControlled'],
            timeout=180000
        )
        
        page = browser.pages[0]
        
        print("📍 LinkedIn...")
        try:
            page.goto('https://www.linkedin.com', timeout=90000)
        except:
            print("⚠️ Navigation issue, continuing...")
        
        print("⏳ Waiting 40 seconds for page to fully load...")
        page.wait_for_timeout(40000)
        
        # Try to detect login
        print("🔍 Checking login...")
        logged_in = False
        
        try:
            # Try multiple checks
            if page.query_selector('.global-nav__me'):
                logged_in = True
            elif 'feed' in page.url:
                logged_in = True
            elif page.query_selector('[data-control-name="topbar_post_update"]'):
                logged_in = True
        except:
            pass
        
        if not logged_in:
            print()
            print("⚠️  NOT LOGGED IN")
            print("👉 LOGIN IN THE BROWSER NOW")
            print("⏳ Waiting 120 seconds...")
            print()
            
            for i in range(24):
                try:
                    page.wait_for_timeout(5000)
                    if page.query_selector('.global-nav__me'):
                        print("✓ Login detected!")
                        logged_in = True
                        break
                except:
                    pass
                
                if (i + 1) % 4 == 0:
                    print(f"  Waiting... ({(i+1)*5}s)")
            
            if not logged_in:
                print("⏱️ Timeout")
                browser.close()
                sys.exit(1)
        
        # POST
        print()
        print("🖱️  Start a post...")
        try:
            btn = page.query_selector('[data-control-name="topbar_post_update"]')
            if btn:
                btn.click()
                page.wait_for_timeout(5000)
        except:
            pass
        
        print("⌨️  Content...")
        try:
            editor = page.query_selector('[role="textbox"][contenteditable="true"]')
            if editor:
                editor.fill(post_text)
                page.wait_for_timeout(3000)
        except:
            pass
        
        print("🖱️  Post...")
        try:
            submit = page.query_selector('button:has-text("Post")')
            if submit:
                submit.click()
                page.wait_for_timeout(10000)
                print()
                print("✅ POSTED!")
                
                # Move to Done
                done = vault_path / 'Done'
                done.mkdir(parents=True, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                done_path = done / f"{ts}_{post_file.name}"
                post_file.rename(done_path)
        except:
            print("⚠️ Click Post manually")
        
        browser.close()
        print("Done!")


if __name__ == '__main__':
    main()
