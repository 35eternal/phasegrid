# check_players.py - fixed version that handles missing names

import requests

headers = {
    "User-Agent": "Mozilla/5.0"
}
url = "https://api.prizepicks.com/projections?league_id=7&per_page=500"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    try:
        data = response.json()
        included = data.get("included", [])

        # Collect names, skip None
        all_names = sorted({
            item["attributes"].get("name")
            for item in included
            if "attributes" in item and item["attributes"].get("name") is not None
        })

        if all_names:
            print(f"📋 Found {len(all_names)} total entries in 'included':")
            for name in all_names:
                print(" -", name)
        else:
            print("❌ No names found in included.")
    except Exception as e:
        print("❌ Error parsing PrizePicks response:", str(e))
else:
    print("❌ Failed to fetch data. Status code:", response.status_code)
