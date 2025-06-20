#!/usr/bin/env python3
"""
Automated WNBA Predictor Project Reorganizer
This script will safely reorganize your entire project structure
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
import hashlib

class ProjectReorganizer:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.report = []
        
    def log(self, message):
        """Log actions taken"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        self.report.append(f"{datetime.now()}: {message}")
    
    def create_backup(self):
        """Create full backup before making changes"""
        self.log("Creating backup...")
        
        # List of items to backup (excluding venv)
        items_to_backup = []
        for item in self.project_root.iterdir():
            if item.name not in ['venv', '.git', '__pycache__', 'backup_*']:
                items_to_backup.append(item)
        
        if items_to_backup:
            self.backup_dir.mkdir(exist_ok=True)
            for item in items_to_backup:
                if item.is_file():
                    shutil.copy2(item, self.backup_dir / item.name)
                elif item.is_dir():
                    shutil.copytree(item, self.backup_dir / item.name)
            self.log(f"Backup created at: {self.backup_dir}")
        
    def create_new_structure(self):
        """Create the new folder structure"""
        self.log("Creating new folder structure...")
        
        folders = [
            "core",
            "models/trained",
            "data/raw",
            "data/processed",
            "data/mappings",
            "data/archive/2023",
            "data/archive/2024",
            "output/daily",
            "output/reports",
            "dev/debug",
            "dev/experiments",
            "dev/notebooks"
        ]
        
        for folder in folders:
            (self.project_root / folder).mkdir(parents=True, exist_ok=True)
            self.log(f"Created: {folder}/")
    
    def identify_core_scripts(self):
        """Identify the best version of each core script"""
        script_mappings = {
            # Best scraper scripts
            "core/scraper.py": [
                "scripts/scrape_prizepicks_wnba_props.py",
                "scripts/auto_scrape_prizepicks.py",
                "scrape_prizepicks.py"
            ],
            
            # Best mapper scripts
            "core/mapper.py": [
                "scripts/auto_player_mapper.py",
                "scripts/auto_map_players.py",
                "scripts/build_final_player_map.py"
            ],
            
            # Best gamelog scripts
            "core/gamelog.py": [
                "scripts/gamelog_scraper.py",
                "scripts/fetch_wnba_gamelogs.py",
                "fetch_all_gamelogs.py"
            ],
            
            # Best analyzer scripts
            "core/analyzer.py": [
                "scripts/analyze_prop_value.py",
                "scripts/evaluate_props.py",
                "analyze_gamelog.py"
            ],
            
            # Feature engineering
            "models/features.py": [
                "scripts/feature_engineering.py",
                "scripts/features.py",
                "scripts/model_features.py"
            ],
            
            # Utils
            "core/utils.py": [
                "scripts/utils.py"
            ]
        }
        
        return script_mappings
    
    def consolidate_scripts(self, script_mappings):
        """Move and consolidate the best scripts"""
        self.log("Consolidating core scripts...")
        
        for target, sources in script_mappings.items():
            copied = False
            for source in sources:
                source_path = self.project_root / source
                if source_path.exists():
                    target_path = self.project_root / target
                    shutil.copy2(source_path, target_path)
                    self.log(f"Copied {source} → {target}")
                    copied = True
                    break
            
            if not copied:
                self.log(f"WARNING: No source found for {target}")
    
    def organize_data_files(self):
        """Organize data files into proper structure"""
        self.log("Organizing data files...")
        
        data_mappings = {
            # Current data files
            "data/mappings/player_final_mapping.csv": "data/player_final_mapping.csv",
            "data/raw/wnba_prizepicks_props.json": "data/wnba_prizepicks_props.json",
            "data/processed/merged_props_with_gamelogs.csv": "data/merged_props_with_gamelogs.csv",
            
            # Archive old data
            "data/archive/2024/": [
                "data/*_2024.csv",
                "data/player_gamelogs_2024/",
                "data/cleaned_gamelogs_2024.csv",
                "data/engineered_gamelogs_2024.csv"
            ],
            
            "data/archive/2023/": [
                "data/player_gamelogs/*_2023.csv"
            ]
        }
        
        # Move current files
        for target, source in data_mappings.items():
            if isinstance(source, str):
                source_path = self.project_root / source
                if source_path.exists():
                    target_path = self.project_root / target
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source_path), str(target_path))
                    self.log(f"Moved {source} → {target}")
            elif isinstance(source, list):
                # Handle patterns and folders
                for pattern in source:
                    for source_path in self.project_root.glob(pattern):
                        if source_path.exists():
                            target_path = self.project_root / target / source_path.name
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(source_path), str(target_path))
                            self.log(f"Archived {source_path.name} → {target}")
    
    def move_debug_files(self):
        """Move debug and experimental files"""
        self.log("Moving debug files...")
        
        # Move debug scripts
        for script in self.project_root.glob("*debug*.py"):
            target = self.project_root / "dev/debug" / script.name
            shutil.move(str(script), str(target))
            self.log(f"Moved {script.name} → dev/debug/")
        
        # Move test scripts
        for script in self.project_root.glob("test_*.py"):
            target = self.project_root / "dev/experiments" / script.name
            shutil.move(str(script), str(target))
            self.log(f"Moved {script.name} → dev/experiments/")
        
        # Move network logs and debug data
        if (self.project_root / "data/network_logs").exists():
            shutil.move(
                str(self.project_root / "data/network_logs"),
                str(self.project_root / "dev/debug/network_logs")
            )
            self.log("Moved network_logs → dev/debug/")
    
    def create_init_files(self):
        """Create __init__.py files for packages"""
        self.log("Creating __init__.py files...")
        
        packages = ["core", "models", "dev"]
        for package in packages:
            init_file = self.project_root / package / "__init__.py"
            init_file.write_text('"""Package initialization"""')
            self.log(f"Created {package}/__init__.py")
    
    def create_pipeline_script(self):
        """Create the main pipeline orchestrator"""
        self.log("Creating pipeline.py...")
        
        pipeline_content = '''#!/usr/bin/env python3
"""
WNBA Predictor Pipeline - Main Orchestrator
Runs the complete pipeline from scraping to signal generation
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core import scraper, mapper, gamelog, analyzer
from models import predictor

def run_pipeline():
    """Execute the complete prediction pipeline"""
    
    print(f"\\n{'='*60}")
    print(f"WNBA Predictor Pipeline - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\\n")
    
    try:
        # Step 1: Scrape PrizePicks
        print("[1/5] Fetching PrizePicks props...")
        props_file = scraper.fetch_current_props()
        print(f"✓ Found {len(props_file)} props")
        
        # Step 2: Map players
        print("\\n[2/5] Mapping players to Basketball Reference...")
        mapped_count = mapper.auto_map_new_players()
        print(f"✓ Mapped {mapped_count} new players")
        
        # Step 3: Fetch game logs
        print("\\n[3/5] Fetching player game logs...")
        gamelogs = gamelog.fetch_missing_gamelogs()
        print(f"✓ Updated {len(gamelogs)} player game logs")
        
        # Step 4: Analyze prop values
        print("\\n[4/5] Analyzing prop values...")
        analysis = analyzer.analyze_all_props()
        print(f"✓ Analyzed {len(analysis)} props")
        
        # Step 5: Generate signals
        print("\\n[5/5] Generating betting signals...")
        signals = analyzer.generate_signals(analysis)
        print(f"✓ Generated {len(signals)} betting signals")
        
        # Save daily report
        report_path = f"output/daily/signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        analyzer.save_signals(signals, report_path)
        
        print(f"\\n{'='*60}")
        print(f"✅ Pipeline completed successfully!")
        print(f"📊 Signals saved to: {report_path}")
        print(f"{'='*60}\\n")
        
        return signals
        
    except Exception as e:
        print(f"\\n❌ Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the pipeline
    signals = run_pipeline()
    
    # Display top signals
    if signals:
        print("\\n🎯 TOP BETTING SIGNALS:")
        print("-" * 50)
        for i, signal in enumerate(signals[:5], 1):
            print(f"{i}. {signal['player']} {signal['prop']} {signal['action']}")
            print(f"   Line: {signal['line']} | Edge: {signal['edge']:.1f}")
'''
        
        pipeline_path = self.project_root / "pipeline.py"
        pipeline_path.write_text(pipeline_content)
        self.log("Created pipeline.py")
    
    def create_config_file(self):
        """Create centralized config file"""
        self.log("Creating config.py...")
        
        config_content = '''"""
WNBA Predictor Configuration
Centralized configuration for all components
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
MODELS_DIR = PROJECT_ROOT / "models"

# Data paths
PLAYER_MAPPING_FILE = DATA_DIR / "mappings/player_final_mapping.csv"
PROPS_FILE = DATA_DIR / "raw/wnba_prizepicks_props.json"
GAMELOGS_DIR = DATA_DIR / "processed/gamelogs"

# API Configuration
PRIZEPICKS_API = "https://api.prizepicks.com/projections"
BASKETBALL_REF_BASE = "https://www.basketball-reference.com"

# Model parameters
CONFIDENCE_THRESHOLD = 0.75
MIN_EDGE_THRESHOLD = 5.0
ROLLING_GAME_WINDOWS = [3, 5, 7, 10]

# Scraping parameters
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
REQUEST_DELAY = 1.0  # seconds between requests

# Output settings
SIGNAL_COLUMNS = [
    'timestamp', 'player', 'prop_type', 'line', 'prediction',
    'edge', 'confidence', 'action', 'recent_avg'
]

# Feature engineering
FEATURES = [
    'games_played', 'minutes_avg', 'stat_avg_3g', 'stat_avg_5g',
    'stat_avg_10g', 'stat_std', 'days_rest', 'home_away',
    'opponent_defensive_rating', 'trend_direction'
]
'''
        
        config_path = self.project_root / "config.py"
        config_path.write_text(config_content)
        self.log("Created config.py")
    
    def cleanup_old_files(self):
        """Remove redundant files (with safety checks)"""
        self.log("Cleaning up redundant files...")
        
        # Files to remove (only if they've been backed up)
        redundant_patterns = [
            "parse_*.py",
            "fetch_*.py",
            "build_*.py",
            "debug_*.py",
            "test_*.py",
            "*_debug.py",
            "data/*_debug*",
            "data/html_cache/*",
            "data/network_logs/*"
        ]
        
        removed_count = 0
        for pattern in redundant_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.exists() and file_path.is_file():
                    # Check if file was backed up
                    backup_path = self.backup_dir / file_path.relative_to(self.project_root)
                    if backup_path.exists():
                        file_path.unlink()
                        removed_count += 1
                        self.log(f"Removed: {file_path.name}")
        
        self.log(f"Removed {removed_count} redundant files")
    
    def generate_report(self):
        """Generate reorganization report"""
        report_path = self.project_root / "REORGANIZATION_REPORT.txt"
        
        with open(report_path, 'w') as f:
            f.write("WNBA PREDICTOR PROJECT REORGANIZATION REPORT\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write("="*60 + "\n\n")
            
            f.write("ACTIONS TAKEN:\n")
            f.write("-"*40 + "\n")
            for action in self.report:
                f.write(f"{action}\n")
            
            f.write("\n\nNEW STRUCTURE:\n")
            f.write("-"*40 + "\n")
            f.write("wnba_predictor/\n")
            f.write("├── pipeline.py (NEW - Main orchestrator)\n")
            f.write("├── config.py (NEW - Configuration)\n")
            f.write("├── core/ (Consolidated scripts)\n")
            f.write("├── models/ (ML components)\n")
            f.write("├── data/ (Organized data)\n")
            f.write("├── output/ (Results)\n")
            f.write("└── dev/ (Development files)\n")
            
            f.write(f"\n\nBACKUP LOCATION: {self.backup_dir}\n")
            f.write("\nNEXT STEPS:\n")
            f.write("1. Review the new structure\n")
            f.write("2. Test pipeline.py\n")
            f.write("3. Delete backup after verification\n")
        
        self.log(f"Report saved to: {report_path}")
    
    def run(self, skip_backup=False, skip_cleanup=False):
        """Execute the complete reorganization"""
        print("\n🚀 WNBA PREDICTOR PROJECT REORGANIZER")
        print("="*50)
        
        if not skip_backup:
            self.create_backup()
        
        # Execute reorganization
        self.create_new_structure()
        
        script_mappings = self.identify_core_scripts()
        self.consolidate_scripts(script_mappings)
        
        self.organize_data_files()
        self.move_debug_files()
        
        self.create_init_files()
        self.create_pipeline_script()
        self.create_config_file()
        
        if not skip_cleanup:
            self.cleanup_old_files()
        
        self.generate_report()
        
        print("\n✅ REORGANIZATION COMPLETE!")
        print(f"📁 Backup saved to: {self.backup_dir}")
        print("📄 See REORGANIZATION_REPORT.txt for details")
        print("\n⚡ Run 'python pipeline.py' to test the new structure!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Reorganize WNBA Predictor Project")
    parser.add_argument("--skip-backup", action="store_true", help="Skip backup creation")
    parser.add_argument("--skip-cleanup", action="store_true", help="Skip file cleanup")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        print("\nThis script will:")
        print("1. Create a full backup of your project")
        print("2. Create a new, organized folder structure")
        print("3. Consolidate duplicate scripts")
        print("4. Organize data files")
        print("5. Move debug files to dev folder")
        print("6. Create pipeline.py and config.py")
        print("7. Clean up redundant files")
        print("8. Generate a detailed report")
    else:
        reorganizer = ProjectReorganizer()
        reorganizer.run(
            skip_backup=args.skip_backup,
            skip_cleanup=args.skip_cleanup
        )