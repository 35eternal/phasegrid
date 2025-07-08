from phasegrid.cycle_tracker import CycleTracker
from phasegrid.uuid_mapper import UUIDMapper
import json

print("Testing CycleTracker + UUID Mapper Integration")
print("=" * 50)

# Create cycle tracker
tracker = CycleTracker("data/test_cycle_integration.json")

# Load test data with player names
with open("data/test_cycle_data_with_names.json", "r") as f:
    test_data = json.load(f)

# Ingest the data
count = tracker.ingest_cycle_data(test_data)
print(f"Ingested {count} cycle entries")
print()

# Show the UUID mappings that were created
print("UUID Mappings Created:")
for name in ["A'ja Wilson", "Breanna Stewart", "Diana Taurasi"]:
    uuid = tracker.uuid_mapper.get_or_create_uuid(name)
    print(f"  {name} -> {uuid}")
print()

# Test phase modifiers
from datetime import date
test_date = date(2025, 7, 8)

print("Phase Modifiers on 2025-07-08:")
for name in ["A'ja Wilson", "Breanna Stewart", "Diana Taurasi"]:
    uuid = tracker.uuid_mapper.get_or_create_uuid(name)
    modifier = tracker.get_phase_modifier(uuid, test_date)
    steals_mod = tracker.get_phase_modifier(uuid, test_date, "steals")
    print(f"  {name}: Base={modifier:.2f}, Steals={steals_mod:.2f}")

# Show statistics
print()
print("Cycle Data Statistics:")
stats = tracker.get_statistics()
for key, value in stats.items():
    print(f"  {key}: {value}")
