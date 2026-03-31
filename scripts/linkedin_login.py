#!/usr/bin/env python3
"""
LinkedIn Authentication Helper

Use this script for first-time LinkedIn login.
It will open the browser and wait for you to log in.

Usage:
    python scripts\linkedin_login.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright

# Session path
SESSION_PATH = Path.home() / '.linkedin_session'
SESSION_PATH.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("LinkedIn Authentication Helper")
print("=" * 60)
print()
print("A browser window will open in 3 seconds...")
print()
print("INSTRUCTIONS:")
print("1. LinkedIn login page will appear")
print("2. Enter your email/phone and password")
print("3. Complete 2FA if enabled")
print("4. Complete any security check/CAPTCHA")
print("5. Wait for your feed to load completely")
print("6. Browser will auto-close after you reach feed")
print()
print("Your session will be saved to:")
print(f"  {SESSION_PATH}")
print()
print("Next time, run the watcher without --no-headless")
print("=" * 60)
print()

import time
time.sleep(3)

with sync_playwright() as p:
    print("Launching browser...")
    
    # Launch browser with persistent context
    browser = p.chromium.launch_persistent_context(
        SESSION_PATH,
        headless=False,  # Always show browser for login
        args=['--disable-blink-features=AutomationControlled'],
        timeout=600000  # 10 minutes for login + security checks
    )
    
    page = browser.pages[0] if browser.pages else browser.new_page()
    
    print("Navigating to LinkedIn...")
    page.goto('https://www.linkedin.com', wait_until='domcontentloaded', timeout=120000)
    
    print()
    print("✓ Page loaded!")
    print()
    print("Please log in to LinkedIn now...")
    print("Complete any security checks/CAPTCHA if shown.")
    print()
    
    # Wait for user to log in - check every 5 seconds if feed is loaded
    max_wait = 600  # 10 minutes max
    check_interval = 5
    logged_in = False
    
    for i in range(0, max_wait, check_interval):
        # Check if we're on the feed page (logged in)
        try:
            # Look for feed content or navigation bar that appears when logged in
            feed_indicator = page.query_selector('.scaffold-layout__main, .global-nav, [data-control-name="topbar_post_update"]')
            
            # Also check if we're NOT on login page
            current_url = page.url
            is_on_login_page = 'login' in current_url or 'checkpoint' in current_url
            
            if feed_indicator and not is_on_login_page:
                print()
                print("✓ Login detected! Feed page loaded.")
                logged_in = True
                # Wait a bit more to ensure session is fully established
                print("  Waiting 10 more seconds to save session...")
                time.sleep(10)
                break
            
            # Print status every 30 seconds
            if i > 0 and i % 30 == 0:
                print(f"  Still waiting... {i}/{max_wait} seconds")
                print(f"  Current URL: {current_url[:80]}...")
                
        except Exception as e:
            # Page might be reloading, continue waiting
            pass
        
        time.sleep(check_interval)
    
    if logged_in:
        print()
        print("=" * 60)
        print("SUCCESS! Your session has been saved.")
        print("=" * 60)
        print()
        print("You can now run the LinkedIn watcher:")
        print("  cd C:\\Users\\adnanlaptop\\OneDrive\\Documents\\GitHub\\WK-Personal-AI-Employee")
        print("  python scripts\\linkedin_watcher.py AI_Employee_Vault")
        print()
    else:
        print()
        print("=" * 60)
        print("TIMEOUT: Login not completed within 10 minutes.")
        print("=" * 60)
        print()
        print("If you're still on login/security check page:")
        print("  1. Complete the security check")
        print("  2. Run this script again: python scripts\\linkedin_login.py")
        print()
    
    browser.close()
    print("Browser closed.")
