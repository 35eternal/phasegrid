"""
PG-109: Integration script to add cycle tracking to SlipOptimizer
This script patches the existing SlipOptimizer to use cycle phase modifiers
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from phasegrid.cycle_tracker import CycleTracker
from datetime import date
import yaml


def load_cycle_config():
    """Load cycle configuration from YAML"""
    config_path = project_root / "config" / "cycle_config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def patch_slip_optimizer():
    """Create a patched version of slip_optimizer.py with cycle tracking"""
    
    # Read the current slip_optimizer.py
    optimizer_path = project_root / "slip_optimizer.py"
    with open(optimizer_path, 'r') as f:
        content = f.read()
    
    # Find the import section
    import_section_end = content.find('\n\n')
    
    # Add cycle tracker import
    new_imports = """from phasegrid.cycle_tracker import CycleTracker
from datetime import date
import yaml"""
    
    # Insert after existing imports
    patched_content = content[:import_section_end] + '\n' + new_imports + content[import_section_end:]
    
    # Add cycle tracking to the SlipOptimizer class
    class_patch = '''
    def apply_cycle_modifiers(self, player_id, prop_type, base_projection, game_date=None):
        """Apply cycle phase modifiers to player projections"""
        if not hasattr(self, 'cycle_tracker'):
            self.cycle_tracker = CycleTracker()
            self.cycle_tracker.load_from_file()
            
        if not hasattr(self, 'cycle_config'):
            config_path = Path("config/cycle_config.yaml")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.cycle_config = yaml.safe_load(f)
            else:
                return base_projection
                
        if not self.cycle_config.get('cycle_tracking', {}).get('enabled', False):
            return base_projection
            
        # Use game date or today
        target_date = game_date or date.today()
        
        # Get phase modifier
        phase_modifier = self.cycle_tracker.get_phase_modifier(player_id, target_date)
        
        # Apply prop-specific modifier if available
        if self.cycle_config.get('cycle_tracking', {}).get('use_prop_specific_modifiers', False):
            # Get current phase for the player
            player_entries = self.cycle_tracker.cycle_data.get(str(player_id), [])
            if player_entries:
                latest_entry = max(player_entries, key=lambda x: x.date)
                if (target_date - latest_entry.date).days <= 35:
                    phase = latest_entry.cycle_phase
                    prop_modifiers = self.cycle_config['phase_modifiers'][phase]['prop_modifiers']
                    if prop_type.lower() in prop_modifiers:
                        phase_modifier = prop_modifiers[prop_type.lower()]
        
        return base_projection * phase_modifier
'''
    
    # Save the patched version
    output_path = project_root / "slip_optimizer_with_cycles.py"
    with open(output_path, 'w') as f:
        f.write(patched_content)
    
    print(f"Created patched SlipOptimizer at: {output_path}")
    print("\nTo integrate:")
    print("1. Review the changes in slip_optimizer_with_cycles.py")
    print("2. Manually integrate the apply_cycle_modifiers method into slip_optimizer.py")
    print("3. Call apply_cycle_modifiers when processing player projections")


def create_demo_script():
    """Create a demo script showing cycle tracking in action"""
    demo_content = '''"""
PG-109: Demo script showing cycle-aware performance prediction
"""

from phasegrid.cycle_tracker import CycleTracker
from datetime import date
from uuid import UUID
import json

# Initialize cycle tracker
tracker = CycleTracker()

# Load test data
with open("data/test_cycle_data.json", 'r') as f:
    test_data = json.load(f)

# Ingest the test fixtures
count = tracker.ingest_cycle_data(test_data["test_fixtures"])
print(f"Ingested {count} cycle entries")

# Demo player IDs
player1_id = UUID("550e8400-e29b-41d4-a716-446655440001")
player2_id = UUID("550e8400-e29b-41d4-a716-446655440002")

# Get phase modifiers for today
today = date.today()
print(f"\\nPhase modifiers for {today}:")

for player_id, name in [
    (player1_id, "Test Player 1"),
    (player2_id, "Test Player 2")
]:
    modifier = tracker.get_phase_modifier(player_id, today)
    print(f"{name}: {modifier:.2f}x")

# Example: Apply to a projection
base_projection = 25.5  # Points
prop_type = "points"

print(f"\\nExample projection adjustment:")
print(f"Base projection: {base_projection} {prop_type}")

for player_id, name in [(player1_id, "Test Player 1")]:
    modifier = tracker.get_phase_modifier(player_id, today)
    adjusted = base_projection * modifier
    print(f"{name}: {adjusted:.1f} {prop_type} (x{modifier:.2f})")

# Show cycle phases
print("\\nCurrent cycle phases:")
for player_id in [player1_id, player2_id]:
    entries = tracker.cycle_data.get(str(player_id), [])
    if entries:
        latest = max(entries, key=lambda x: x.date)
        print(f"Player {str(player_id)[:8]}...: {latest.cycle_phase} (as of {latest.date})")
'''
    
    demo_path = project_root / "demo_cycle_tracking.py"
    with open(demo_path, 'w') as f:
        f.write(demo_content)
    
    print(f"\nCreated demo script at: {demo_path}")


if __name__ == "__main__":
    print("PG-109: Integrating cycle tracking with SlipOptimizer")
    print("=" * 50)
    
    # Load and display config
    config = load_cycle_config()
    print("\nCycle tracking enabled:", config['cycle_tracking']['enabled'])
    print("Phase modifiers loaded:", list(config['phase_modifiers'].keys()))
    
    # Create integration files
    patch_slip_optimizer()
    create_demo_script()
    
    print("\n✅ Integration files created successfully!")
