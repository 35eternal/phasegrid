"""Fix JSON files created by PowerShell with BOM."""
import json
from pathlib import Path

def fix_json_file(filepath):
    """Read and rewrite JSON file without BOM."""
    try:
        # Read with utf-8-sig to handle BOM
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        
        # Write back without BOM
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Fixed {filepath}")
        return True
    except Exception as e:
        print(f"✗ Error fixing {filepath}: {e}")
        return False

def create_clean_configs():
    """Create clean config files."""
    # Ensure directories exist
    Path("config").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)
    
    # Phase mapping
    phase_mapping = {
        "conservative": {
            "threshold": 0.55,
            "confidence": 0.60,
            "max_exposure": 0.02
        },
        "moderate": {
            "threshold": 0.58,
            "confidence": 0.63,
            "max_exposure": 0.03
        },
        "aggressive": {
            "threshold": 0.60,
            "confidence": 0.65,
            "max_exposure": 0.05
        }
    }
    
    with open('config/phase_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(phase_mapping, f, indent=2)
    print("✓ Created clean config/phase_mapping.json")
    
    # Kelly divisors
    kelly_divisors = {
        "conservative": 4,
        "moderate": 3,
        "aggressive": 2
    }
    
    with open('config/phase_kelly_divisors.json', 'w', encoding='utf-8') as f:
        json.dump(kelly_divisors, f, indent=2)
    print("✓ Created clean config/phase_kelly_divisors.json")

if __name__ == "__main__":
    print("=== Fixing JSON Files ===\n")
    
    # Try to fix existing files
    config_files = [
        'config/phase_mapping.json',
        'config/phase_kelly_divisors.json'
    ]
    
    files_fixed = 0
    for filepath in config_files:
        if Path(filepath).exists():
            if fix_json_file(filepath):
                files_fixed += 1
    
    # If no files were fixed, create new ones
    if files_fixed == 0:
        print("\nCreating new clean config files...")
        create_clean_configs()
    
    print("\n✓ JSON files are now clean and ready!")
    print("\nRun: python paper_trader.py")