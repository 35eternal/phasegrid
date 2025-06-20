import pandas as pd
import asyncio
import os
from playwright.async_api import async_playwright

# Load player mapping
mapping_df = pd.read_csv("data/player_final_mapping.csv")

# Ensure output folder exists
os.makedirs("data/game_logs", exist_ok=True)

async def fetch_game_log(playwright, bbref_id):
    url = f"https://www.basketball-reference.com/wnba/players/{bbref_id[0]}/{bbref_id}/gamelog/2023/"
    path = f"data/game_logs/{bbref_id}.html"

    try:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        print(f"🌐 Fetching {bbref_id}...")

        await page.goto(url, timeout=15000)
        await page.wait_for_selector("#pgl_basic", timeout=10000)
        content = await page.content()

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Saved game log for {bbref_id}")
        await browser.close()

    except Exception as e:
        print(f"❌ Failed to fetch {bbref_id}: {e}")

async def main():
    async with async_playwright() as p:
        tasks = []

        for _, row in mapping_df.iterrows():
            bbref_id = row["BBRefID"]
            if pd.isna(bbref_id):
                continue
            tasks.append(fetch_game_log(p, bbref_id))

        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
