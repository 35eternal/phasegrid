import asyncio
from playwright.async_api import async_playwright

URL = "https://app.prizepicks.com/"
OUTPUT_HTML = "data/debug_projection_cards.html"

async def run():
    print("🧪 Launching Playwright for raw HTML card dump...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL)
        await page.wait_for_timeout(6000)

        for _ in range(12):
            await page.mouse.wheel(0, 5000)
            await page.wait_for_timeout(1000)

        cards = await page.locator("div[data-testid='ProjectionCard']").all()
        print(f"🧩 Found {len(cards)} raw projection cards.")

        html_dump = ""
        for card in cards:
            html = await card.inner_html()
            wrapper = f"<div data-testid='ProjectionCard'>\n{html}\n</div>\n\n"
            html_dump += wrapper

        with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
            f.write(html_dump)

        await browser.close()
        print(f"📁 Dumped raw card HTML to: {OUTPUT_HTML}")

if __name__ == "__main__":
    asyncio.run(run())
