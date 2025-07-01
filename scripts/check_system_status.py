#!/usr/bin/env python3
"""PhaseGrid System Status Check"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("🔍 PHASEGRID SYSTEM STATUS CHECK")
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# Check environment variables
print("\n📋 ENVIRONMENT VARIABLES:")
env_vars = [
    'GOOGLE_SHEET_ID', 'SHEET_ID', 'DISCORD_WEBHOOK_URL', 
    'SLACK_WEBHOOK_URL', 'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN'
]
for var in env_vars:
    value = os.getenv(var)
    if value:
        print(f"  ✅ {var}: {'*' * 10} (configured)")
    else:
        print(f"  ❌ {var}: Not configured")

# Check key files
print("\n📁 KEY FILES:")
files_to_check = [
    'credentials.json',
    '.env',
    'scripts/verify_sheets.py',
    'scripts/smoke_alert.py',
    'auto_paper.py'
]
for file in files_to_check:
    if Path(file).exists():
        print(f"  ✅ {file}")
    else:
        print(f"  ❌ {file}")

# Check recent logs
print("\n📊 RECENT ACTIVITY:")
log_dirs = ['logs', 'phase_logs', 'betting_cards']
for log_dir in log_dirs:
    if Path(log_dir).exists():
        files = list(Path(log_dir).glob('**/*'))
        if files:
            most_recent = max(files, key=lambda x: x.stat().st_mtime if x.is_file() else 0)
            if most_recent.is_file():
                mod_time = datetime.fromtimestamp(most_recent.stat().st_mtime)
                print(f"  📁 {log_dir}: Last modified {mod_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            print(f"  📁 {log_dir}: Empty")

print("\n✅ Status check complete!")
