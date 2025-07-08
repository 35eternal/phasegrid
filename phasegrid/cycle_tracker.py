"""
PG-109: Menstrual Cycle Tracking Module
Handles cycle data ingestion, storage, and phase-based performance modifiers
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Dict, Optional, Literal
from uuid import UUID, uuid4
import json
from pathlib import Path

# Define cycle phases as a type
CyclePhase = Literal["follicular", "ovulatory", "luteal", "menstrual"]
DataSource = Literal["user_input", "predicted", "imported", "test_fixture"]


@dataclass
class CycleEntry:
    """Privacy-compliant cycle data entry"""
    id: UUID = field(default_factory=uuid4)
    player_id: UUID = field(default_factory=uuid4)
    date: date = field(default_factory=date.today)
    cycle_phase: CyclePhase = "follicular"
    cycle_day: Optional[int] = None
    confidence_score: float = 1.0
    source: DataSource = "user_input"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": str(self.id),
            "player_id": str(self.player_id),
            "date": self.date.isoformat(),
            "cycle_phase": self.cycle_phase,
            "cycle_day": self.cycle_day,
            "confidence_score": self.confidence_score,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CycleEntry":
        """Create from dictionary"""
        return cls(
            id=UUID(data["id"]) if "id" in data else uuid4(),
            player_id=UUID(data["player_id"]),
            date=date.fromisoformat(data["date"]),
            cycle_phase=data["cycle_phase"],
            cycle_day=data.get("cycle_day"),
            confidence_score=data.get("confidence_score", 1.0),
            source=data.get("source", "user_input"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )


class CycleTracker:
    """Manages cycle data ingestion and phase-based performance analysis"""
    
    def __init__(self, data_path: Optional[Path] = None):
        """Initialize cycle tracker with optional data path"""
        self.data_path = data_path or Path("data/cycle_data.json")
        self.cycle_data: Dict[str, List[CycleEntry]] = {}  # player_id -> entries
        
    def ingest_cycle_data(self, entries: List[Dict]) -> int:
        """
        Ingest cycle data from various sources
        
        Args:
            entries: List of cycle data dictionaries
            
        Returns:
            Number of entries successfully ingested
        """
        ingested_count = 0
        
        for entry_data in entries:
            try:
                entry = CycleEntry.from_dict(entry_data)
                player_key = str(entry.player_id)
                
                if player_key not in self.cycle_data:
                    self.cycle_data[player_key] = []
                
                # Check for duplicate entries (same player, same date)
                existing_dates = {e.date for e in self.cycle_data[player_key]}
                if entry.date not in existing_dates:
                    self.cycle_data[player_key].append(entry)
                    ingested_count += 1
                else:
                    print(f"Skipping duplicate entry for player {player_key} on {entry.date}")
                    
            except Exception as e:
                print(f"Error ingesting entry: {e}")
                continue
                
        return ingested_count
    
    def get_phase_modifier(self, player_id: UUID, target_date: date) -> float:
        """
        Calculate performance modifier based on cycle phase
        
        Args:
            player_id: Anonymized player identifier
            target_date: Date to check
            
        Returns:
            Performance modifier (0.8 - 1.2 range)
        """
        # Default modifiers by phase (configurable via YAML later)
        phase_modifiers = {
            "follicular": 1.05,  # Early cycle, rising energy
            "ovulatory": 1.10,   # Peak performance window
            "luteal": 0.95,      # Post-ovulation, declining energy
            "menstrual": 0.90    # Menstruation, lower baseline
        }
        
        player_key = str(player_id)
        if player_key not in self.cycle_data:
            return 1.0  # No data, neutral modifier
        
        # Find the most recent phase entry on or before target date
        player_entries = sorted(
            [e for e in self.cycle_data[player_key] if e.date <= target_date],
            key=lambda x: x.date,
            reverse=True
        )
        
        if not player_entries:
            return 1.0  # No applicable data
        
        latest_entry = player_entries[0]
        days_diff = (target_date - latest_entry.date).days
        
        # If data is too old (>35 days), consider it stale
        if days_diff > 35:
            return 1.0
        
        # Apply confidence-weighted modifier
        base_modifier = phase_modifiers.get(latest_entry.cycle_phase, 1.0)
        return 1.0 + (base_modifier - 1.0) * latest_entry.confidence_score
    
    def save_to_file(self):
        """Persist cycle data to JSON file"""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert all entries to dictionaries
        serializable_data = {
            player_id: [entry.to_dict() for entry in entries]
            for player_id, entries in self.cycle_data.items()
        }
        
        with open(self.data_path, 'w') as f:
            json.dump(serializable_data, f, indent=2)
            
    def load_from_file(self):
        """Load cycle data from JSON file"""
        if not self.data_path.exists():
            print(f"No existing cycle data found at {self.data_path}")
            return
        
        with open(self.data_path, 'r') as f:
            raw_data = json.load(f)
            
        self.cycle_data = {}
        for player_id, entries in raw_data.items():
            self.cycle_data[player_id] = [
                CycleEntry.from_dict(entry) for entry in entries
            ]


# Phase performance configuration (will be moved to YAML config)
DEFAULT_PHASE_CONFIG = {
    "phase_modifiers": {
        "follicular": {
            "base": 1.05,
            "props": {
                "points": 1.03,
                "rebounds": 1.05,
                "assists": 1.04,
                "steals": 1.06,
                "blocks": 1.02
            }
        },
        "ovulatory": {
            "base": 1.10,
            "props": {
                "points": 1.08,
                "rebounds": 1.10,
                "assists": 1.12,
                "steals": 1.15,
                "blocks": 1.08
            }
        },
        "luteal": {
            "base": 0.95,
            "props": {
                "points": 0.96,
                "rebounds": 0.94,
                "assists": 0.95,
                "steals": 0.93,
                "blocks": 0.95
            }
        },
        "menstrual": {
            "base": 0.90,
            "props": {
                "points": 0.92,
                "rebounds": 0.88,
                "assists": 0.90,
                "steals": 0.87,
                "blocks": 0.89
            }
        }
    }
}
