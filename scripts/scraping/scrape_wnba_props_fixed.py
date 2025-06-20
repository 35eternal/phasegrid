import requests

headers = {
    "User-Agent": "Mozilla/5.0"
}

print("📊 Scraping PrizePicks WNBA props...")

all_props = []

for page in range(1, 5):  # Try first 4 pages
    url = f"https://api.prizepicks.com/projections?league_id=18&per_page=250&page={page}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Page {page}: Failed to fetch - {response.status_code}")
        continue

    data = response.json()
    projections = data.get("data", [])
    included = data.get("included", [])

    if not projections and not included:
        print(f"⚠️ Page {page}: No projections or included items found.")
        continue

    print(f"✅ Page {page}: Found {len(projections)} projections, {len(included)} included items.")

    for item in included:
        if item.get("type") == "new_player":
            name = item.get("attributes", {}).get("name")
            if name:
                all_props.append(name)

if all_props:
    print(f"\n🟢 Total unique WNBA props found: {len(set(all_props))}")
    for name in sorted(set(all_props)):
        print(" -", name)
else:
    print("\n❌ No WNBA props found.")
