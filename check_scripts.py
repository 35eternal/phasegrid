import os
from pathlib import Path

# Check what's in scripts/prediction directory
prediction_dir = Path("scripts/prediction")

print("Checking for scripts in:", prediction_dir.absolute())
print("-" * 60)

if prediction_dir.exists():
    scripts = sorted([f for f in prediction_dir.iterdir() if f.suffix == '.py'])
    print(f"Found {len(scripts)} Python scripts:")
    for script in scripts:
        print(f"  - {script.name}")
else:
    print("❌ Directory 'scripts/prediction' not found!")
    
print("\n" + "-" * 60)
print("Directory structure:")
for item in Path(".").iterdir():
    if item.is_dir() and not item.name.startswith('.'):
        print(f"📁 {item.name}/")
        if item.name == "scripts":
            for subitem in item.iterdir():
                if subitem.is_dir():
                    print(f"   📁 {subitem.name}/")
                    for file in subitem.iterdir():
                        if file.suffix == '.py':
                            print(f"      📄 {file.name}")