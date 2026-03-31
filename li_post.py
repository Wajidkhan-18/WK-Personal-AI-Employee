#!/usr/bin/env python3
"""
LinkedIn Auto-Post - KEEPS BROWSER OPEN

Run: python li_post.py
"""

import sys
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("pip install playwright && playwright install chromium")
    sys.exit(1)


SESSION = Path.home() / '.li_session'


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
        print("🚀 Opening browser...")
        browser = p.chromium.launch_persistent_context(
            SESSION,
            headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            timeout=300000
        )
        
        page = browser.pages[0]
        
        print("📍 LinkedIn...")
        page.goto('https://www.linkedin.com', timeout=120000)
        page.wait_for_timeout(20000)
        
        # Check login
        print("🔍 Checking login...")
        logged_in = page.query_selector('.global-nav__me') is not None
        
        if not logged_in:
            print()
            print("⚠️  NOT LOGGED IN")
            print("👉 LOGIN IN THE BROWSER NOW")
            print("⏳ Waiting 120 seconds...")
            print()
            
            for i in range(24):
                page.wait_for_timeout(5000)
                if page.query_selector('.global-nav__me'):
                    print("✓ Logged in!")
                    logged_in = True
                    break
                if (i + 1) % 4 == 0:
                    print(f"  Waiting... ({(i+1)*5}s)")
            
            if not logged_in:
                print("⏱️  Timeout")
                print()
                print("KEEP THE BROWSER OPEN - I'll wait 2 more minutes")
                print("Login and the script will continue...")
                
                for i in range(24):
                    page.wait_for_timeout(5000)
                    if page.query_selector('.global-nav__me'):
                        print("✓ Login detected!")
                        logged_in = True
                        break
                
                if not logged_in:
                    print("Still not logged in. Close browser and run again.")
                    input("Press Enter to close...")
                    browser.close()
                    sys.exit(1)
        
        # POST
        print()
        print("🖱️  Start a post...")
        btn = page.query_selector('[data-control-name="topbar_post_update"]')
        if btn:
            btn.click()
            page.wait_for_timeout(5000)
            print("✓ Clicked!")
        
        print("⌨️  Content...")
        editor = page.query_selector('[role="textbox"][contenteditable="true"]')
        if editor:
            editor.fill(post_text)
            page.wait_for_timeout(3000)
            print("✓ Done!")
        
        print("🖱️  Post...")
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
        else:
            print("⚠️ Click Post manually")
            page.wait_for_timeout(60000)
        
        browser.close()
        print("Done!")


if __name__ == '__main__':
    main()
