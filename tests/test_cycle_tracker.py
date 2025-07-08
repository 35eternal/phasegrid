"""
PG-109: Unit tests for CycleTracker module
Tests cycle data ingestion, phase modifiers, and privacy compliance
"""

import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4
import json
import tempfile
import os

from phasegrid.cycle_tracker import (
    CycleEntry, CycleTracker, DEFAULT_PHASE_CONFIG
)


class TestCycleEntry(unittest.TestCase):
    """Test CycleEntry dataclass functionality"""
    
    def test_cycle_entry_creation(self):
        """Test creating a CycleEntry with default values"""
        entry = CycleEntry()
        self.assertIsInstance(entry.id, UUID)
        self.assertIsInstance(entry.player_id, UUID)
        self.assertEqual(entry.cycle_phase, "follicular")
        self.assertEqual(entry.confidence_score, 1.0)
        self.assertEqual(entry.source, "user_input")
    
    def test_cycle_entry_serialization(self):
        """Test to_dict and from_dict methods"""
        original = CycleEntry(
            player_id=uuid4(),
            date=date(2025, 7, 8),
            cycle_phase="ovulatory",
            cycle_day=14,
            confidence_score=0.95,
            source="predicted"
        )
        
        # Convert to dict and back
        entry_dict = original.to_dict()
        restored = CycleEntry.from_dict(entry_dict)
        
        self.assertEqual(str(original.id), str(restored.id))
        self.assertEqual(str(original.player_id), str(restored.player_id))
        self.assertEqual(original.date, restored.date)
        self.assertEqual(original.cycle_phase, restored.cycle_phase)
        self.assertEqual(original.cycle_day, restored.cycle_day)
        self.assertEqual(original.confidence_score, restored.confidence_score)
        self.assertEqual(original.source, restored.source)


class TestCycleTracker(unittest.TestCase):
    """Test CycleTracker functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_path = Path(self.temp_dir) / "test_cycle.json"
        self.tracker = CycleTracker(data_path=self.test_data_path)
        
        # Create test player IDs
        self.player1_id = UUID("550e8400-e29b-41d4-a716-446655440001")
        self.player2_id = UUID("550e8400-e29b-41d4-a716-446655440002")
        self.player3_id = UUID("550e8400-e29b-41d4-a716-446655440003")
    
    def tearDown(self):
        """Clean up test files"""
        if self.test_data_path.exists():
            os.remove(self.test_data_path)
        os.rmdir(self.temp_dir)
    
    def test_ingest_cycle_data(self):
        """Test ingesting cycle data from list of dicts"""
        test_data = [
            {
                "player_id": str(self.player1_id),
                "date": "2025-07-01",
                "cycle_phase": "follicular",
                "cycle_day": 7,
                "confidence_score": 1.0,
                "source": "test_fixture"
            },
            {
                "player_id": str(self.player1_id),
                "date": "2025-07-08",
                "cycle_phase": "ovulatory",
                "cycle_day": 14,
                "confidence_score": 1.0,
                "source": "test_fixture"
            },
            {
                "player_id": str(self.player2_id),
                "date": "2025-07-08",
                "cycle_phase": "menstrual",
                "cycle_day": 2,
                "confidence_score": 0.9,
                "source": "user_input"
            }
        ]
        
        # Ingest data
        count = self.tracker.ingest_cycle_data(test_data)
        self.assertEqual(count, 3)
        
        # Verify data was stored correctly
        self.assertEqual(len(self.tracker.cycle_data), 2)  # 2 players
        self.assertEqual(len(self.tracker.cycle_data[str(self.player1_id)]), 2)
        self.assertEqual(len(self.tracker.cycle_data[str(self.player2_id)]), 1)
    
    def test_duplicate_entry_handling(self):
        """Test that duplicate entries (same player, same date) are rejected"""
        test_data = [
            {
                "player_id": str(self.player1_id),
                "date": "2025-07-08",
                "cycle_phase": "follicular",
                "cycle_day": 7
            },
            {
                "player_id": str(self.player1_id),
                "date": "2025-07-08",  # Same date
                "cycle_phase": "ovulatory",
                "cycle_day": 14
            }
        ]
        
        count = self.tracker.ingest_cycle_data(test_data)
        self.assertEqual(count, 1)  # Only first entry should be added
        self.assertEqual(len(self.tracker.cycle_data[str(self.player1_id)]), 1)
    
    def test_get_phase_modifier_basic(self):
        """Test basic phase modifier calculation"""
        # Add test data
        test_data = [
            {
                "player_id": str(self.player1_id),
                "date": "2025-07-08",
                "cycle_phase": "ovulatory",
                "confidence_score": 1.0
            }
        ]
        self.tracker.ingest_cycle_data(test_data)
        
        # Test exact date match
        modifier = self.tracker.get_phase_modifier(self.player1_id, date(2025, 7, 8))
        self.assertEqual(modifier, 1.10)  # Ovulatory phase modifier
        
        # Test future date (within 35 days)
        modifier = self.tracker.get_phase_modifier(self.player1_id, date(2025, 7, 15))
        self.assertEqual(modifier, 1.10)
    
    def test_get_phase_modifier_confidence_weighted(self):
        """Test that confidence score affects the modifier"""
        test_data = [
            {
                "player_id": str(self.player1_id),
                "date": "2025-07-08",
                "cycle_phase": "ovulatory",
                "confidence_score": 0.5  # 50% confidence
            }
        ]
        self.tracker.ingest_cycle_data(test_data)
        
        modifier = self.tracker.get_phase_modifier(self.player1_id, date(2025, 7, 8))
        # Expected: 1.0 + (1.10 - 1.0) * 0.5 = 1.05
        self.assertEqual(modifier, 1.05)
    
    def test_get_phase_modifier_stale_data(self):
        """Test that data older than 35 days returns neutral modifier"""
        test_data = [
            {
                "player_id": str(self.player1_id),
                "date": "2025-05-01",
                "cycle_phase": "ovulatory",
                "confidence_score": 1.0
            }
        ]
        self.tracker.ingest_cycle_data(test_data)
        
        # Check date 40 days later
        modifier = self.tracker.get_phase_modifier(self.player1_id, date(2025, 6, 10))
        self.assertEqual(modifier, 1.0)  # Neutral modifier for stale data
    
    def test_get_phase_modifier_no_data(self):
        """Test modifier for player with no cycle data"""
        modifier = self.tracker.get_phase_modifier(self.player3_id, date(2025, 7, 8))
        self.assertEqual(modifier, 1.0)  # Neutral modifier
    
    def test_all_phase_modifiers(self):
        """Test modifiers for all cycle phases"""
        phases_and_expected = [
            ("follicular", 1.05),
            ("ovulatory", 1.10),
            ("luteal", 0.95),
            ("menstrual", 0.90)
        ]
        
        for phase, expected in phases_and_expected:
            self.tracker.cycle_data.clear()
            test_data = [{
                "player_id": str(self.player1_id),
                "date": "2025-07-08",
                "cycle_phase": phase,
                "confidence_score": 1.0
            }]
            self.tracker.ingest_cycle_data(test_data)
            
            modifier = self.tracker.get_phase_modifier(self.player1_id, date(2025, 7, 8))
            self.assertEqual(modifier, expected, f"Failed for phase: {phase}")
    
    def test_save_and_load_file(self):
        """Test persisting and loading cycle data"""
        # Add test data
        test_data = [
            {
                "player_id": str(self.player1_id),
                "date": "2025-07-01",
                "cycle_phase": "follicular",
                "cycle_day": 7
            },
            {
                "player_id": str(self.player2_id),
                "date": "2025-07-08",
                "cycle_phase": "menstrual",
                "cycle_day": 2
            }
        ]
        self.tracker.ingest_cycle_data(test_data)
        
        # Save to file
        self.tracker.save_to_file()
        self.assertTrue(self.test_data_path.exists())
        
        # Create new tracker and load
        new_tracker = CycleTracker(data_path=self.test_data_path)
        new_tracker.load_from_file()
        
        # Verify data was loaded correctly
        self.assertEqual(len(new_tracker.cycle_data), 2)
        self.assertEqual(len(new_tracker.cycle_data[str(self.player1_id)]), 1)
        self.assertEqual(len(new_tracker.cycle_data[str(self.player2_id)]), 1)
    
    def test_privacy_compliance(self):
        """Test that player IDs are properly anonymized"""
        # Ensure no real names in the data structure
        entry = CycleEntry(player_id=self.player1_id)
        entry_dict = entry.to_dict()
        
        # Check that player_id is UUID string
        self.assertIsInstance(entry_dict["player_id"], str)
        self.assertEqual(len(entry_dict["player_id"]), 36)  # UUID string length
        
        # Ensure no PII fields exist
        forbidden_fields = ["name", "birth_date", "email", "phone"]
        for field in forbidden_fields:
            self.assertNotIn(field, entry_dict)


class TestPhaseConfiguration(unittest.TestCase):
    """Test phase configuration and prop-specific modifiers"""
    
    def test_default_phase_config_structure(self):
        """Test that DEFAULT_PHASE_CONFIG has expected structure"""
        self.assertIn("phase_modifiers", DEFAULT_PHASE_CONFIG)
        
        phases = ["follicular", "ovulatory", "luteal", "menstrual"]
        props = ["points", "rebounds", "assists", "steals", "blocks"]
        
        for phase in phases:
            self.assertIn(phase, DEFAULT_PHASE_CONFIG["phase_modifiers"])
            phase_config = DEFAULT_PHASE_CONFIG["phase_modifiers"][phase]
            
            self.assertIn("base", phase_config)
            self.assertIn("props", phase_config)
            
            for prop in props:
                self.assertIn(prop, phase_config["props"])
                self.assertIsInstance(phase_config["props"][prop], (int, float))


if __name__ == "__main__":
    unittest.main()
