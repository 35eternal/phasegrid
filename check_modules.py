import sys
print("🔍 Checking system modules...")

modules_to_check = [
    'slips_generator',
    'odds_provider.prizepicks',
    'models',
    'phasegrid'
]

for module in modules_to_check:
    try:
        exec(f"import {module}")
        print(f"✅ {module}")
    except ImportError as e:
        print(f"❌ {module}: {e}")
        
# Check for data files
import os
data_files = ['live_odds.csv', 'props.json', 'slips.json']
print("\n📁 Checking data files:")
for file in data_files:
    if os.path.exists(file):
        size = os.path.getsize(file)
        print(f"✅ {file} ({size} bytes)")
    else:
        print(f"❌ {file} not found")
