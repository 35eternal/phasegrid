from phasegrid.cycle_tracker import CycleTracker
import json
from datetime import date, timedelta

print("Full PhasGrid Integration Demo")
print("=" * 50)

# Initialize tracker
tracker = CycleTracker()

# Sample data with player names (no UUIDs needed!)
new_entries = [
    {
        "player_name": "A'ja Wilson",
        "date": date.today().isoformat(),
        "cycle_phase": "ovulatory",
        "cycle_day": 14,
        "confidence_score": 0.95
    },
    {
        "player_name": "Breanna Stewart", 
        "date": date.today().isoformat(),
        "cycle_phase": "follicular",
        "cycle_day": 7,
        "confidence_score": 0.90
    },
    {
        "player_name": "A'JA WILSON",  # Different formatting!
        "date": (date.today() - timedelta(days=1)).isoformat(),
        "cycle_phase": "ovulatory",
        "cycle_day": 13,
        "confidence_score": 0.95
    }
]

# Ingest data
count = tracker.ingest_cycle_data(new_entries)
print(f"Ingested {count} entries")
print()

# Check how many unique players we have
stats = tracker.get_statistics()
print(f"Unique players tracked: {stats['unique_players']}")
print(f"Total entries: {stats['total_entries']}")
print()

# Show that "A'ja Wilson" and "A'JA WILSON" are the same player
uuid_aja = tracker.uuid_mapper.get_or_create_uuid("A'ja Wilson")
history = tracker.get_player_history(uuid_aja)
print(f"A'ja Wilson history entries: {len(history)}")
for entry in history:
    print(f"  - {entry.date}: {entry.cycle_phase} (confidence: {entry.confidence_score})")
