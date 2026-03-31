#!/usr/bin/env python3
"""
LinkedIn Quick Post - Simple helper that opens LinkedIn with post content

This is the MOST RELIABLE way to post:
1. Opens LinkedIn in browser
2. Copies post content to clipboard
3. You paste and click Post (takes 10 seconds)
4. AI tracks completion
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import pyperclip  # For clipboard
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False
    print("Note: Install pyperclip for auto-copy: pip install pyperclip")


def main():
    vault_path = Path('AI_Employee_Vault').absolute()
    approved = vault_path / 'Approved'
    
    if not approved.exists():
        print("No Approved folder found.")
        return
    
    approved_posts = list(approved.glob('LINKEDIN_*.md'))
    
    if not approved_posts:
        print("No LinkedIn posts in Approved folder.")
        print()
        print("To create a post:")
        print('  python scripts\\linkedin_post.py create --content "Your post text"')
        return
    
    print("=" * 70)
    print("LinkedIn Quick Post")
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
            
            # Copy to clipboard if available
            if HAS_CLIPBOARD:
                pyperclip.copy(post_text)
                print("✓ Post content copied to clipboard!")
                print()
            
            # Open LinkedIn in default browser
            print("Opening LinkedIn...")
            subprocess.run(['start', 'https://www.linkedin.com'], shell=True)
            
            print()
            print("INSTRUCTIONS:")
            print("1. LinkedIn will open in your browser")
            print("2. Click 'Start a post'")
            if HAS_CLIPBOARD:
                print("3. Paste (Ctrl+V) - content is already copied!")
            else:
                print("3. Copy the content shown above (Ctrl+C)")
                print("4. Paste in LinkedIn (Ctrl+V)")
            print("4. Click 'Post'")
            print()
            
            # Ask for confirmation
            response = input("Did you post successfully? (y/n): ").strip().lower()
            
            if response == 'y':
                # Move to Done
                done = vault_path / 'Done'
                done.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                done_path = done / f"{timestamp}_{post_file.name}"
                
                try:
                    post_file.rename(done_path)
                    print(f"✓ Success! Moved to Done/")
                except Exception as e:
                    print(f"⚠️ Could not move file: {e}")
            else:
                print("Post not completed. File stays in Approved/")
            
            print()
    
    print("=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == '__main__':
    main()
