#!/usr/bin/env python3
"""Quick setup script to create necessary directories and show project structure."""

import os
from pathlib import Path

def main():
    # Get the project root (parent of this script's directory)
    if Path(__file__).parent.name == "scripts":
        project_root = Path(__file__).parent.parent
    else:
        project_root = Path(__file__).parent
    
    print(f"Project root: {project_root}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Create necessary directories
    directories = [
        "config",
        "scripts", 
        "tests",
        "output"
    ]
    
    print("\nCreating directories...")
    for dir_name in directories:
        dir_path = project_root / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"✓ {dir_name}/ - {'created' if not dir_path.exists() else 'exists'}")
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Place your Google Sheets credentials in: config/gsheets_creds.json")
    print("2. Run: python scripts/repo_audit.py")
    print("3. Run: python scripts/verify_sheets.py")

if __name__ == "__main__":
    main()