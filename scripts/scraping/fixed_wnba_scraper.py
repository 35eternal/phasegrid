#!/usr/bin/env python3
"""
Fixed WNBA PrizePicks Scraper - Properly clicks WNBA tab
"""

import asyncio
import json
import csv
from datetime import datetime
from pathlib import Path
import logging

from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def scrape_prizepicks():
    """Scrape WNBA props from PrizePicks"""
    
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser (visible for debugging)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            # Navigate to PrizePicks
            logger.info("Navigating to PrizePicks...")
            await page.goto("https://app.prizepicks.com/", timeout=60000)
            
            # Wait for page to load
            await page.wait_for_timeout(5000)
            
            # Handle any popups
            try:
                close_btns = page.locator('button[aria-label="Close"], button:has-text("Close"), [data-testid="close-button"]')
                if await close_btns.count() > 0:
                    await close_btns.first.click()
                    logger.info("Closed popup")
                    await page.wait_for_timeout(1000)
            except:
                pass
            
            # CRITICAL: Click on WNBA tab
            logger.info("Looking for WNBA tab...")
            
            # Based on the screenshot, the sports are in a row with icons and text
            # WNBA is the 4th item in the row
            wnba_selectors = [
                # Text-based selectors
                'button:has-text("WNBA")',
                'div:has-text("WNBA"):not(:has(*))',  # Leaf node with WNBA text
                '[role="button"]:has-text("WNBA")',
                
                # Position-based (WNBA is 4th in the sports row)
                '.css-1k33q06:nth-child(4)',  # If using emotion CSS
                'nav button:nth-child(4)',
                'nav > div:nth-child(4)',
                
                # Attribute-based
                '[data-sport="WNBA"]',
                '[aria-label="WNBA"]',
                
                # Image/icon based (if it has an icon)
                'img[alt="WNBA"]',
                'svg[title="WNBA"]',
                
                # Generic but specific to sports nav
                'nav :has-text("WNBA")',
                'header :has-text("WNBA")'
            ]
            
            clicked = False
            for selector in wnba_selectors:
                try:
                    elements = page.locator(selector)
                    count = await elements.count()
                    
                    if count > 0:
                        # Find the clickable one
                        for i in range(count):
                            elem = elements.nth(i)
                            if await elem.is_visible():
                                # Take screenshot before clicking
                                await page.screenshot(path=str(data_dir / "before_wnba_click.png"))
                                
                                await elem.click()
                                clicked = True
                                logger.info(f"Clicked WNBA using selector: {selector}")
                                
                                # Wait for navigation/content change
                                await page.wait_for_timeout(3000)
                                
                                # Take screenshot after clicking
                                await page.screenshot(path=str(data_dir / "after_wnba_click.png"))
                                break
                        
                        if clicked:
                            break
                            
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not clicked:
                logger.warning("Could not click WNBA tab, trying direct navigation...")
                await page.goto("https://app.prizepicks.com/wnba", timeout=30000)
                await page.wait_for_timeout(3000)
            
            # Now extract props
            logger.info("Waiting for props to load...")
            await page.wait_for_timeout(5000)
            
            # Take final screenshot
            await page.screenshot(path=str(data_dir / "wnba_props_page.png"))
            
            # Extract props
            props = []
            
            # Common patterns for prop cards
            card_selectors = [
                'div[class*="ProjectionCard"]',
                'div[class*="projection-card"]',
                'div[class*="stat-card"]',
                '[data-testid*="projection"]',
                'div[class*="player-prop"]',
                '.projection-row',
                'article[class*="card"]'
            ]
            
            for selector in card_selectors:
                cards = await page.locator(selector).all()
                if cards:
                    logger.info(f"Found {len(cards)} potential prop cards with {selector}")
                    
                    for idx, card in enumerate(cards):
                        try:
                            card_text = await card.inner_text()
                            
                            # Log first few cards for debugging
                            if idx < 3:
                                logger.info(f"Card {idx} text: {card_text[:100]}...")
                            
                            lines = [line.strip() for line in card_text.split('\n') if line.strip()]
                            
                            if len(lines) >= 2:
                                prop = {
                                    "player_name": lines[0],
                                    "stat_type": None,
                                    "line": None,
                                    "team_name": "Unknown",
                                    "timestamp": datetime.now().isoformat()
                                }
                                
                                # Find stat type and line
                                for line in lines[1:]:
                                    # Common stat types
                                    stat_types = ['Points', 'Rebounds', 'Assists', 'Pts+Rebs+Asts', 
                                                  'Pts+Rebs', 'Pts+Asts', 'Rebs+Asts', '3-Pointers Made',
                                                  'Blocks', 'Steals', 'Turnovers', 'FG Made']
                                    
                                    for stat in stat_types:
                                        if stat.lower() in line.lower():
                                            prop["stat_type"] = stat
                                            break
                                    
                                    # Extract numbers
                                    import re
                                    numbers = re.findall(r'[\d.]+', line)
                                    if numbers and prop["line"] is None:
                                        prop["line"] = float(numbers[0])
                                
                                if prop["stat_type"] and prop["line"]:
                                    props.append(prop)
                                    
                        except Exception as e:
                            logger.debug(f"Error parsing card {idx}: {e}")
                            continue
                    
                    if props:
                        break
            
            logger.info(f"Extracted {len(props)} valid props")
            
            # Save the page HTML for debugging
            page_content = await page.content()
            with open(data_dir / "wnba_page_content.html", 'w', encoding='utf-8') as f:
                f.write(page_content)
            
            # Save props
            if props:
                # JSON
                json_path = data_dir / "wnba_prizepicks_props.json"
                with open(json_path, 'w') as f:
                    json.dump(props, f, indent=2)
                    
                # CSV
                csv_path = data_dir / "wnba_prizepicks_props.csv"
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=["player_name", "team_name", "stat_type", "line", "timestamp"])
                    writer.writeheader()
                    writer.writerows(props)
                    
                print(f"\n✓ Saved {len(props)} WNBA props!")
                print(f"  JSON: {json_path}")
                print(f"  CSV: {csv_path}")
                
                # Show sample
                print("\nSample props:")
                for prop in props[:3]:
                    print(f"  {prop['player_name']} - {prop['stat_type']}: {prop['line']}")
            else:
                print("\n⚠ No WNBA props found.")
                print("Check these files for debugging:")
                print("  - data/before_wnba_click.png")
                print("  - data/after_wnba_click.png")
                print("  - data/wnba_props_page.png")
                print("  - data/wnba_page_content.html")
                
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            await page.screenshot(path=str(data_dir / "error_screenshot.png"))
            
        finally:
            input("\nPress Enter to close browser...")  # Keep browser open for inspection
            await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape_prizepicks())