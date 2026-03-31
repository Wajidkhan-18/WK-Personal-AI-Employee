#!/usr/bin/env python3
"""
LinkedIn Post - Manual Helper (Most Reliable)

Opens LinkedIn in your browser. You click Post (10 seconds).
This is the MOST reliable method.

Usage: python li_quick.py
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import pyperclip
    HAS_CLIPBOARD = True
except:
    HAS_CLIPBOARD = False


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
    print("=" * 70)
    print("LinkedIn Quick Post")
    print("=" * 70)
    print()
    print("Content:")
    print("-" * 70)
    print(post_text)
    print("-" * 70)
    print()
    
    # Copy to clipboard
    if HAS_CLIPBOARD:
        pyperclip.copy(post_text)
        print("✓ Copied to clipboard!")
        print()
    
    # Open LinkedIn
    print("Opening LinkedIn...")
    subprocess.run(['start', 'https://www.linkedin.com'], shell=True)
    
    print()
    print("INSTRUCTIONS:")
    print("1. LinkedIn will open in your browser")
    print("2. Click 'Start a post'")
    if HAS_CLIPBOARD:
        print("3. Paste (Ctrl+V) - content is already copied!")
    else:
        print("3. Copy the content above (Ctrl+C)")
        print("4. Paste in LinkedIn (Ctrl+V)")
    print("4. Click 'Post'")
    print()
    
    response = input("Did you post successfully? (y/n): ").strip().lower()
    
    if response == 'y':
        # Move to Done
        done = vault_path / 'Done'
        done.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        done_path = done / f"{ts}_{post_file.name}"
        
        try:
            post_file.rename(done_path)
            print(f"✓ Moved to Done/")
            print()
            print("✅ DONE! Great job!")
        except Exception as e:
            print(f"⚠️ Could not move file: {e}")
    else:
        print("Post not completed. File stays in Approved/")
    
    print()


if __name__ == '__main__':
    main()
