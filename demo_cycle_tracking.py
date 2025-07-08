"""
PG-109: Demo script showing cycle-aware performance prediction
"""

from phasegrid.cycle_tracker import CycleTracker
from datetime import date
from uuid import UUID
import json

# Initialize cycle tracker
tracker = CycleTracker()

# Load test data - use utf-8-sig to strip BOM
with open("data/test_cycle_data.json", 'r', encoding='utf-8-sig') as f:
    test_data = json.load(f)

# Ingest the test fixtures
count = tracker.ingest_cycle_data(test_data["test_fixtures"])
print(f"Ingested {count} cycle entries")

# Demo player IDs
player1_id = UUID("550e8400-e29b-41d4-a716-446655440001")
player2_id = UUID("550e8400-e29b-41d4-a716-446655440002")

# Get phase modifiers for today
today = date.today()
print(f"\nPhase modifiers for {today}:")

for player_id, name in [
    (player1_id, "Test Player 1"),
    (player2_id, "Test Player 2")
]:
    modifier = tracker.get_phase_modifier(player_id, today)
    print(f"{name}: {modifier:.2f}x")

# Example: Apply to a projection
base_projection = 25.5  # Points
prop_type = "points"

print(f"\nExample projection adjustment:")
print(f"Base projection: {base_projection} {prop_type}")

for player_id, name in [(player1_id, "Test Player 1")]:
    modifier = tracker.get_phase_modifier(player_id, today)
    adjusted = base_projection * modifier
    print(f"{name}: {adjusted:.1f} {prop_type} (x{modifier:.2f})")

# Show cycle phases
print("\nCurrent cycle phases:")
for player_id in [player1_id, player2_id]:
    entries = tracker.cycle_data.get(str(player_id), [])
    if entries:
        latest = max(entries, key=lambda x: x.date)
        print(f"Player {str(player_id)[:8]}...: {latest.cycle_phase} (as of {latest.date})")

# Load and apply prop-specific modifiers
print("\n" + "="*50)
print("PROP-SPECIFIC MODIFIERS DEMO")
print("="*50)

with open("config/cycle_config.json", 'r', encoding='utf-8-sig') as f:
    cycle_config = json.load(f)

# Test Player 1 is in ovulatory phase (as of 2025-07-08)
print(f"\nTest Player 1 - Ovulatory Phase Performance Modifiers:")
ovulatory_mods = cycle_config["phase_modifiers"]["ovulatory"]["prop_modifiers"]

props_and_projections = [
    ("points", 25.5),
    ("rebounds", 8.2),
    ("assists", 5.5),
    ("steals", 2.1),
    ("blocks", 1.3)
]

for prop, base in props_and_projections:
    modifier = ovulatory_mods.get(prop, 1.0)
    adjusted = base * modifier
    print(f"  {prop:10s}: {base:5.1f} → {adjusted:5.1f} (x{modifier:.2f})")

# Test Player 2 is in menstrual phase
print(f"\nTest Player 2 - Menstrual Phase Performance Modifiers:")
menstrual_mods = cycle_config["phase_modifiers"]["menstrual"]["prop_modifiers"]

for prop, base in props_and_projections:
    modifier = menstrual_mods.get(prop, 1.0)
    adjusted = base * modifier
    print(f"  {prop:10s}: {base:5.1f} → {adjusted:5.1f} (x{modifier:.2f})")
