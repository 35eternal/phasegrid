import asyncio
import json
import os
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime

DATA_DIR = "data"
NETWORK_LOGS_DIR = os.path.join(DATA_DIR, "network_logs")
os.makedirs(NETWORK_LOGS_DIR, exist_ok=True)

PRIZEPICKS_URL = "https://app.prizepicks.com/"

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def fetch_graphql_responses():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        graphql_responses = []

        page.on("response", lambda res: graphql_responses.append(res) if "api.prizepicks.com/graphql" in res.url else None)

        print("🌐 Navigating to PrizePicks WNBA page...")
        await page.goto(PRIZEPICKS_URL)
        await page.wait_for_timeout(10000)  # wait 10s to allow GraphQL calls to load

        print(f"📥 Captured {len(graphql_responses)} GraphQL responses.")
        all_data = []

        for i, res in enumerate(graphql_responses):
            try:
                body = await res.json()
                filename = os.path.join(NETWORK_LOGS_DIR, f"graphql_{i:02}.json")
                save_json(body, filename)
                all_data.append(body)
            except Exception:
                continue

        await browser.close()
        return all_data

def parse_projections_from_graphql(all_data):
    props = []
    for entry in all_data:
        try:
            data = entry.get("data", {})
            if "projections" in data:
                for item in data["projections"]["data"]:
                    attributes = item.get("attributes", {})
                    player_name = attributes.get("name", "")
                    stat_type = attributes.get("stat_type", "")
                    line_score = attributes.get("line_score", "")
                    team = attributes.get("team", "")
                    props.append({
                        "Player": player_name,
                        "Stat Type": stat_type,
                        "Line": line_score,
                        "Team": team
                    })
        except Exception:
            continue
    return pd.DataFrame(props)

def main():
    print("📦 Fetching PrizePicks WNBA props (GraphQL)...")
    all_data = asyncio.run(fetch_graphql_responses())

    print("🔍 Searching GraphQL responses for props...")
    df = parse_projections_from_graphql(all_data)

    if not df.empty:
        out_csv = os.path.join(DATA_DIR, "props_prizepicks.csv")
        df.to_csv(out_csv, index=False)
        print(f"✅ Saved props: {out_csv}")
    else:
        print("⚠️ No props found in captured GraphQL responses.")

if __name__ == "__main__":
    main()
