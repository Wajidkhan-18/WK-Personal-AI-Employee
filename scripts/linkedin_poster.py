#!/usr/bin/env python3
"""
LinkedIn Auto-Poster - Creates and posts business updates to LinkedIn.

This script:
1. Creates post drafts based on business achievements
2. Manages approval workflow
3. Posts to LinkedIn via Playwright automation
4. Tracks engagement metrics

WARNING: LinkedIn's ToS prohibits automated posting. Use responsibly
for business accounts only. Consider LinkedIn Marketing API for production.

Usage:
    python linkedin_poster.py create --content "Post content"
    python linkedin_poster.py post --vault /path/to/vault
    python linkedin_poster.py status
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Try to import Playwright
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from base_watcher import BaseWatcher


class LinkedInPoster(BaseWatcher):
    """LinkedIn auto-posting with approval workflow."""

    # Default hashtags for business posts
    DEFAULT_HASHTAGS = ['#Business', '#AI', '#Automation', '#Innovation', '#Growth']

    # Best posting times (hour, day_of_week)
    OPTIMAL_TIMES = [
        (9, 1),   # Tuesday 9 AM
        (10, 1),  # Tuesday 10 AM
        (9, 2),   # Wednesday 9 AM
        (10, 2),  # Wednesday 10 AM
        (9, 3),   # Thursday 9 AM
        (10, 3),  # Thursday 10 AM
    ]

    def __init__(self, vault_path: str, session_path: Optional[str] = None,
                 headless: bool = True):
        """
        Initialize LinkedIn poster.

        Args:
            vault_path: Path to the Obsidian vault
            session_path: Path to store browser session
            headless: Run browser without UI
        """
        super().__init__(vault_path, check_interval=0)

        self.session_path = Path(session_path) if session_path else Path.home() / '.linkedin_session'
        self.session_path.mkdir(parents=True, exist_ok=True)
        self.headless = headless
        self.hashtags = self.DEFAULT_HASHTAGS.copy()

        self.logger.info(f"Session path: {self.session_path}")
        self.logger.info(f"Default hashtags: {', '.join(self.hashtags)}")

    def create_post_draft(self, content: str, hashtags: Optional[List[str]] = None,
                          scheduled_for: Optional[str] = None) -> Path:
        """
        Create a post draft file.

        Args:
            content: Post content
            hashtags: List of hashtags
            scheduled_for: ISO datetime for scheduled posting

        Returns:
            Path to created draft file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hashtags = hashtags or self.hashtags

        # Calculate character count
        char_count = len(content) + sum(len(h) + 1 for h in hashtags)

        # Generate draft content
        draft_content = f'''---
type: linkedin_post
created: {datetime.now().isoformat()}
status: draft
priority: normal
scheduled_for: {scheduled_for if scheduled_for else "null"}
hashtags: {json.dumps(hashtags)}
character_count: {char_count}
---

## Post Content

{content}

{' '.join(hashtags)}

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
        draft_filename = f"LINKEDIN_{timestamp}_draft.md"
        draft_path = self.needs_action / draft_filename
        draft_path.write_text(draft_content, encoding='utf-8')

        self.logger.info(f"Created draft: {draft_path}")
        return draft_path

    def post_to_linkedin(self, content: str) -> bool:
        """
        Post content to LinkedIn via browser automation.

        Args:
            content: Post content to publish

        Returns:
            True if post successful
        """
        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=self.headless,
                    args=['--disable-blink-features=AutomationControlled']
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Navigate to LinkedIn
                page.goto('https://www.linkedin.com', wait_until='networkidle')

                # Wait for feed to load
                page.wait_for_selector('[data-control-name="topbar_post_update"]', timeout=30000)

                # Click "Start a post" button
                page.click('[data-control-name="topbar_post_update"]')

                # Wait for post dialog
                page.wait_for_selector('[role="dialog"]', timeout=10000)

                # Find the editor and type content
                editor = page.query_selector('[role="textbox"]')
                if editor:
                    editor.fill(content)

                    # Wait a moment for text to register
                    page.wait_for_timeout(1000)

                    # Click Post button
                    post_button = page.query_selector('button:has-text("Post")')
                    if post_button:
                        post_button.click()

                        # Wait for confirmation
                        page.wait_for_timeout(3000)

                        self.logger.info("Post published successfully")
                        browser.close()
                        return True
                    else:
                        self.logger.error("Post button not found")
                else:
                    self.logger.error("Editor not found")

                browser.close()
                return False

        except Exception as e:
            self.logger.error(f"Error posting to LinkedIn: {e}")
            return False

    def process_approved_posts(self) -> List[Path]:
        """
        Process approved posts from Approved/ folder.

        Returns:
            List of successfully processed post files
        """
        processed = []

        approved_folder = self.vault_path / 'Approved'
        if not approved_folder.exists():
            return processed

        for post_file in approved_folder.glob('LINKEDIN_*.md'):
            content = post_file.read_text(encoding='utf-8')

            # Extract post content from markdown
            if '## Post Content' in content:
                start = content.find('## Post Content') + len('## Post Content')
                end = content.find('---', start)
                post_content = content[start:end].strip()

                # Post to LinkedIn
                success = self.post_to_linkedin(post_content)

                if success:
                    processed.append(post_file)
                    self.logger.info(f"Posted: {post_file.name}")
                else:
                    self.logger.error(f"Failed to post: {post_file.name}")

        return processed


def create_post_from_achievements(vault_path: Path) -> Optional[Path]:
    """
    Create a post draft based on weekly achievements.

    Args:
        vault_path: Path to the Obsidian vault

    Returns:
        Path to created draft file
    """
    done_folder = vault_path / 'Done'

    if not done_folder.exists():
        return None

    # Count completed tasks this week
    week_ago = datetime.now() - timedelta(days=7)
    tasks_completed = []

    for file in done_folder.glob('*.md'):
        mtime = datetime.fromtimestamp(file.stat().st_mtime)
        if mtime >= week_ago:
            tasks_completed.append(file.stem)

    if not tasks_completed:
        return None

    # Generate achievement post
    content = f"""🎉 Great week completed!

This week I'm proud to have finished {len(tasks_completed)} tasks, including:
"""

    # Add first 3 tasks
    for task in tasks_completed[:3]:
        content += f"\n• {task.replace('_', ' ').title()}"

    content += """

Grateful for the opportunity to work on meaningful projects!

#Business #Growth #Productivity"""

    # Create draft
    poster = LinkedInPoster(str(vault_path))
    return poster.create_post_draft(content)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='LinkedIn Auto-Poster')
    parser.add_argument('command', choices=['create', 'post', 'status', 'generate'],
                        help='Command to execute')
    parser.add_argument('--vault', '-v', default='AI_Employee_Vault',
                        help='Path to Obsidian vault')
    parser.add_argument('--content', '-c', type=str, help='Post content')
    parser.add_argument('--hashtags', '-t', type=str, help='Comma-separated hashtags')
    parser.add_argument('--schedule', '-s', type=str, help='Schedule for (ISO datetime)')
    parser.add_argument('--no-headless', '-n', action='store_true',
                        help='Run browser with UI')

    args = parser.parse_args()

    if not PLAYWRIGHT_AVAILABLE:
        print("Playwright not installed")
        print("Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    vault_path = Path(args.vault_path).absolute() if hasattr(args, 'vault_path') else Path(args.vault).absolute()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    if args.command == 'create':
        if not args.content:
            print("Error: --content required for create command")
            sys.exit(1)

        hashtags = args.hashtags.split(',') if args.hashtags else None
        poster = LinkedInPoster(str(vault_path))
        draft_path = poster.create_post_draft(args.content, hashtags, args.schedule)
        print(f"✓ Draft created: {draft_path}")

    elif args.command == 'post':
        poster = LinkedInPoster(str(vault_path), headless=not args.no_headless)
        processed = poster.process_approved_posts()
        print(f"✓ Posted {len(processed)} update(s)")

    elif args.command == 'generate':
        draft_path = create_post_from_achievements(vault_path)
        if draft_path:
            print(f"✓ Generated achievement post: {draft_path}")
        else:
            print("No achievements found this week")

    elif args.command == 'status':
        approved = len(list((vault_path / 'Approved').glob('LINKEDIN_*.md')) if (vault_path / 'Approved').exists() else [])
        drafts = len(list((vault_path / 'Needs_Action').glob('LINKEDIN_*.md')) if (vault_path / 'Needs_Action').exists() else [])
        print(f"Pending drafts: {drafts}")
        print(f"Approved (ready to post): {approved}")


if __name__ == '__main__':
    main()
