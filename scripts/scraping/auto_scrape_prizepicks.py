import asyncio
import json
import os
from playwright.async_api import async_playwright

async def run():
    print("🌐 Launching browser and opening PrizePicks site...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Step 1: Go to PrizePicks board page
        await page.goto("https://app.prizepicks.com/")
        print("⏳ Waiting for your session to fully load...")

        await page.wait_for_timeout(7000)

        # Step 2: Extract headers and cookies
        print("🍪 Collecting session headers and cookies...")
        cookies = await context.cookies()
        headers = {
            "User-Agent": await page.evaluate("() => navigator.userAgent"),
            "Referer": "https://app.prizepicks.com/",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        headers["Cookie"] = cookie_header

        # Step 3: Use context's APIRequest to fetch data
        print("📡 Sending real API request with browser headers...")

        response = await context.request.get(
            "https://api.prizepicks.com/projections?league_id=3&per_page=250&single_stat=true&in_game=true&state_code=NM&game_mode=pickem",
            headers=headers
        )

        if response.status != 200:
            print(f"❌ Failed to fetch data: HTTP {response.status}")
            await browser.close()
            return

        data = await response.json()

        # Step 4: Save data
        os.makedirs("data", exist_ok=True)
        with open("data/wnba_prizepicks_props.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print("✅ WNBA PrizePicks props saved to data/wnba_prizepicks_props.json")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
