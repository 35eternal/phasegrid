"""
PG-109: Menstrual Cycle Tracking Module
Handles cycle data ingestion, storage, and phase-based performance modifiers
Updated with PG-110: UUID Mapper Integration
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Literal, Tuple
from uuid import UUID, uuid4
import json
from pathlib import Path
from phasegrid.uuid_mapper import UUIDMapper

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
    """Manages menstrual cycle data and performance modifiers"""
    
    # Default phase modifiers (can be overridden by config)
    DEFAULT_PHASE_CONFIG = {
        "follicular": {
            "base_modifier": 1.05,
            "prop_modifiers": {
                "points": 1.03,
                "rebounds": 1.05,
                "assists": 1.04,
                "steals": 1.06,
                "blocks": 1.04,
                "turnovers": 0.98
            }
        },
        "ovulatory": {
            "base_modifier": 1.10,
            "prop_modifiers": {
                "points": 1.08,
                "rebounds": 1.07,
                "assists": 1.09,
                "steals": 1.15,  # Peak reaction time
                "blocks": 1.10,
                "turnovers": 0.95
            }
        },
        "luteal": {
            "base_modifier": 0.95,
            "prop_modifiers": {
                "points": 0.97,
                "rebounds": 0.93,
                "assists": 0.96,
                "steals": 0.94,
                "blocks": 0.92,
                "turnovers": 1.03
            }
        },
        "menstrual": {
            "base_modifier": 0.90,
            "prop_modifiers": {
                "points": 0.92,
                "rebounds": 0.88,  # Physical discomfort impact
                "assists": 0.91,
                "steals": 0.90,
                "blocks": 0.87,
                "turnovers": 1.05
            }
        }
    }
    
    def __init__(self, data_file: str = "data/cycle_data.json"):
        """Initialize the cycle tracker with UUID mapper integration"""
        self.data_file = Path(data_file)
        self.cycle_data: Dict[Tuple[UUID, date], CycleEntry] = {}
        self.uuid_mapper = UUIDMapper()  # PG-110: UUID Mapper Integration
        self._ensure_data_dir()
        self.load_from_file()
        
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
    def ingest_cycle_data(self, entries: List[Dict]) -> int:
        """
        Ingest cycle data from list of dictionaries
        Now supports both player_name and player_id for backward compatibility
        
        Args:
            entries: List of dicts with cycle data
            
        Returns:
            Number of entries successfully ingested
        """
        ingested_count = 0
        
        for entry in entries:
            try:
                # PG-110: Support both player_name and player_id
                if 'player_name' in entry:
                    player_id = self.uuid_mapper.get_or_create_uuid(entry['player_name'])
                elif 'player_id' in entry:
                    player_id = UUID(entry.get('player_id'))
                else:
                    raise ValueError("Entry must contain either 'player_name' or 'player_id'")
                
                # Create cycle entry
                cycle_entry = CycleEntry(
                    player_id=player_id,
                    date=date.fromisoformat(entry['date']),
                    cycle_phase=entry['cycle_phase'],
                    cycle_day=entry.get('cycle_day'),
                    confidence_score=entry.get('confidence_score', 1.0),
                    source=entry.get('source', 'user_input')
                )
                
                # Store with composite key (player_id, date)
                key = (cycle_entry.player_id, cycle_entry.date)
                
                # Only add if not duplicate or if confidence is higher
                if key not in self.cycle_data:
                    self.cycle_data[key] = cycle_entry
                    ingested_count += 1
                else:
                    existing = self.cycle_data[key]
                    if cycle_entry.confidence_score > existing.confidence_score:
                        self.cycle_data[key] = cycle_entry
                        ingested_count += 1
                    else:
                        print(f"Skipping duplicate entry for player {player_id} on {entry['date']}")
                        
            except (ValueError, KeyError) as e:
                print(f"Error ingesting entry: {e}")
                continue
                
        self.save_to_file()
        return ingested_count
        
    def get_phase_modifier(self, player_id: UUID, target_date: date, 
                          prop_type: Optional[str] = None) -> float:
        """
        Get performance modifier for player on given date
        
        Args:
            player_id: Player's UUID
            target_date: Date to check
            prop_type: Optional prop type for specific modifiers
            
        Returns:
            Modifier value (1.0 = neutral)
        """
        # Look for most recent cycle data
        player_entries = [
            (entry_date, entry) for (pid, entry_date), entry in self.cycle_data.items()
            if pid == player_id and entry_date <= target_date
        ]
        
        if not player_entries:
            return 1.0  # No data, neutral modifier
            
        # Sort by date and get most recent
        player_entries.sort(key=lambda x: x[0], reverse=True)
        most_recent_date, most_recent_entry = player_entries[0]
        
        # Check if data is stale (>35 days old)
        days_old = (target_date - most_recent_date).days
        if days_old > 35:
            return 1.0  # Data too old, neutral modifier
            
        # Get phase config
        phase_config = self.DEFAULT_PHASE_CONFIG.get(most_recent_entry.cycle_phase, {})
        
        # Get appropriate modifier
        if prop_type and 'prop_modifiers' in phase_config:
            base_modifier = phase_config['prop_modifiers'].get(prop_type, 
                                                               phase_config.get('base_modifier', 1.0))
        else:
            base_modifier = phase_config.get('base_modifier', 1.0)
            
        # Apply confidence weighting
        confidence_weight = most_recent_entry.confidence_score
        modifier = 1.0 + (base_modifier - 1.0) * confidence_weight
        
        return modifier
        
    def get_player_history(self, player_id: UUID, 
                          start_date: Optional[date] = None,
                          end_date: Optional[date] = None) -> List[CycleEntry]:
        """Get cycle history for a player within date range"""
        entries = []
        
        for (pid, entry_date), entry in self.cycle_data.items():
            if pid != player_id:
                continue
                
            if start_date and entry_date < start_date:
                continue
                
            if end_date and entry_date > end_date:
                continue
                
            entries.append(entry)
            
        return sorted(entries, key=lambda x: x.date)
        
    def save_to_file(self) -> None:
        """Save cycle data to JSON file"""
        data = {
            f"{pid}_{entry_date.isoformat()}": entry.to_dict()
            for (pid, entry_date), entry in self.cycle_data.items()
        }
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
    def load_from_file(self) -> None:
        """Load cycle data from JSON file"""
        if not self.data_file.exists():
            return
            
        try:
            with open(self.data_file, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                
            self.cycle_data = {}
            for key, entry_dict in data.items():
                entry = CycleEntry.from_dict(entry_dict)
                self.cycle_data[(entry.player_id, entry.date)] = entry
                
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading cycle data: {e}")
            self.cycle_data = {}
            
    def get_statistics(self) -> Dict:
        """Get summary statistics about cycle data"""
        if not self.cycle_data:
            return {"total_entries": 0, "unique_players": 0}
            
        unique_players = len(set(pid for pid, _ in self.cycle_data.keys()))
        phase_counts = {}
        
        for entry in self.cycle_data.values():
            phase = entry.cycle_phase
            phase_counts[phase] = phase_counts.get(phase, 0) + 1
            
        return {
            "total_entries": len(self.cycle_data),
            "unique_players": unique_players,
            "phase_distribution": phase_counts,
            "data_sources": list(set(entry.source for entry in self.cycle_data.values()))
        }