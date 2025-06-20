import json

with open("debug/raw_prizepicks_response.json", "r", encoding="utf-8") as f:
    data = json.load(f)

included = data.get("included", [])

keywords = ["WNBA", "Las Vegas", "Liberty", "Fever", "Lynx", "Sky", "Dream", "Mystics", "Sun", "Mercury", "Sparks", "Storm", "Wings", "Aces"]

print("🔍 Searching for potential WNBA names...\n")

found_any = False
for item in included:
    name = item.get("attributes", {}).get("name")
    if name:
        for keyword in keywords:
            if keyword.lower() in name.lower():
                print(" -", name)
                found_any = True
                break

if not found_any:
    print("❌ No matching WNBA-related names found.")
