#!/usr/bin/env python3
"""
Orchestration script to automate WNBA betting prediction pipeline.
Must be run from project root directory.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_script(script_path):
    """Execute a Python script and handle errors."""
    print(f"\n>>> Running: {script_path}")
    print("-" * 60)
    
    # Set UTF-8 encoding for Windows
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True,
            env=env,
            encoding='utf-8'
        )
        
        # Print stdout if any
        if result.stdout:
            print(result.stdout)
            
        print(f"✓ {script_path} completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: {script_path} failed with exit code {e.returncode}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Failed to run {script_path}: {str(e)}")
        return False


def verify_output_files():
    """Check if expected output files exist."""
    required_files = [
        "output/trap_lines.csv",
        "output/optimal_goblin_slate.csv",
        "data/wnba_clean_props_for_betting.csv"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ Found: {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            all_exist = False
            
    return all_exist


def main():
    """Run the complete WNBA prediction pipeline."""
    
    # Define scripts in execution order
    scripts = [
        "scripts/scraping/fetch_and_parse_prizepicks.py",
        "scripts/mapping/map_prizepicks_names.py",
        "scripts/prediction/run_prop_predictions.py",
        "scripts/prediction/verify_trap_props.py",
        "scripts/prediction/aggressive_trap_detector.py",
        "scripts/prediction/prepare_clean_props.py",
        "scripts/prediction/updated_betting_strategy.py"
    ]
    
    print("🏀 WNBA Daily Prediction Pipeline")
    print("=" * 60)
    
    # Run each script in order
    for script in scripts:
        if not run_script(script):
            print(f"\n❌ Pipeline failed at: {script}")
            print("Exiting...")
            sys.exit(1)
    
    # Verify output files
    print("\n" + "=" * 60)#!/usr/bin/env python3
"""
Orchestration script to automate WNBA betting prediction pipeline.
Must be run from project root directory.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_script(script_path):
    """Execute a Python script and handle errors."""
    print(f"\n>>> Running: {script_path}")
    print("-" * 60)
    
    # Set UTF-8 encoding for Windows
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True,
            env=env,
            encoding='utf-8'
        )
        
        # Print stdout if any
        if result.stdout:
            print(result.stdout)
            
        print(f"✓ {script_path} completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: {script_path} failed with exit code {e.returncode}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: Failed to run {script_path}: {str(e)}")
        return False

def verify_output_files():
    """Check if expected output files exist."""
    required_files = [
        "output/trap_lines.csv",
        "output/optimal_goblin_slate.csv",
        "data/wnba_clean_props_for_betting.csv",
        "data/wnba_gamelogs_with_cycle_phases.csv",  # Added
        "output/cycle_phase_summary.csv"  # Added
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ Found: {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            all_exist = False
            
    return all_exist

def main():
    """Run the complete WNBA prediction pipeline."""
    # Define scripts in execution order
    scripts = [
        "scripts/scraping/fetch_and_parse_prizepicks.py",
        "scripts/mapping/map_prizepicks_names.py", 
        "scripts/prediction/run_prop_predictions.py",
        "scripts/intelligence/menstrual_phase_estimator.py",  # ADDED: Menstrual Intelligence Layer
        "scripts/prediction/verify_trap_props.py",
        "scripts/prediction/aggressive_trap_detector.py",
        "scripts/prediction/prepare_clean_props.py",
        "scripts/prediction/updated_betting_strategy.py"
    ]
    
    print("🏀 WNBA Daily Prediction Pipeline")
    print("=" * 60)
    print("🧠 NOW WITH MENSTRUAL INTELLIGENCE LAYER")
    print("=" * 60)
    
    # Run each script in order
    for script in scripts:
        if not run_script(script):
            print(f"\n❌ Pipeline failed at: {script}")
            print("Exiting...")
            sys.exit(1)
    
    # Verify output files
    print("\n" + "=" * 60)
    print("Verifying output files...")
    print("-" * 60)
    
    if verify_output_files():
        print("\n" + "=" * 60)
        print("✅ Daily pipeline complete.")
        print("- Clean props: data/wnba_clean_props_for_betting.csv") 
        print("- Goblin slate: output/optimal_goblin_slate.csv")
        print("- Traps detected: output/trap_lines.csv")
        print("- Cycle intelligence: data/wnba_gamelogs_with_cycle_phases.csv")
        print("- Phase summary: output/cycle_phase_summary.csv")
        print("\n🎯 TARS: Cycle-aware predictions ready for deployment!")
    else:
        print("\n⚠️ Pipeline completed but some output files are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()

# Sample console output:
# 🏀 WNBA Daily Prediction Pipeline
# ============================================================
# 🧠 NOW WITH MENSTRUAL INTELLIGENCE LAYER
# ============================================================
#
# >>> Running: scripts/prediction/fetch_and_parse_prizepicks.py
# ------------------------------------------------------------
# Fetching PrizePicks data...
# ✓ scripts/prediction/fetch_and_parse_prizepicks.py completed successfully
#
# >>> Running: scripts/intelligence/menstrual_phase_estimator.py
# ------------------------------------------------------------
# 🧠 TARS: Initializing Menstrual Intelligence Layer...
# ✓ scripts/intelligence/menstrual_phase_estimator.py completed successfully
    print("Verifying output files...")
    print("-" * 60)
    
    if verify_output_files():
        print("\n" + "=" * 60)
        print("✅ Daily pipeline complete.")
        print("- Clean props: data/wnba_clean_props_for_betting.csv")
        print("- Goblin slate: output/optimal_goblin_slate.csv")
        print("- Traps detected: output/trap_lines.csv")
    else:
        print("\n⚠️  Pipeline completed but some output files are missing.")
        sys.exit(1)


if __name__ == "__main__":
    main()


# Sample console output:
# 🏀 WNBA Daily Prediction Pipeline
# ============================================================
# 
# >>> Running: scripts/prediction/fetch_and_parse_prizepicks.py
# ------------------------------------------------------------
# Fetching PrizePicks data...
# ✓ scripts/prediction/fetch_and_parse_prizepicks.py completed successfully