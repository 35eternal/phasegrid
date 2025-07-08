import json
import os

print("Current directory:", os.getcwd())
print("File exists:", os.path.exists("data/test_cycle_data.json"))

try:
    with open("data/test_cycle_data.json", "rb") as f:
        raw_bytes = f.read(10)
        print("First 10 bytes:", [hex(b) for b in raw_bytes])
    
    with open("data/test_cycle_data.json", "r", encoding="utf-8") as f:
        content = f.read()
        print("File length:", len(content))
        print("First 50 chars:", repr(content[:50]))
        
    data = json.loads(content)
    print("JSON parsed successfully!")
    print("Number of fixtures:", len(data["test_fixtures"]))
        
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
