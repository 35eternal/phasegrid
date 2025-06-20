import requests

headers = {
    "User-Agent": "Mozilla/5.0"
}
url = "https://api.prizepicks.com/projections?league_id=7&per_page=500"

print("🔍 Fetching and listing all projections...")

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    included = data.get("included", [])
    projection_entries = [
        item for item in included if item.get("type") == "projection"
    ]

    print(f"🧾 Found {len(projection_entries)} projection entries\n")

    for item in projection_entries:
        attr = item.get("attributes", {})
        player_name = attr.get("name", "N/A")
        stat_type = attr.get("stat_type", "N/A")
        team = attr.get("team", "N/A")
        print(f"- {player_name} | {stat_type} | {team}")

except Exception as e:
    print("❌ Error during fetch:", e)
