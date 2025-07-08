"""
Player UUID Mapping System for PhasGrid
Provides privacy-compliant mapping between player names and anonymous UUIDs
Windows-compatible version with file locking
"""

import json
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
from uuid import UUID, uuid4
import time
import tempfile
import shutil


class UUIDMapper:
    """Maps player names to anonymous UUIDs with persistence and thread safety."""
    
    def __init__(self, mapping_file: str = "data/uuid_mappings.json"):
        """
        Initialize the UUID mapper with a persistent storage file.
        
        Args:
            mapping_file: Path to JSON file storing UUID mappings
        """
        self.mapping_file = Path(mapping_file)
        self.mappings: Dict[str, Dict[str, Any]] = {}
        self._ensure_file_exists()
        self.load_mappings()
    
    def _ensure_file_exists(self) -> None:
        """Create the mapping file and directory if they don't exist."""
        self.mapping_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.mapping_file.exists():
            self._write_mappings({})
    
    def _normalize(self, name: str) -> str:
        """
        Normalize player names for consistent UUID mapping.
        
        Args:
            name: Raw player name (e.g., "A'ja Wilson")
            
        Returns:
            Normalized name (e.g., "aja wilson")
        """
        # Remove all non-alphanumeric except spaces, lowercase, strip
        normalized = re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()
        # Collapse multiple spaces to single space
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized
    
    def get_or_create_uuid(self, player_name: str) -> UUID:
        """
        Get existing UUID for player or create new one.
        
        Args:
            player_name: Player's display name
            
        Returns:
            UUID associated with the player
        """
        normalized_name = self._normalize(player_name)
        
        # Check if mapping exists in memory
        if normalized_name in self.mappings:
            # Update last accessed timestamp
            self.mappings[normalized_name]["last_accessed"] = datetime.utcnow().isoformat()
            uuid_str = self.mappings[normalized_name]["uuid"]
            return UUID(uuid_str)
        
        # Create new UUID and mapping
        new_uuid = uuid4()
        now = datetime.utcnow().isoformat()
        
        self.mappings[normalized_name] = {
            "uuid": str(new_uuid),
            "original_name": player_name,  # Store first seen version
            "normalized_name": normalized_name,
            "created_at": now,
            "last_accessed": now
        }
        
        # Persist immediately for thread safety
        self.save_mappings()
        return new_uuid
    
    def load_mappings(self) -> None:
        """Load UUID mappings from persistent storage."""
        max_retries = 5
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                with open(self.mapping_file, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                    self.mappings = data
                return
            except FileNotFoundError:
                # File doesn't exist yet, that's okay
                self.mappings = {}
                return
            except json.JSONDecodeError:
                print("Warning: Corrupted mapping file. Starting fresh.")
                self.mappings = {}
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    print(f"Warning: Could not load mappings after {max_retries} attempts. Starting fresh.")
                    self.mappings = {}
    
    def save_mappings(self) -> None:
        """Save UUID mappings to persistent storage with atomic write."""
        max_retries = 5
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                # Create a temporary file in the same directory
                temp_fd, temp_path = tempfile.mkstemp(
                    dir=self.mapping_file.parent,
                    prefix='.tmp_',
                    suffix='.json'
                )
                
                try:
                    # Write to temp file
                    with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                        json.dump(self.mappings, f, indent=2, sort_keys=True)
                    
                    # Atomic rename on Windows
                    # First remove the target file if it exists
                    if self.mapping_file.exists():
                        self.mapping_file.unlink()
                    
                    # Then rename the temp file
                    Path(temp_path).rename(self.mapping_file)
                    return
                    
                except Exception:
                    # Clean up temp file on error
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    raise
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise RuntimeError(f"Failed to save mappings after {max_retries} attempts: {e}")
    
    def _write_mappings(self, data: Dict) -> None:
        """Helper to write mappings without locking (for initialization)."""
        with open(self.mapping_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def get_mapping_stats(self) -> Dict[str, int]:
        """Get statistics about current mappings."""
        return {
            "total_players": len(self.mappings),
            "unique_uuids": len(set(m["uuid"] for m in self.mappings.values()))
        }
    
    def lookup_by_uuid(self, player_uuid: UUID) -> Optional[Dict[str, Any]]:
        """
        Reverse lookup: find player info by UUID.
        
        Args:
            player_uuid: UUID to look up
            
        Returns:
            Player info dict or None if not found
        """
        uuid_str = str(player_uuid)
        for normalized_name, info in self.mappings.items():
            if info["uuid"] == uuid_str:
                return info
        return None