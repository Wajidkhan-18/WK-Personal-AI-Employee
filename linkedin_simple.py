#!/usr/bin/env python3
"""
LinkedIn Auto-Post - Simple Working Version

Closes Chrome, reopens with your profile, posts automatically.

Run: python linkedin_simple.py
"""

import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && playwright install chromium")
    sys.exit(1)


# Your Chrome profile
CHROME_PROFILE = r"C:\Users\adnanlaptop\AppData\Local\Google\Chrome\User Data"
CHROME_EXE = r"C:\Users\adnanlaptop\AppData\Local\Google\Chrome\Application\chrome.exe"


def main():
    vault_path = Path('AI_Employee_Vault').absolute()
    approved = vault_path / 'Approved'
    
    if not approved.exists():
        print("No Approved folder.")
        sys.exit(1)
    
    posts = list(approved.glob('LINKEDIN_*.md'))
    if not posts:
        print("No posts in Approved.")
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
    
    # Close all Chrome windows
    print("⏹️  Closing Chrome...")
    subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], 
                   capture_output=True, timeout=10)
    time.sleep(2)
    
    print("🚀 Opening Chrome with your LinkedIn session...")
    print()
    print("WATCH THE BROWSER - it will auto-post!")
    print()
    
    with sync_playwright() as p:
        # Launch Chrome with your profile
        browser = p.chromium.launch_persistent_context(
            CHROME_PROFILE,
            headless=False,
            executable_path=CHROME_EXE,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu',
            ],
            timeout=120000
        )
        
        page = browser.pages[0]
        
        print("📍 Going to LinkedIn...")
        page.goto('https://www.linkedin.com', timeout=60000, wait_until='domcontentloaded')
        page.wait_for_timeout(10000)
        
        print("🖱️  Clicking 'Start a post'...")
        btn = page.query_selector('[data-control-name="topbar_post_update"]')
        if btn:
            btn.click()
            page.wait_for_timeout(5000)
            print("✓ Clicked!")
        else:
            print("⚠️ Waiting for button...")
            page.wait_for_timeout(15000)
        
        print("⌨️  Entering content...")
        editor = page.query_selector('[role="textbox"][contenteditable="true"]')
        if editor:
            editor.fill(post_text)
            page.wait_for_timeout(3000)
            print("✓ Done!")
        else:
            print("⚠️ Waiting for editor...")
            page.wait_for_timeout(15000)
            editor = page.query_selector('[role="textbox"][contenteditable="true"]')
            if editor:
                editor.fill(post_text)
                print("✓ Done!")
        
        print("🖱️  Clicking 'Post'...")
        submit = page.query_selector('button:has-text("Post")')
        if submit:
            submit.click()
            page.wait_for_timeout(10000)
            print()
            print("=" * 70)
            print("✅ POSTED!")
            print("=" * 70)
            
            # Move to Done
            done = vault_path / 'Done'
            done.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            done_path = done / f"{timestamp}_{post_file.name}"
            post_file.rename(done_path)
            print(f"✓ Moved to Done/")
        else:
            print("⚠️ Click Post manually")
            page.wait_for_timeout(30000)
        
        browser.close()
        print()
        print("Done!")


if __name__ == '__main__':
    main()
