#!/usr/bin/env python3
"""
LinkedIn Poster V3 - Improved Version with Multiple Selectors

Usage:
    python linkedin_poster_v3.py --post "Your post" --hashtags "AI automation" --wait 5

Features:
- Uses your Chrome Profile 2 (where you're logged in)
- Tries 5 different selectors to detect login
- Tries 4 different selectors for post button
- Tries 3 different selectors for editor
- Waits longer for page to load
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install: pip install playwright && playwright install chromium")
    sys.exit(1)


# Your Chrome Profile 2
PROFILE = r"C:\Users\adnanlaptop\AppData\Local\Google\Chrome\User Data\Profile 2"
CHROME = r"C:\Users\adnanlaptop\AppData\Local\Google\Chrome\Application\chrome.exe"


def check_logged_in(page):
    """Check if logged in using multiple selectors."""
    
    # Selector 1: Profile menu
    if page.query_selector('.global-nav__me'):
        return True
    
    # Selector 2: Feed URL
    if 'feed' in page.url or 'mynetwork' in page.url:
        return True
    
    # Selector 3: Post button (only visible when logged in)
    if page.query_selector('[data-control-name="topbar_post_update"]'):
        return True
    
    # Selector 4: Nav menu
    if page.query_selector('nav.global-nav'):
        return True
    
    # Selector 5: Welcome message
    if page.query_selector('.feed-shared-update-v2'):
        return True
    
    return False


def click_post_button(page):
    """Click 'Start a post' using multiple selectors."""
    
    selectors = [
        '[data-control-name="topbar_post_update"]',
        '.share-box-feed-entry__trigger',
        'button:has-text("Start a post")',
        'button:has-text("Start")',
        '.ippon-cta-icon'
    ]
    
    for sel in selectors:
        try:
            btn = page.query_selector(sel)
            if btn:
                btn.click()
                return True
        except:
            pass
    
    return False


def find_editor(page):
    """Find post editor using multiple selectors."""
    
    selectors = [
        '[role="textbox"][contenteditable="true"]',
        '.editor-content[contenteditable="true"]',
        '[data-placeholder*="post"]',
        'div[contenteditable="true"]'
    ]
    
    for sel in selectors:
        try:
            editor = page.query_selector(sel)
            if editor:
                return editor
        except:
            pass
    
    return None


def find_post_submit(page):
    """Find Post button using multiple selectors."""
    
    selectors = [
        'button:has-text("Post")',
        'button:has-text("Share")',
        '.artdeco-button:has-text("Post")',
        '[aria-label="Post"]'
    ]
    
    for sel in selectors:
        try:
            btn = page.query_selector(sel)
            if btn:
                return btn
        except:
            pass
    
    return None


def post_to_linkedin(content: str, hashtags: list, wait_time: int):
    """Post to LinkedIn."""
    
    full_text = content + "\n\n" + " ".join([f"#{tag}" for tag in hashtags])
    
    print()
    print("=" * 70)
    print("LinkedIn Poster V3 - Improved")
    print("=" * 70)
    print()
    print(f"Post: {content[:60]}...")
    print(f"Hashtags: {' '.join(hashtags)}")
    print()
    print("=" * 70)
    print()
    
    with sync_playwright() as p:
        # Launch with YOUR profile
        print("🚀 Opening Chrome Profile 2 (your logged-in session)...")
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
        
        # Wait for page to fully load
        print(f"⏳ Waiting {wait_time} seconds for page and session to load...")
        page.wait_for_timeout(wait_time * 1000)
        
        # Additional wait for cookies/session
        print("⏳ Additional session wait (20 seconds)...")
        for i in range(20):
            page.wait_for_timeout(1000)
            if i % 5 == 0:
                print(f"  {i*5}s...")
        
        # Check login with multiple selectors
        print("🔍 Checking if logged in (5 methods)...")
        
        logged_in = check_logged_in(page)
        
        if not logged_in:
            print()
            print("⚠️  NOT DETECTED AS LOGGED IN")
            print()
            print("👉 PLEASE LOGIN IN THE BROWSER NOW")
            print("⏳ Waiting 120 seconds...")
            print()
            
            for i in range(24):
                page.wait_for_timeout(5000)
                
                if check_logged_in(page):
                    print("✓ Login detected!")
                    logged_in = True
                    break
                
                if (i + 1) % 4 == 0:
                    print(f"  Waiting... ({(i+1)*5}s)")
            
            if not logged_in:
                print()
                print("⏱️  Timeout - please login and run again")
                browser.close()
                return False
        
        # POST
        print()
        print("=" * 70)
        print("✅ Logged in - Auto-posting...")
        print("=" * 70)
        print()
        
        # Click "Start a post"
        print("🖱️  1/3 Clicking 'Start a post' (5 selectors)...")
        if click_post_button(page):
            print("✓ Clicked!")
            page.wait_for_timeout(5000)
        else:
            print("⚠️  Waiting for button...")
            page.wait_for_timeout(15000)
            if click_post_button(page):
                print("✓ Clicked!")
        
        # Enter content
        print()
        print("🖱️  2/3 Entering content...")
        editor = find_editor(page)
        
        if editor:
            try:
                editor.fill('')
                page.wait_for_timeout(1000)
                editor.fill(full_text)
                page.wait_for_timeout(3000)
                print("✓ Content entered!")
            except Exception as e:
                print(f"⚠️  Auto-fill failed: {e}")
                print("  Please paste content manually")
                page.wait_for_timeout(30000)
        else:
            print("⚠️  Editor not found, waiting...")
            page.wait_for_timeout(15000)
            editor = find_editor(page)
            if editor:
                editor.fill(full_text)
                print("✓ Content entered!")
        
        # Click Post
        print()
        print("🖱️  3/3 Clicking 'Post'...")
        submit = find_post_submit(page)
        
        if submit:
            try:
                submit.click()
                page.wait_for_timeout(10000)
                print()
                print("=" * 70)
                print("🎉 POST SUBMITTED!")
                print("=" * 70)
                browser.close()
                return True
            except Exception as e:
                print(f"⚠️  Click failed: {e}")
                print("  Please click Post manually")
                page.wait_for_timeout(30000)
        else:
            print("⚠️  Post button not found")
            print("  Please click Post manually")
            page.wait_for_timeout(30000)
        
        browser.close()
        print()
        print("Done!")
        return True


def main():
    parser = argparse.ArgumentParser(description='LinkedIn Poster V3')
    parser.add_argument('--post', '-p', type=str, required=True, help='Post content')
    parser.add_argument('--hashtags', '-t', type=str, default='AI automation', help='Hashtags')
    parser.add_argument('--wait', '-w', type=int, default=5, help='Wait time (seconds)')
    
    args = parser.parse_args()
    hashtags = args.hashtags.split()
    
    success = post_to_linkedin(args.post, hashtags, args.wait)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
