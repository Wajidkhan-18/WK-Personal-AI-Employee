#!/usr/bin/env python3
"""
Base Watcher - Abstract base class for all AI Employee watchers.

Watchers are lightweight Python scripts that run continuously in the background,
monitoring various inputs (Gmail, WhatsApp, filesystems) and creating actionable
files for Claude Code to process.
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Any, Optional


class BaseWatcher(ABC):
    """
    Abstract base class for all watcher implementations.
    
    All watchers follow the same pattern:
    1. Continuously monitor a data source
    2. Detect new/updated items
    3. Create action files in the Needs_Action folder
    4. Track processed items to avoid duplicates
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.inbox = self.vault_path / 'Inbox'
        self.logs_dir = self.vault_path / 'Logs'
        self.check_interval = check_interval
        
        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self._setup_logging()
        
        # Track processed items to avoid duplicates
        self.processed_ids: set = set()
        
        # State file for persistence across restarts
        self.state_file = self.vault_path / f'.state_{self.__class__.__name__}.json'
        self._load_state()
    
    def _setup_logging(self):
        """Configure logging to file and console."""
        log_file = self.logs_dir / f'{datetime.now().strftime("%Y-%m-%d")}_{self.__class__.__name__}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _load_state(self):
        """Load processed IDs from state file for persistence."""
        import json
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.processed_ids = set(state.get('processed_ids', []))
                self.logger.info(f"Loaded {len(self.processed_ids)} processed IDs from state")
            except Exception as e:
                self.logger.warning(f"Could not load state: {e}")
                self.processed_ids = set()
        else:
            self.processed_ids = set()
    
    def _save_state(self):
        """Save processed IDs to state file."""
        import json
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    'processed_ids': list(self.processed_ids),
                    'last_updated': datetime.now().isoformat()
                }, f)
        except Exception as e:
            self.logger.error(f"Could not save state: {e}")
    
    @abstractmethod
    def check_for_updates(self) -> List[Any]:
        """
        Check the data source for new or updated items.
        
        Returns:
            List of items that need processing
        """
        pass
    
    @abstractmethod
    def create_action_file(self, item: Any) -> Optional[Path]:
        """
        Create an action file in the Needs_Action folder for the given item.
        
        Args:
            item: The item to create an action file for
            
        Returns:
            Path to the created file, or None if creation failed
        """
        pass
    
    def run(self):
        """
        Main run loop. Continuously checks for updates and creates action files.
        
        This method runs indefinitely until interrupted (Ctrl+C).
        """
        self.logger.info(f"Starting {self.__class__.__name__}")
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Check interval: {self.check_interval}s")
        
        try:
            while True:
                try:
                    items = self.check_for_updates()
                    
                    if items:
                        self.logger.info(f"Found {len(items)} new item(s)")
                        
                    for item in items:
                        try:
                            filepath = self.create_action_file(item)
                            if filepath:
                                self.logger.info(f"Created action file: {filepath.name}")
                        except Exception as e:
                            self.logger.error(f"Error creating action file: {e}")
                    
                    # Save state after each check
                    self._save_state()
                    
                except Exception as e:
                    self.logger.error(f"Error in check cycle: {e}")
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info(f"{self.__class__.__name__} stopped by user")
            self._save_state()
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            self._save_state()
            raise
    
    def generate_frontmatter(self, item_type: str, **kwargs) -> str:
        """
        Generate YAML frontmatter for action files.
        
        Args:
            item_type: Type of item (email, whatsapp, file_drop, etc.)
            **kwargs: Additional frontmatter fields
            
        Returns:
            Formatted YAML frontmatter string
        """
        lines = [
            "---",
            f"type: {item_type}",
            f"received: {datetime.now().isoformat()}",
            "status: pending",
            "priority: normal",
        ]
        
        for key, value in kwargs.items():
            lines.append(f"{key}: {value}")
        
        lines.append("---")
        return "\n".join(lines)
    
    def sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string for use as a filename.
        
        Args:
            name: The original name
            
        Returns:
            Sanitized filename-safe string
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|？*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Limit length
        return name[:100] if len(name) > 100 else name


if __name__ == "__main__":
    # This is an abstract class - cannot be run directly
    print("BaseWatcher is an abstract class. Use a concrete implementation like FilesystemWatcher.")
    print("Example: python filesystem_watcher.py")
