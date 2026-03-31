#!/usr/bin/env python3
"""
LinkedIn Auto-Post - FINAL VERSION

Opens your Profile 2, waits for LinkedIn to load, then posts.

Run: python post_li.py
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
    print(post_text[:60] + "...")
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
        
        print("📍 Going to LinkedIn...")
        page.goto('https://www.linkedin.com', timeout=120000, wait_until='networkidle')
        
        # Wait longer for page and cookies to load
        print("⏳ Waiting for page and session to load (30 seconds)...")
        for i in range(30):
            page.wait_for_timeout(1000)
            if (i + 1) % 5 == 0:
                print(f"  {i+1}s...")
        
        # Check multiple times
        print("🔍 Checking if logged in...")
        logged_in = False
        
        for attempt in range(5):
            # Check profile menu
            if page.query_selector('.global-nav__me'):
                logged_in = True
                break
            
            # Check URL
            if 'feed' in page.url or 'mynetwork' in page.url:
                logged_in = True
                break
            
            # Check for post button
            if page.query_selector('[data-control-name="topbar_post_update"]'):
                logged_in = True
                break
            
            page.wait_for_timeout(3000)
        
        if not logged_in:
            print()
            print("⚠️  NOT DETECTED AS LOGGED IN")
            print()
            print("👉 PLEASE LOGIN IN THE BROWSER NOW")
            print("⏳ Waiting 90 seconds...")
            print()
            
            for i in range(18):
                page.wait_for_timeout(5000)
                if page.query_selector('.global-nav__me'):
                    logged_in = True
                    print("✓ Login detected!")
                    break
                if (i + 1) % 3 == 0:
                    print(f"  Waiting... ({(i+1)*5}s)")
            
            if not logged_in:
                print("⏱️  Timeout")
                browser.close()
                sys.exit(1)
        
        # POST
        print()
        print("🖱️  Start a post...")
        btn = page.query_selector('[data-control-name="topbar_post_update"]')
        if btn:
            btn.click()
            page.wait_for_timeout(5000)
        
        print("⌨️  Content...")
        editor = page.query_selector('[role="textbox"][contenteditable="true"]')
        if editor:
            editor.fill(post_text)
            page.wait_for_timeout(3000)
        
        print("🖱️  Post...")
        submit = page.query_selector('button:has-text("Post")')
        if submit:
            submit.click()
            page.wait_for_timeout(10000)
            print()
            print("✅ POSTED!")
            
            done = vault_path / 'Done'
            done.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            done_path = done / f"{ts}_{post_file.name}"
            post_file.rename(done_path)
        else:
            print("⚠️ Click Post manually")
            page.wait_for_timeout(30000)
        
        browser.close()
        print("Done!")


if __name__ == '__main__':
    main()
