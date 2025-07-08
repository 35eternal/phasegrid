"""
Test suite for CycleTracker module
Tests cycle data ingestion, phase modifiers, and privacy compliance
"""

import unittest
import tempfile
import json
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4
from pathlib import Path
import os

from phasegrid.cycle_tracker import CycleEntry, CycleTracker


class TestCycleEntry(unittest.TestCase):
    """Test the CycleEntry dataclass"""
    
    def test_cycle_entry_creation(self):
        """Test creating a CycleEntry with default values"""
        entry = CycleEntry()
        
        self.assertIsInstance(entry.id, UUID)
        self.assertIsInstance(entry.player_id, UUID)
        self.assertEqual(entry.date, date.today())
        self.assertEqual(entry.cycle_phase, "follicular")
        self.assertEqual(entry.confidence_score, 1.0)
        
    def test_cycle_entry_serialization(self):
        """Test to_dict and from_dict methods"""
        original = CycleEntry(
            player_id=uuid4(),
            date=date(2025, 7, 8),
            cycle_phase="ovulatory",
            cycle_day=14,
            confidence_score=0.95
        )
        
        # Serialize
        data = original.to_dict()
        self.assertIsInstance(data, dict)
        self.assertIn("player_id", data)
        self.assertIn("date", data)
        
        # Deserialize
        loaded = CycleEntry.from_dict(data)
        self.assertEqual(loaded.player_id, original.player_id)
        self.assertEqual(loaded.date, original.date)
        self.assertEqual(loaded.cycle_phase, original.cycle_phase)


class TestCycleTracker(unittest.TestCase):
    """Test the CycleTracker class"""
    
    def setUp(self):
        """Create temp file for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_file = os.path.join(self.temp_dir, "test_cycle_data.json")
        self.tracker = CycleTracker(data_file=self.data_file)  # Use data_file, not data_path
        
    def tearDown(self):
        """Clean up temp files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_ingest_cycle_data(self):
        """Test ingesting cycle data from list of dicts"""
        test_data = [
            {
                "player_id": str(uuid4()),
                "date": "2025-07-08",
                "cycle_phase": "follicular",
                "cycle_day": 7,
                "confidence_score": 0.9
            },
            {
                "player_name": "Test Player",  # Test name-based input
                "date": "2025-07-08", 
                "cycle_phase": "ovulatory",
                "cycle_day": 14,
                "confidence_score": 0.95
            }
        ]
        
        count = self.tracker.ingest_cycle_data(test_data)
        self.assertEqual(count, 2)
        
    def test_duplicate_entry_handling(self):
        """Test that duplicate entries (same player, same date) are rejected"""
        player_id = uuid4()
        test_data = [
            {
                "player_id": str(player_id),
                "date": "2025-07-08",
                "cycle_phase": "follicular",
                "confidence_score": 0.8
            },
            {
                "player_id": str(player_id),
                "date": "2025-07-08",  # Same date
                "cycle_phase": "ovulatory",
                "confidence_score": 0.7  # Lower confidence
            }
        ]
        
        count = self.tracker.ingest_cycle_data(test_data)
        self.assertEqual(count, 1)  # Second entry should be skipped
        
    def test_get_phase_modifier_basic(self):
        """Test basic phase modifier calculation"""
        player_id = uuid4()
        test_date = date.today()
        
        # Ingest test data
        self.tracker.ingest_cycle_data([{
            "player_id": str(player_id),
            "date": test_date.isoformat(),
            "cycle_phase": "ovulatory",
            "confidence_score": 1.0
        }])
        
        # Get modifier
        modifier = self.tracker.get_phase_modifier(player_id, test_date)
        self.assertAlmostEqual(modifier, 1.10, places=2)
        
    def test_get_phase_modifier_no_data(self):
        """Test modifier for player with no cycle data"""
        random_player = uuid4()
        modifier = self.tracker.get_phase_modifier(random_player, date.today())
        self.assertEqual(modifier, 1.0)  # Neutral modifier
        
    def test_get_phase_modifier_stale_data(self):
        """Test that data older than 35 days returns neutral modifier"""
        player_id = uuid4()
        old_date = date.today() - timedelta(days=40)
        
        # Ingest old data
        self.tracker.ingest_cycle_data([{
            "player_id": str(player_id),
            "date": old_date.isoformat(),
            "cycle_phase": "ovulatory",
            "confidence_score": 1.0
        }])
        
        # Check modifier for today (40 days later)
        modifier = self.tracker.get_phase_modifier(player_id, date.today())
        self.assertEqual(modifier, 1.0)  # Should be neutral due to staleness
        
    def test_get_phase_modifier_confidence_weighted(self):
        """Test that confidence score affects the modifier"""
        player_id = uuid4()
        test_date = date.today()
        
        # Test with 50% confidence
        self.tracker.ingest_cycle_data([{
            "player_id": str(player_id),
            "date": test_date.isoformat(),
            "cycle_phase": "ovulatory",  # Base modifier 1.10
            "confidence_score": 0.5
        }])
        
        modifier = self.tracker.get_phase_modifier(player_id, test_date)
        # Should be 1.0 + (1.10 - 1.0) * 0.5 = 1.05
        self.assertAlmostEqual(modifier, 1.05, places=2)
        
    def test_save_and_load_file(self):
        """Test persisting and loading cycle data"""
        player_id = uuid4()
        
        # Ingest some data
        self.tracker.ingest_cycle_data([{
            "player_id": str(player_id),
            "date": "2025-07-08",
            "cycle_phase": "luteal"
        }])
        
        # Save
        self.tracker.save_to_file()
        
        # Create new tracker with same file
        new_tracker = CycleTracker(data_file=self.data_file)
        
        # Should have the same data
        modifier = new_tracker.get_phase_modifier(player_id, date(2025, 7, 8))
        self.assertLess(modifier, 1.0)  # Luteal phase has negative modifier
        
    def test_privacy_compliance(self):
        """Test that player IDs are properly anonymized"""
        # This is more of an integration test with uuid_mapper
        test_data = [{
            "player_name": "Test Player",
            "date": "2025-07-08",
            "cycle_phase": "follicular"
        }]
        
        count = self.tracker.ingest_cycle_data(test_data)
        self.assertEqual(count, 1)
        
        # Check that a UUID was created
        uuid = self.tracker.uuid_mapper.get_or_create_uuid("Test Player")
        self.assertIsInstance(uuid, UUID)
        
    def test_all_phase_modifiers(self):
        """Test modifiers for all cycle phases"""
        player_id = uuid4()
        base_date = date.today()
        
        phases_and_modifiers = [
            ("follicular", 1.05),
            ("ovulatory", 1.10),
            ("luteal", 0.95),
            ("menstrual", 0.90)
        ]
        
        for phase, expected_modifier in phases_and_modifiers:
            # Clear existing data
            self.tracker.cycle_data.clear()
            
            # Ingest data for this phase
            self.tracker.ingest_cycle_data([{
                "player_id": str(player_id),
                "date": base_date.isoformat(),
                "cycle_phase": phase,
                "confidence_score": 1.0
            }])
            
            # Check modifier
            modifier = self.tracker.get_phase_modifier(player_id, base_date)
            self.assertAlmostEqual(modifier, expected_modifier, places=2,
                                 msg=f"Failed for phase: {phase}")


class TestPhaseConfiguration(unittest.TestCase):
    """Test phase configuration structure"""
    
    def test_default_phase_config_structure(self):
        """Test that DEFAULT_PHASE_CONFIG has expected structure"""
        # Access from the class
        config = CycleTracker.DEFAULT_PHASE_CONFIG
        
        # Check all phases exist
        expected_phases = ["follicular", "ovulatory", "luteal", "menstrual"]
        for phase in expected_phases:
            self.assertIn(phase, config)
            
        # Check structure
        for phase, phase_config in config.items():
            self.assertIn("base_modifier", phase_config)
            self.assertIn("prop_modifiers", phase_config)
            
            # Check prop modifiers
            prop_mods = phase_config["prop_modifiers"]
            expected_props = ["points", "rebounds", "assists", "steals", "blocks", "turnovers"]
            for prop in expected_props:
                self.assertIn(prop, prop_mods)


if __name__ == "__main__":
    unittest.main()