#!/usr/bin/env python3
"""
LinkedIn Post Helper - Manual posting assistance

Opens LinkedIn with the post content ready for you to paste and submit.
"""

import sys
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Run: pip install playwright")
    sys.exit(1)


def main():
    vault_path = Path('AI_Employee_Vault').absolute()
    approved = vault_path / 'Approved'
    
    # Find approved LinkedIn posts
    if not approved.exists():
        print("No Approved folder found.")
        sys.exit(1)
    
    approved_posts = list(approved.glob('LINKEDIN_*.md'))
    
    if not approved_posts:
        print("No LinkedIn posts in Approved folder.")
        sys.exit(1)
    
    print("=" * 70)
    print("LinkedIn Post Helper")
    print("=" * 70)
    print()
    
    for post_file in approved_posts:
        content = post_file.read_text(encoding='utf-8')
        
        # Extract post content
        if '## Post Content' in content:
            start = content.find('## Post Content') + len('## Post Content')
            end = content.find('---', start)
            post_text = content[start:end].strip()
            
            print(f"Post to publish:")
            print("-" * 70)
            print(post_text)
            print("-" * 70)
            print()
            
            # Ask user to confirm
            response = input("Open LinkedIn for posting? (y/n): ").strip().lower()
            if response != 'y':
                print("Skipped.")
                continue
            
            # Open LinkedIn
            session_path = Path.home() / '.linkedin_session'
            
            print("\nOpening LinkedIn...")
            print("The browser will open in 3 seconds...")
            print()
            print("INSTRUCTIONS:")
            print("1. Click 'Start a post' on LinkedIn")
            print("2. Copy the post content shown above")
            print("3. Paste into LinkedIn")
            print("4. Click 'Post'")
            print("5. Come back here and press Enter when done")
            print()
            
            import time
            time.sleep(3)
            
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    session_path,
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled'],
                    timeout=120000
                )
                
                page = browser.pages[0] if browser.pages else browser.new_page()
                
                print("Navigating to LinkedIn...")
                page.goto('https://www.linkedin.com', wait_until='domcontentloaded', timeout=60000)
                
                print("\n✓ LinkedIn loaded!")
                print()
                print("Post this content:")
                print("-" * 70)
                print(post_text)
                print("-" * 70)
                print()
                print("After posting, press Enter here to continue...")
                
                # Wait for user to complete
                input()
                
                # Ask if successful
                success = input("Did you successfully post? (y/n): ").strip().lower()
                
                if success == 'y':
                    # Move to Done
                    done = vault_path / 'Done'
                    done.mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    done_path = done / f"{timestamp}_{post_file.name}"
                    post_file.rename(done_path)
                    
                    print(f"✓ Moved to Done/: {done_path.name}")
                else:
                    print("Post not completed. File remains in Approved/")
                
                browser.close()
    
    print()
    print("=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == '__main__':
    main()
