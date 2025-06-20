import json

with open("data/wnba_prizepicks_props.json", "r") as f:
    data = json.load(f)

print("\n🔍 Player Names from 'included':\n")

if "included" in data:
    for item in data["included"]:
        if item["type"] == "new_player":
            player_id = item.get("id", "N/A")
            name = item.get("attributes", {}).get("name", "Unknown")
            print(f"🧍 {name} (ID: {player_id})")
else:
    print("❌ 'included' section not found.")
