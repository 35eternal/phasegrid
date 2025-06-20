import json
import os

def inspect_json_structure(json_path):
    if not os.path.exists(json_path):
        print(f"❌ File not found: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Failed to decode JSON: {e}")
            return

    print("✅ JSON file loaded successfully.\n")

    # Case 1: JSON is a dictionary
    if isinstance(data, dict):
        print("🔑 Top-level keys:")
        for key in data.keys():
            print(f"   - {key}")

        if "included" in data:
            print("\n🟢 'included' section is present (legacy support).")
        else:
            print("\n⚠️ 'included' section is missing — player names not embedded.")

        if "data" in data:
            print(f"\n🔍 Inspecting first entry in 'data' list:")
            first_entry = data["data"][0]
            for k, v in first_entry.items():
                val_preview = v if isinstance(v, (str, int, float)) else str(type(v))
                print(f"   {k}: {val_preview}")

            if "relationships" in first_entry and "new_player" in first_entry["relationships"]:
                player_obj = first_entry["relationships"]["new_player"]
                print("\n🧠 Found 'relationships.new_player':")
                for k, v in player_obj.items():
                    print(f"   - {k}: {v}")
            else:
                print("\n⚠️ No 'relationships.new_player' mapping found.")
        else:
            print("❌ 'data' section missing. Cannot inspect props.")

    # Case 2: JSON is a list
    elif isinstance(data, list):
        print("📋 JSON is a list with", len(data), "entries.\n")
        print("🔍 Previewing first entry:")
        first_entry = data[0]
        for k, v in first_entry.items():
            val_preview = v if isinstance(v, (str, int, float)) else str(type(v))
            print(f"   {k}: {val_preview}")
    else:
        print("❌ Unexpected JSON structure: Top-level object is neither a dict nor a list.")

if __name__ == "__main__":
    inspect_json_structure("data/wnba_prizepicks_props.json")
