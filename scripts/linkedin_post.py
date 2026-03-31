#!/usr/bin/env python3
"""
LinkedIn Post Creator - Create and post to LinkedIn

Usage:
    # Create a post draft
    python scripts\linkedin_post.py create --content "Your post content here"
    
    # Post after approval
    python scripts\linkedin_post.py post
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Try to import Playwright
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def create_post_draft(vault_path: str, content: str, hashtags: list = None):
    """Create a post draft file for approval."""
    
    vault = Path(vault_path)
    needs_action = vault / 'Needs_Action'
    needs_action.mkdir(parents=True, exist_ok=True)
    
    hashtags = hashtags or ['#AI', '#Automation', '#Business', '#Innovation']
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Calculate character count
    full_content = content + "\n\n" + " ".join(hashtags)
    char_count = len(full_content)
    
    draft_content = f'''---
type: linkedin_post
created: {datetime.now().isoformat()}
status: draft
priority: normal
scheduled_for: null
hashtags: {json.dumps(hashtags)}
character_count: {char_count}
---

## Post Content

{content}

{" ".join(hashtags)}

---

## Posting Details

- **Platform:** LinkedIn
- **Post Type:** Text + Hashtags
- **Character Count:** {char_count}/3000
- **Best Time to Post:** Tuesday-Thursday, 9-11 AM

## Approval Required

⚠️ This post requires human approval before publishing.

**To Approve:** Move this file to `/Approved` folder
**To Reject:** Move this file to `/Rejected` folder
**To Edit:** Edit content above and save

---

*Created by AI Employee at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
'''
    
    # Write draft file
    draft_filename = f"LINKEDIN_{timestamp}_post.md"
    draft_path = needs_action / draft_filename
    draft_path.write_text(draft_content, encoding='utf-8')
    
    print("=" * 60)
    print("✅ LinkedIn Post Draft Created!")
    print("=" * 60)
    print()
    print(f"File: {draft_path}")
    print(f"Character count: {char_count}/3000")
    print()
    print("Next Steps:")
    print("1. Review the post content")
    print("2. Move to Approved/ to publish")
    print("3. Run: python scripts\\linkedin_post.py post")
    print()
    
    return draft_path


def post_to_linkedin(vault_path: str):
    """Post approved LinkedIn posts."""
    
    vault = Path(vault_path)
    approved = vault / 'Approved'
    
    if not approved.exists():
        print("No approved posts found.")
        return
    
    # Find approved LinkedIn posts
    approved_posts = list(approved.glob('LINKEDIN_*.md'))
    
    if not approved_posts:
        print("No LinkedIn posts in Approved folder.")
        return
    
    print(f"Found {len(approved_posts)} approved post(s)")
    
    for post_file in approved_posts:
        content = post_file.read_text(encoding='utf-8')
        
        # Extract post content
        if '## Post Content' in content:
            start = content.find('## Post Content') + len('## Post Content')
            end = content.find('---', start)
            post_text = content[start:end].strip()
            
            print(f"\nPosting: {post_text[:100]}...")
            
            # Post to LinkedIn
            success = _post_to_linkedin_impl(post_text)
            
            if success:
                # Move to Done
                done = vault / 'Done'
                done.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                done_path = done / f"{timestamp}_{post_file.name}"
                post_file.rename(done_path)
                print(f"✓ Posted successfully! Moved to Done/")
            else:
                print("✗ Failed to post")


def _post_to_linkedin_impl(content: str) -> bool:
    """Actually post to LinkedIn using Playwright."""
    
    if not PLAYWRIGHT_AVAILABLE:
        print("Playwright not available. Install with: pip install playwright")
        return False
    
    session_path = Path.home() / '.linkedin_session'
    
    try:
        with sync_playwright() as p:
            # Launch browser with saved session
            print(f"Session path: {session_path}")
            print(f"Session exists: {session_path.exists()}")
            
            browser = p.chromium.launch_persistent_context(
                session_path,
                headless=False,  # Show browser so user can see what's happening
                args=['--disable-blink-features=AutomationControlled'],
                timeout=120000  # 2 minutes to load
            )
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            
            print("Navigating to LinkedIn...")
            page.goto('https://www.linkedin.com', wait_until='networkidle', timeout=60000)
            
            # Wait for page to load
            page.wait_for_selector('.global-nav', timeout=30000)
            page.wait_for_timeout(3000)
            
            # Click "Start a post" button
            print("Clicking 'Start a post'...")
            try:
                # Try different selectors for the post button
                post_button = None
                selectors = [
                    '[data-control-name="topbar_post_update"]',
                    'button:has-text("Start a post")',
                    '.share-box-feed-entry__trigger'
                ]
                
                for selector in selectors:
                    try:
                        post_button = page.query_selector(selector)
                        if post_button:
                            break
                    except:
                        continue
                
                if post_button:
                    post_button.click()
                    page.wait_for_timeout(2000)
                else:
                    print("Could not find 'Start a post' button")
                    browser.close()
                    return False
                    
            except Exception as e:
                print(f"Error clicking post button: {e}")
                browser.close()
                return False
            
            # Find the editor and type content
            print("Entering post content...")
            try:
                # LinkedIn uses a contenteditable div for the post editor
                editor = page.query_selector('[role="textbox"][contenteditable="true"]')
                
                if editor:
                    # Clear any existing content
                    editor.fill('')
                    page.wait_for_timeout(500)
                    
                    # Type the content
                    editor.fill(content)
                    page.wait_for_timeout(2000)
                    
                    # Click Post button
                    print("Clicking 'Post'...")
                    post_submit = page.query_selector('button:has-text("Post")')
                    if post_submit:
                        post_submit.click()
                        page.wait_for_timeout(3000)
                        
                        print("✓ Post submitted!")
                        browser.close()
                        return True
                    else:
                        print("Could not find Post button")
                        browser.close()
                        return False
                else:
                    print("Could not find post editor")
                    browser.close()
                    return False
                    
            except Exception as e:
                print(f"Error entering content: {e}")
                browser.close()
                return False
            
    except Exception as e:
        print(f"Error posting to LinkedIn: {e}")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Post Creator')
    parser.add_argument('command', choices=['create', 'post'],
                        help='Command to execute')
    parser.add_argument('--vault', '-v', default='AI_Employee_Vault',
                        help='Path to Obsidian vault')
    parser.add_argument('--content', '-c', type=str, 
                        help='Post content (for create command)')
    parser.add_argument('--hashtags', '-t', type=str, 
                        help='Comma-separated hashtags')
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault).absolute()
    
    if args.command == 'create':
        if not args.content:
            print("Error: --content required for create command")
            sys.exit(1)
        
        hashtags = args.hashtags.split(',') if args.hashtags else None
        create_post_draft(str(vault_path), args.content, hashtags)
        
    elif args.command == 'post':
        post_to_linkedin(str(vault_path))


if __name__ == '__main__':
    main()
