"""
WNBA Predictor - Main Pipeline
Clean, organized entry point for the betting system
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def main():
    print("🏀 WNBA PREDICTOR - ORGANIZED PIPELINE")
    print("=" * 50)
    
    try:
        # Import core modules
        from core import scraper, mapper, gamelog, analyzer, cycle_detector
        print("✅ Core modules imported successfully")
        
        # Import configuration
        import config
        print("✅ Configuration loaded")
        
        print("\n📁 Project structure organized:")
        print("   core/         - Main system modules")
        print("   scripts/      - Organized utility scripts")
        print("   data/         - All data files")
        print("   models/       - ML models and features")
        print("   dev/          - Development tools")
        
        print("\n🎯 System ready for player mapping and deployment!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Check that all modules are properly organized")

if __name__ == "__main__":
    main()