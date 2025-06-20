#!/usr/bin/env python3
"""Fix payout configuration issues."""

import json
from pathlib import Path

def check_and_fix_payout_config():
    """Check and fix the payout configuration."""
    config_path = Path("config/payout_tables.json")
    
    print("Checking payout configuration...")
    
    # Read current config
    if config_path.exists():
        with open(config_path, 'r') as f:
            current_config = json.load(f)
        print(f"Current config: {json.dumps(current_config, indent=2)}")
    else:
        print("No payout config found!")
        current_config = {}
    
    # Correct configuration structure
    correct_config = {
        "POWER": {
            "2_legs": 3.0,
            "3_legs": 6.0
        },
        "FLEX": {
            "2_legs": {
                "0_correct": 0.0,
                "1_correct": 0.4,
                "2_correct": 2.5
            },
            "3_legs": {
                "0_correct": 0.0,
                "1_correct": 0.25,
                "2_correct": 1.2,
                "3_correct": 5.0
            }
        }
    }
    
    # Check if we need to update
    if current_config != correct_config:
        print("\nConfig needs updating. Creating correct structure...")
        
        # Backup existing if it exists
        if config_path.exists():
            backup_path = config_path.with_suffix('.json.backup')
            config_path.rename(backup_path)
            print(f"Backed up existing config to: {backup_path}")
        
        # Write correct config
        with open(config_path, 'w') as f:
            json.dump(correct_config, f, indent=2)
        
        print("✅ Payout configuration fixed!")
    else:
        print("✅ Payout configuration is already correct!")
    
    # Also check phase kelly divisors
    phase_config_path = Path("config/phase_kelly_divisors.json")
    if phase_config_path.exists():
        with open(phase_config_path, 'r') as f:
            phase_config = json.load(f)
        print(f"\nPhase divisors config: {json.dumps(phase_config, indent=2)}")
    else:
        print("\nNo phase divisors config found. Creating default...")
        default_phase_config = {
            "phase_divisors": {
                "follicular": "8.0 - 2.0 * win_rate",
                "ovulation": "12.0 - 4.0 * win_rate",
                "luteal": "6.0 - 1.5 * win_rate",
                "menstrual": "10.0 - 3.0 * win_rate",
                "unknown": "15.0"
            }
        }
        with open(phase_config_path, 'w') as f:
            json.dump(default_phase_config, f, indent=2)
        print("✅ Phase divisors configuration created!")

if __name__ == "__main__":
    check_and_fix_payout_config()