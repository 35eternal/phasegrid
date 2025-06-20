import asyncio
import csv
from playwright.async_api import async_playwright

INPUT_CSV = "data/prizepicks_player_ids.csv"
OUTPUT_CSV = "data/prizepicks_player_map.csv"
URL = "https://app.prizepicks.com/"

async def run():
    print("🚀 Launching full browser — complete human verification + location access...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # full visual
        page = await browser.new_page()
        await page.goto(URL)

        print("⏳ Waiting 90 seconds for you to complete bot check and page load...")
        await page.wait_for_timeout(90000)  # Give you 90 seconds

        # Scroll to load cards
        for _ in range(12):
            await page.mouse.wheel(0, 5000)
            await page.wait_for_timeout(1000)

        print("✅ Finished scrolling. Extracting cards...")

        cards = await page.locator("div[data-testid='ProjectionCard']").all()
        results = {}

        for card in cards:
            try:
                player_id = await card.get_attribute("data-id")
                player_name = await card.locator("h3[data-test='player-name']").text_content()
                if player_id and player_name:
                    results[player_id.strip()] = player_name.strip()
            except Exception:
                continue

        # Load expected player IDs
        with open(INPUT_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            target_ids = [row["player_id"] for row in reader]

        matched = {pid: results[pid] for pid in target_ids if pid in results}

        print(f"✅ Mapped {len(matched)} / {len(target_ids)} players.")

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["player_id", "player_name"])
            for pid, name in matched.items():
                writer.writerow([pid, name])

        print(f"📁 Saved to: {OUTPUT_CSV}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
