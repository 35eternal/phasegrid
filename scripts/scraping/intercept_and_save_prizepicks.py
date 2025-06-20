import asyncio
import json
import os
from playwright.async_api import async_playwright

async def run():
    print("🌐 Navigating to PrizePicks board page...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        captured_data = {}

        async def handle_route(route, request):
            if "projections" in request.url and "league_id=3" in request.url:
                print("📡 Intercepted WNBA projections request!")
                response = await route.fetch()
                try:
                    data = await response.json()
                    captured_data["json"] = data
                    print("✅ Successfully captured data.")
                except:
                    print("❌ Failed to parse intercepted response.")
                await route.continue_()
            else:
                await route.continue_()

        await context.route("**/*", handle_route)

        await page.goto("https://app.prizepicks.com/")
        print("⏳ Please scroll or interact briefly if necessary...")
        await page.wait_for_timeout(12000)  # wait for full load and interception

        await browser.close()

        if "json" in captured_data:
            os.makedirs("data", exist_ok=True)
            with open("data/wnba_prizepicks_props.json", "w", encoding="utf-8") as f:
                json.dump(captured_data["json"], f, indent=2)
            print("💾 Saved intercepted data to data/wnba_prizepicks_props.json")
        else:
            print("⚠️ No PrizePicks WNBA data was captured.")

if __name__ == "__main__":
    asyncio.run(run())
