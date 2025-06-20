"""Quick fix script to get PhaseGrid running immediately."""
import os
import json
from pathlib import Path

def create_directories():
    """Create necessary directories."""
    dirs = ['config', 'output', 'scripts', 'tests']
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
    print("✓ Created directories")

def create_config_files():
    """Create config files with defaults."""
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
    
    with open('config/phase_mapping.json', 'w') as f:
        json.dump(phase_mapping, f, indent=2)
    print("✓ Created config/phase_mapping.json")
    
    # Kelly divisors
    kelly_divisors = {
        "conservative": 4,
        "moderate": 3,
        "aggressive": 2,
        "description": "Divisors applied to Kelly criterion for risk management"
    }
    
    with open('config/phase_kelly_divisors.json', 'w') as f:
        json.dump(kelly_divisors, f, indent=2)
    print("✓ Created config/phase_kelly_divisors.json")
    
    # Create .env if missing
    if not Path('.env').exists():
        with open('.env', 'w') as f:
            f.write("""# PhaseGrid Environment Variables
SHEET_ID=1-VX73...VZM
GOOGLE_CREDS=credentials.json
BANKROLL=10000
""")
        print("✓ Created .env template")

def create_minimal_requirements():
    """Create minimal working requirements.txt."""
    requirements = """# Core dependencies only
pandas
numpy
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
pytest
pytest-cov
python-dotenv
"""
    with open('requirements_minimal.txt', 'w') as f:
        f.write(requirements)
    print("✓ Created requirements_minimal.txt")

def test_paper_trader():
    """Test if paper_trader can run."""
    try:
        print("\n--- Testing paper_trader.py ---")
        import subprocess
        result = subprocess.run(
            ['python', 'paper_trader.py'], 
            capture_output=True, 
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✓ Paper trader completed successfully!")
            print("\n--- Output ---")
            print(result.stdout)
        else:
            print("✗ Paper trader failed:")
            print(result.stderr)
            
    except Exception as e:
        print(f"✗ Could not run paper trader: {e}")

if __name__ == "__main__":
    print("=== PhaseGrid Quick Fix ===\n")
    
    # Create all necessary files
    create_directories()
    create_config_files()
    create_minimal_requirements()
    
    print("\n=== Setup Complete ===")
    print("\nNext steps:")
    print("1. Install minimal dependencies:")
    print("   pip install pandas numpy")
    print("\n2. Run paper trader:")
    print("   python paper_trader.py")
    
    # Try running paper trader
    print("\nAttempting to run paper_trader now...")
    test_paper_trader()