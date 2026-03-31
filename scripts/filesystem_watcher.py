#!/usr/bin/env python3
"""
Filesystem Watcher - Monitors a drop folder for new files.

This watcher uses the watchdog library to efficiently monitor a folder
for new files. When a file is added, it creates an action file in
Needs_Action and copies the file for processing.

Usage:
    python filesystem_watcher.py /path/to/vault

Or with custom drop folder:
    python filesystem_watcher.py /path/to/vault --drop-folder /path/to/drop
"""

import sys
import shutil
import hashlib
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

# Try to import watchdog, fall back to polling if not available
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # Define stub classes for when watchdog is not available
    class FileSystemEventHandler:
        pass
    class Observer:
        def __init__(self): pass
        def schedule(self, *args, **kwargs): pass
        def start(self): pass
        def stop(self): pass
        def join(self): pass

from base_watcher import BaseWatcher


class FileDropHandler(FileSystemEventHandler):
    """Handle file system events for the drop folder."""
    
    def __init__(self, watcher: 'FilesystemWatcher'):
        self.watcher = watcher
        self.logger = watcher.logger
    
    def on_created(self, event):
        """Called when a file or directory is created."""
        if event.is_directory:
            return
        
        self.logger.info(f"File created: {event.src_path}")
        self.watcher.process_file(Path(event.src_path))


class FilesystemWatcher(BaseWatcher):
    """
    Watcher that monitors a drop folder for new files.
    
    When a file is added to the drop folder (or Inbox), this watcher:
    1. Copies the file to the vault
    2. Creates a metadata action file in Needs_Action
    3. Logs the action
    """
    
    def __init__(self, vault_path: str, check_interval: int = 5, drop_folder: Optional[str] = None):
        """
        Initialize the filesystem watcher.

        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 5 for responsive file detection)
            drop_folder: Optional custom drop folder path (defaults to vault/Drop and vault/Inbox)
        """
        super().__init__(vault_path, check_interval)

        # Set up drop folders - monitor both Drop and Inbox folders
        if drop_folder:
            self.drop_folders = [Path(drop_folder)]
        else:
            self.drop_folders = [
                self.vault_path / 'Drop',   # Primary drop folder
                self.vault_path / 'Inbox'   # Also monitor Inbox for manual files
            ]

        # Ensure folders exist
        for folder in self.drop_folders:
            folder.mkdir(parents=True, exist_ok=True)

        # Track file hashes to detect changes (loaded from state)
        self.file_hashes: Dict[str, str] = {}
        self._load_file_hashes()

        # Keywords to detect in filenames for priority
        self.priority_keywords = ['urgent', 'asap', 'invoice', 'payment', 'contract', 'legal']

        self.logger.info(f"Drop folders: {[str(f) for f in self.drop_folders]}")

    def _load_file_hashes(self):
        """Load file hashes from state file for persistence."""
        import json
        state_file = self.vault_path / '.state_FilesystemWatcher_hashes.json'
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.file_hashes = state.get('file_hashes', {})
                self.logger.info(f"Loaded {len(self.file_hashes)} file hashes from state")
            except Exception as e:
                self.logger.warning(f"Could not load file hashes: {e}")
                self.file_hashes = {}
        else:
            self.file_hashes = {}

    def _save_file_hashes(self):
        """Save file hashes to state file for persistence."""
        import json
        state_file = self.vault_path / '.state_FilesystemWatcher_hashes.json'
        try:
            with open(state_file, 'w') as f:
                json.dump({
                    'file_hashes': self.file_hashes,
                    'last_updated': datetime.now().isoformat()
                }, f)
        except Exception as e:
            self.logger.error(f"Could not save file hashes: {e}")

    def _save_state(self):
        """Override to save file hashes."""
        super()._save_state()
        self._save_file_hashes()
    
    def _calculate_hash(self, filepath: Path) -> str:
        """Calculate MD5 hash of a file for change detection."""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _detect_priority(self, filename: str) -> str:
        """Detect priority level from filename keywords."""
        filename_lower = filename.lower()
        for keyword in self.priority_keywords:
            if keyword in filename_lower:
                return "high"
        return "normal"
    
    def check_for_updates(self) -> List[Path]:
        """
        Check the drop folders for new files.

        In polling mode (no watchdog), this scans the folders for new files.
        In watchdog mode, this is called periodically but files are detected via events.

        Returns:
            List of new file paths
        """
        new_files = []

        try:
            for drop_folder in self.drop_folders:
                if not drop_folder.exists():
                    continue
                    
                for filepath in drop_folder.iterdir():
                    if filepath.is_file() and not filepath.name.startswith('.'):
                        file_hash = self._calculate_hash(filepath)
                        file_key = str(filepath.absolute())

                        # Check if this is a new or modified file
                        if file_key not in self.file_hashes or self.file_hashes[file_key] != file_hash:
                            self.file_hashes[file_key] = file_hash
                            new_files.append(filepath)
        except Exception as e:
            self.logger.error(f"Error scanning drop folders: {e}")

        return new_files
    
    def process_file(self, filepath: Path):
        """
        Process a newly detected file.
        
        Args:
            filepath: Path to the new file
        """
        try:
            # Create action file
            action_file_path = self.create_action_file(filepath)
            if action_file_path:
                self.logger.info(f"Processed file: {filepath.name} -> {action_file_path.name}")
        except Exception as e:
            self.logger.error(f"Error processing file {filepath}: {e}")
    
    def create_action_file(self, filepath: Path) -> Optional[Path]:
        """
        Create an action file for the dropped file.

        If file is in Drop folder: moves to Inbox
        If file is already in Inbox: keeps it there (just creates action file)

        Args:
            filepath: Path to the dropped file

        Returns:
            Path to the created action file
        """
        try:
            # Generate unique ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = self.sanitize_filename(filepath.stem)

            # Check if file is already in Inbox
            inbox_path = self.vault_path / 'Inbox'
            is_already_in_inbox = str(filepath.parent) == str(inbox_path)

            if is_already_in_inbox:
                # File is already in Inbox, just use it as-is
                dest_path = filepath
                self.logger.info(f"File already in Inbox: {dest_path}")
            else:
                # Move file from Drop to Inbox
                inbox_path.mkdir(parents=True, exist_ok=True)
                dest_path = inbox_path / f"{timestamp}_{filepath.name}"
                shutil.move(str(filepath), str(dest_path))
                self.logger.info(f"Moved file to: {dest_path}")

            # Get file info
            file_size = dest_path.stat().st_size
            priority = self._detect_priority(filepath.name)

            # Generate action file content
            frontmatter = self.generate_frontmatter(
                item_type="file_drop",
                original_name=f'"{filepath.name}"',
                file_path=f'"{dest_path}"',
                file_size=file_size,
                priority=f'"{priority}"',
                source=f'"{filepath.parent}"'
            )

            content = f'''{frontmatter}

## File Drop for Processing

**Original File:** `{filepath.name}`
**Size:** {self._format_size(file_size)}
**Detected Priority:** {priority}
**Location:** `{dest_path.name}`

## Suggested Actions

- [ ] Review file contents
- [ ] Categorize and move to appropriate folder
- [ ] Extract any actionable information
- [ ] Move to /Done when complete

## Notes

*Add any notes about this file below*

---
*Detected by FilesystemWatcher at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
'''
            
            # Write action file
            action_filename = f"FILE_{timestamp}_{safe_name}.md"
            action_path = self.needs_action / action_filename
            action_path.write_text(content, encoding='utf-8')
            
            return action_path
            
        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            return None
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def run_with_watchdog(self):
        """Run using watchdog for efficient file system monitoring."""
        if not WATCHDOG_AVAILABLE:
            self.logger.warning("Watchdog not available, falling back to polling")
            return self.run()
        
        self.logger.info(f"Starting {self.__class__.__name__} with watchdog")
        self.logger.info(f"Drop folder: {self.drop_folder}")
        
        event_handler = FileDropHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.drop_folder), recursive=False)
        observer.start()
        
        self.logger.info(f"Watchdog monitoring: {self.drop_folder}")
        
        try:
            while True:
                time.sleep(1)  # Keep alive, watchdog handles events
        except KeyboardInterrupt:
            self.logger.info("Stopped by user")
            observer.stop()
        except Exception as e:
            self.logger.error(f"Error: {e}")
            observer.stop()
        
        observer.join()
        self._save_state()


def main():
    """Main entry point for running the filesystem watcher."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Filesystem Watcher for AI Employee')
    parser.add_argument('vault_path', help='Path to the Obsidian vault')
    parser.add_argument('--drop-folder', '-d', help='Custom drop folder path')
    parser.add_argument('--interval', '-i', type=int, default=5, help='Check interval in seconds')
    parser.add_argument('--watchdog', '-w', action='store_true', help='Use watchdog if available')
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault_path).absolute()

    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    watcher = FilesystemWatcher(
        str(vault_path),
        check_interval=args.interval,
        drop_folder=args.drop_folder
    )

    print(f"📁 Filesystem Watcher starting...")
    print(f"   Vault: {vault_path}")
    print(f"   Drop folders: {', '.join([str(f) for f in watcher.drop_folders])}")
    print(f"   Check interval: {args.interval}s")

    if args.watchdog and WATCHDOG_AVAILABLE:
        print(f"   Mode: Watchdog (event-based)")
        watcher.run_with_watchdog()
    else:
        print(f"   Mode: Polling")
        watcher.run()


if __name__ == "__main__":
    main()
