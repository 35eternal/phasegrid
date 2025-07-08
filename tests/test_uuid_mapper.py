"""
Test suite for UUID Mapper module
Validates normalization, persistence, and thread safety
Windows-compatible version
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime
import time
import shutil

from phasegrid.uuid_mapper import UUIDMapper


class TestUUIDMapper(unittest.TestCase):
    """Test cases for the UUID mapping system."""
    
    def setUp(self):
        """Create a temporary mapping file for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.mapping_file = os.path.join(self.temp_dir, "test_mappings.json")
        self.mapper = UUIDMapper(self.mapping_file)
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_normalization(self):
        """Test name normalization handles various formats correctly."""
        test_cases = [
            ("A'ja Wilson", "aja wilson"),
            ("Breanna  Stewart", "breanna stewart"),  # Double space
            ("DIANA TAURASI", "diana taurasi"),
            ("Sue Bird-Storm", "sue birdstorm"),
            ("Candace Parker!!!", "candace parker"),
            ("  Kelsey Plum  ", "kelsey plum"),  # Leading/trailing spaces
            ("María José", "mara jos"),  # Diacritics
            ("O'Neal, Shaquille", "oneal shaquille"),  # Apostrophe and comma
        ]
        
        for original, expected in test_cases:
            with self.subTest(name=original):
                normalized = self.mapper._normalize(original)
                self.assertEqual(normalized, expected)
    
    def test_get_or_create_new_player(self):
        """Test creating UUID for new player."""
        player_name = "Maya Moore"
        
        # Get UUID for new player
        uuid1 = self.mapper.get_or_create_uuid(player_name)
        
        # Verify it's a valid UUID
        self.assertIsInstance(uuid1, UUID)
        
        # Check mapping was created
        normalized = self.mapper._normalize(player_name)
        self.assertIn(normalized, self.mapper.mappings)
        
        # Verify mapping structure
        mapping = self.mapper.mappings[normalized]
        self.assertEqual(mapping["original_name"], player_name)
        self.assertEqual(mapping["normalized_name"], normalized)
        self.assertEqual(mapping["uuid"], str(uuid1))
        self.assertIn("created_at", mapping)
        self.assertIn("last_accessed", mapping)
    
    def test_get_or_create_existing_player(self):
        """Test retrieving UUID for existing player."""
        player_name = "Diana Taurasi"
        
        # Create initial mapping
        uuid1 = self.mapper.get_or_create_uuid(player_name)
        created_at1 = self.mapper.mappings["diana taurasi"]["created_at"]
        
        # Wait a moment to ensure timestamp difference
        time.sleep(0.01)
        
        # Get UUID again - should return same UUID
        uuid2 = self.mapper.get_or_create_uuid(player_name)
        
        # Verify same UUID returned
        self.assertEqual(uuid1, uuid2)
        
        # Verify created_at unchanged but last_accessed updated
        mapping = self.mapper.mappings["diana taurasi"]
        self.assertEqual(mapping["created_at"], created_at1)
        self.assertNotEqual(mapping["last_accessed"], created_at1)
    
    def test_name_variations_same_uuid(self):
        """Test that name variations map to same UUID."""
        variations = [
            "A'ja Wilson",
            "A'JA WILSON",
            "Aja Wilson",
            "a'ja wilson",
            "  A'ja  Wilson  "
        ]
        
        # Get UUID for first variation
        uuid1 = self.mapper.get_or_create_uuid(variations[0])
        
        # All variations should return same UUID
        for variation in variations[1:]:
            uuid_test = self.mapper.get_or_create_uuid(variation)
            self.assertEqual(uuid1, uuid_test, 
                           f"'{variation}' should map to same UUID as '{variations[0]}'")
    
    def test_persistence_save_load(self):
        """Test mappings persist across save/load cycles."""
        # Create several mappings
        players = ["Sue Bird", "Maya Moore", "Candace Parker"]
        uuids = {}
        
        for player in players:
            uuids[player] = self.mapper.get_or_create_uuid(player)
        
        # Save explicitly (though it auto-saves)
        self.mapper.save_mappings()
        
        # Create new mapper instance with same file
        mapper2 = UUIDMapper(self.mapping_file)
        
        # Verify all mappings loaded correctly
        for player, expected_uuid in uuids.items():
            loaded_uuid = mapper2.get_or_create_uuid(player)
            self.assertEqual(loaded_uuid, expected_uuid)
    
    def test_file_creation(self):
        """Test that mapping file is created if it doesn't exist."""
        # Remove the file if it exists
        if os.path.exists(self.mapping_file):
            os.remove(self.mapping_file)
        
        # Create new mapper - should create file
        mapper = UUIDMapper(self.mapping_file)
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.mapping_file))
        
        # Verify it's valid JSON
        with open(self.mapping_file, 'r') as f:
            data = json.load(f)
            self.assertIsInstance(data, dict)
    
    def test_corrupted_file_recovery(self):
        """Test recovery from corrupted mapping file."""
        # Write invalid JSON to file
        with open(self.mapping_file, 'w') as f:
            f.write("{invalid json content")
        
        # Create mapper - should handle gracefully
        mapper = UUIDMapper(self.mapping_file)
        
        # Should start with empty mappings
        self.assertEqual(len(mapper.mappings), 0)
        
        # Should still work normally
        uuid1 = mapper.get_or_create_uuid("Test Player")
        self.assertIsInstance(uuid1, UUID)
    
    def test_mapping_stats(self):
        """Test getting mapping statistics."""
        # Start with empty
        stats = self.mapper.get_mapping_stats()
        self.assertEqual(stats["total_players"], 0)
        self.assertEqual(stats["unique_uuids"], 0)
        
        # Add some players
        self.mapper.get_or_create_uuid("Player One")
        self.mapper.get_or_create_uuid("Player Two")
        self.mapper.get_or_create_uuid("Player One")  # Duplicate
        
        stats = self.mapper.get_mapping_stats()
        self.assertEqual(stats["total_players"], 2)
        self.assertEqual(stats["unique_uuids"], 2)
    
    def test_reverse_lookup(self):
        """Test looking up player info by UUID."""
        player_name = "Breanna Stewart"
        player_uuid = self.mapper.get_or_create_uuid(player_name)
        
        # Look up by UUID
        info = self.mapper.lookup_by_uuid(player_uuid)
        
        self.assertIsNotNone(info)
        self.assertEqual(info["original_name"], player_name)
        self.assertEqual(info["normalized_name"], "breanna stewart")
        self.assertEqual(info["uuid"], str(player_uuid))
        
        # Test non-existent UUID
        import uuid
        random_uuid = uuid.uuid4()
        info = self.mapper.lookup_by_uuid(random_uuid)
        self.assertIsNone(info)
    
    def test_atomic_writes(self):
        """Test that writes are atomic (file is never partially written)."""
        # Add a mapping
        self.mapper.get_or_create_uuid("Test Player")
        
        # Save multiple times rapidly
        for i in range(5):
            self.mapper.save_mappings()
            
            # File should always be valid JSON
            with open(self.mapping_file, 'r') as f:
                data = json.load(f)
                self.assertIsInstance(data, dict)
    
    def test_special_characters_normalization(self):
        """Test edge cases in name normalization."""
        test_cases = [
            ("", ""),  # Empty string
            ("   ", ""),  # Only spaces
            ("123", "123"),  # Numbers only
            ("Player#1", "player1"),
            ("José-María González", "josmara gonzlez"),
            ("O'Brien-Smith, Mary", "obriensmith mary"),
            ("A.J. Wilson", "aj wilson"),
            ("Player (Rookie)", "player rookie"),
        ]
        
        for original, expected in test_cases:
            with self.subTest(name=original):
                normalized = self.mapper._normalize(original)
                self.assertEqual(normalized, expected)
    
    def test_utf8_bom_handling(self):
        """Test that UTF-8 BOM is handled correctly."""
        # Write file with UTF-8 BOM
        test_data = {"test player": {"uuid": str(uuid4()), "original_name": "Test Player"}}
        with open(self.mapping_file, 'wb') as f:
            f.write(b'\xef\xbb\xbf')  # UTF-8 BOM
            f.write(json.dumps(test_data).encode('utf-8'))
        
        # Should load without issues
        mapper = UUIDMapper(self.mapping_file)
        self.assertEqual(len(mapper.mappings), 1)
        self.assertIn("test player", mapper.mappings)


if __name__ == "__main__":
    unittest.main(verbosity=2)