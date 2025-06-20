# capture_network_debug.py

import asyncio
import json
import os
from playwright.async_api import async_playwright

OUTPUT_DIR = "data/network_logs"

async def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser to solve CAPTCHA
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Navigating to PrizePicks...")
        responses = []

        page.on("response", lambda response: responses.append(response))

        await page.goto("https://app.prizepicks.com/projections?league=wnba", timeout=60000)
        await page.wait_for_timeout(15000)  # Give it time to load props after solving CAPTCHA

        print("🧠 Saving full rendered HTML...")
        html = await page.content()
        with open("data/raw_html_prizepicks.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Saved full HTML to data/raw_html_prizepicks.html")

        print(f"📥 Captured {len(responses)} responses. Saving...")
        for idx, response in enumerate(responses):
            try:
                if "application/json" in response.headers.get("content-type", ""):
                    json_data = await response.json()
                    with open(os.path.join(OUTPUT_DIR, f"debug_{idx:03}.json"), "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=2)
            except Exception:
                continue

        print("✅ All responses saved to data/network_logs/")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
