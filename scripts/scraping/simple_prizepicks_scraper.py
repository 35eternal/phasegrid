#!/usr/bin/env python3
"""
Simplified WNBA PrizePicks Scraper
Handles common page patterns and popups
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
            
            # Wait a bit for initial load
            await page.wait_for_timeout(5000)
            
            # Handle common popups/prompts
            try:
                # Location prompt - click allow if present
                allow_btn = page.locator('button:has-text("Allow")')
                if await allow_btn.count() > 0:
                    await allow_btn.click()
                    logger.info("Clicked Allow for location")
            except:
                pass
                
            try:
                # Close any welcome/promo modals
                close_btns = page.locator('button[aria-label="Close"], button:has-text("Close"), [data-testid="close-button"]')
                if await close_btns.count() > 0:
                    await close_btns.first.click()
                    logger.info("Closed modal")
            except:
                pass
            
            # Navigate to WNBA section
            await page.wait_for_timeout(2000)
            
            # Try multiple ways to get to WNBA
            wnba_clicked = False
            
            # Method 1: Direct URL
            await page.goto("https://app.prizepicks.com/wnba", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Method 2: Click WNBA if not there
            if "wnba" not in page.url.lower():
                selectors = [
                    'button:has-text("WNBA")',
                    'a:has-text("WNBA")',
                    '[data-testid="WNBA"]',
                    'span:has-text("WNBA")'
                ]
                
                for selector in selectors:
                    try:
                        elem = page.locator(selector).first
                        if await elem.count() > 0:
                            await elem.click()
                            wnba_clicked = True
                            logger.info(f"Clicked WNBA using: {selector}")
                            break
                    except:
                        continue
            
            # Wait for props to load
            await page.wait_for_timeout(5000)
            
            # Extract props using multiple strategies
            props = []
            
            # Strategy 1: Look for common card patterns
            card_selectors = [
                'div[class*="projection"]',
                'div[class*="player-prop"]',
                'div[class*="stat-card"]',
                'div[class*="PlayerProp"]',
                '[data-testid*="projection"]',
                '.stat-container > div'
            ]
            
            for selector in card_selectors:
                cards = await page.locator(selector).all()
                if cards:
                    logger.info(f"Found {len(cards)} cards using: {selector}")
                    
                    for card in cards:
                        try:
                            # Get all text from card
                            card_text = await card.inner_text()
                            lines = card_text.strip().split('\n')
                            
                            if len(lines) >= 3:
                                # Common pattern: Player, Stat Type, Line
                                prop = {
                                    "player_name": lines[0].strip(),
                                    "stat_type": lines[1].strip(),
                                    "line": None,
                                    "team_name": "Unknown",
                                    "timestamp": datetime.now().isoformat()
                                }
                                
                                # Extract number from remaining lines
                                for line in lines[2:]:
                                    try:
                                        # Look for numbers
                                        import re
                                        numbers = re.findall(r'[\d.]+', line)
                                        if numbers:
                                            prop["line"] = float(numbers[0])
                                            break
                                    except:
                                        continue
                                
                                if prop["line"] is not None:
                                    props.append(prop)
                                    
                        except Exception as e:
                            logger.warning(f"Error parsing card: {e}")
                            continue
                    
                    if props:
                        break
            
            # Save debug info
            await page.screenshot(path=str(data_dir / "prizepicks_final.png"))
            
            logger.info(f"Extracted {len(props)} props")
            
            # Save data
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
                    
                print(f"\n✓ Saved {len(props)} props to:")
                print(f"  - {json_path}")
                print(f"  - {csv_path}")
            else:
                print("\n⚠ No props found. Check prizepicks_final.png for page state")
                
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            await page.screenshot(path=str(data_dir / "error_screenshot.png"))
            
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape_prizepicks())