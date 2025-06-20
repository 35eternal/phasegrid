import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0"
}

print("📅 Fetching all active slates from PrizePicks...")

try:
    slate_url = "https://api.prizepicks.com/slates"
    response = requests.get(slate_url, headers=headers)
    response.raise_for_status()
    slates = response.json().get("data", [])

    print(f"🧾 Found {len(slates)} total slates.\n")

    for slate in slates:
        attributes = slate.get("attributes", {})
        slug = attributes.get("slug")
        name = attributes.get("name", "Unnamed")
        league = attributes.get("league", "Unknown")
        if "wnba" in slug.lower():
            print(f"🔍 Fetching props from slate: {name} (slug: {slug})")

            props_url = f"https://api.prizepicks.com/projections/slate?slug={slug}"
            props_response = requests.get(props_url, headers=headers)
            props_data = props_response.json()

            included = props_data.get("included", [])
            projection_entries = [i for i in included if i.get("type") == "projection"]

            if projection_entries:
                print(f"✅ Found {len(projection_entries)} props in this slate:\n")
                for entry in projection_entries:
                    attr = entry.get("attributes", {})
                    name = attr.get("name")
                    team = attr.get("team")
                    stat = attr.get("stat_type")
                    line = attr.get("line_score")
                    print(f" - {name} ({team}) — {stat}: {line}")
            else:
                print("⚠️ No props found in this slate.\n")
except Exception as e:
    print("❌ Error while fetching slates or props:", e)
