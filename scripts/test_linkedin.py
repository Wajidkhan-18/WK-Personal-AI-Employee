#!/usr/bin/env python3
"""
Test LinkedIn Session - Opens browser so you can see if you're logged in
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

session_path = Path.home() / '.linkedin_session'

print("Session path:", session_path)
print("Session exists:", session_path.exists())
print()
print("Opening LinkedIn in browser...")
print("If you see your feed, you're logged in!")
print()

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        session_path,
        headless=False,
        args=['--disable-blink-features=AutomationControlled'],
        timeout=120000
    )
    
    page = browser.pages[0] if browser.pages else browser.new_page()
    
    print("Navigating to LinkedIn...")
    page.goto('https://www.linkedin.com', wait_until='domcontentloaded', timeout=120000)
    
    print()
    print("Waiting 30 seconds...")
    print("Check the browser - are you logged in?")
    print()
    
    # Wait and check
    import time
    time.sleep(30)
    
    # Check if logged in
    try:
        profile = page.query_selector('.global-nav__me')
        if profile:
            print("✓ You ARE logged in!")
        else:
            print("✗ You are NOT logged in")
    except:
        print("✗ Could not detect login status")
    
    print()
    print("Press Enter to close browser...")
    input()
    
    browser.close()
    print("Browser closed.")
