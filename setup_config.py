"""Setup configuration files for PhaseGrid."""
import json
from pathlib import Path

def create_config_files():
    """Create default config files if missing."""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Phase mapping config
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
    
    phase_mapping_path = config_dir / "phase_mapping.json"
    if not phase_mapping_path.exists():
        with open(phase_mapping_path, 'w') as f:
            json.dump(phase_mapping, f, indent=2)
        print(f"Created {phase_mapping_path}")
    
    # Kelly divisors config
    kelly_divisors = {
        "conservative": 4,
        "moderate": 3,
        "aggressive": 2,
        "description": "Divisors applied to Kelly criterion for risk management"
    }
    
    kelly_path = config_dir / "phase_kelly_divisors.json"
    if not kelly_path.exists():
        with open(kelly_path, 'w') as f:
            json.dump(kelly_divisors, f, indent=2)
        print(f"Created {kelly_path}")
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    print(f"Ensured {output_dir} exists")
    
    # Create .env template if missing
    env_path = Path(".env")
    if not env_path.exists():
        env_template = """# PhaseGrid Environment Variables
SHEET_ID=1-VX73...VZM
GOOGLE_CREDS=credentials.json
BANKROLL=10000
"""
        with open(env_path, 'w') as f:
            f.write(env_template)
        print(f"Created {env_path} template")

if __name__ == "__main__":
    create_config_files()
    print("\nConfig files initialized successfully!")