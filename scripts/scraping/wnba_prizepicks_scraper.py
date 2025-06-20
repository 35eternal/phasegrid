#!/usr/bin/env python3
"""
WNBA PrizePicks Props Scraper
Production-grade headless browser scraper using Playwright
"""

import asyncio
import json
import csv
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional
import logging
from pathlib import Path
import random

from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeout


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('wnba_scraper')


class WNBAPrizePicks:
    """WNBA Props Scraper for PrizePicks.com"""
    
    def __init__(self, headless: bool = False):  # Changed to False for debugging
        self.headless = headless
        self.base_url = "https://app.prizepicks.com/wnba"  # Direct WNBA URL
        self.props: List[Dict] = []
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Use absolute path to data directory
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.data_dir.mkdir(exist_ok=True)
        
    async def init_browser(self):
        """Initialize Playwright browser with production settings"""
        try:
            playwright = await async_playwright().start()
            
            # Launch with more realistic settings
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--start-maximized'
                ]
            )
            
            # Create browser context with realistic settings
            context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/Phoenix',
                permissions=['geolocation'],
                geolocation={'latitude': 33.4484, 'longitude': -112.0740}  # Phoenix
            )
            
            # Add stealth scripts
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                window.chrome = {
                    runtime: {}
                };
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({ state: 'granted' })
                    })
                });
            """)
            
            self.page = await context.new_page()
            
            # Don't block any resources - we need everything to load
            
            logger.info("Browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
            
    async def navigate_and_wait(self):
        """Navigate to PrizePicks and wait for content"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Navigating to {self.base_url} (attempt {retry_count + 1})")
                
                # Navigate with extended timeout
                await self.page.goto(self.base_url, wait_until='domcontentloaded', timeout=60000)
                
                # Wait for any of these selectors that indicate props are loaded
                selectors_to_try = [
                    '[data-test="projection-card"]',
                    '.projection-card',
                    '[class*="ProjectionCard"]',
                    '[class*="stat-card"]',
                    '.stat-container',
                    '[data-testid="projection-item"]'
                ]
                
                for selector in selectors_to_try:
                    try:
                        await self.page.wait_for_selector(selector, timeout=10000)
                        logger.info(f"Found props using selector: {selector}")
                        break
                    except:
                        continue
                
                # Additional wait for dynamic content
                await self.page.wait_for_timeout(5000)
                
                # Take screenshot for debugging
                screenshot_path = self.data_dir / "prizepicks_debug.png"
                await self.page.screenshot(path=str(screenshot_path))
                logger.info(f"Screenshot saved to {screenshot_path}")
                
                return
                
            except PlaywrightTimeout:
                retry_count += 1
                logger.warning(f"Timeout on attempt {retry_count}, retrying...")
                
            except Exception as e:
                logger.error(f"Navigation error: {e}")
                retry_count += 1
                
        raise Exception("Failed to load page after maximum retries")
        
    async def extract_props_json_method(self):
        """Try to extract props from JSON in page"""
        try:
            # Look for window.__INITIAL_STATE__ or similar
            props_data = await self.page.evaluate("""
                () => {
                    // Common patterns for stored data
                    if (window.__INITIAL_STATE__) return window.__INITIAL_STATE__;
                    if (window.__NEXT_DATA__) return window.__NEXT_DATA__;
                    if (window.initialData) return window.initialData;
                    if (window.__APP_STATE__) return window.__APP_STATE__;
                    
                    // Try to find in localStorage
                    const stored = localStorage.getItem('projections') || 
                                  localStorage.getItem('props') || 
                                  localStorage.getItem('wnba-props');
                    if (stored) return JSON.parse(stored);
                    
                    return null;
                }
            """)
            
            if props_data:
                logger.info("Found props data in JavaScript")
                # Parse the data structure (this will vary based on PrizePicks' structure)
                # You'll need to inspect the actual structure
                return props_data
                
        except Exception as e:
            logger.warning(f"Could not extract JSON data: {e}")
            
        return None
        
    async def extract_props_dom_method(self):
        """Extract props by parsing DOM elements"""
        try:
            # Get page content for debugging
            content = await self.page.content()
            debug_path = self.data_dir / "prizepicks_page_content.html"
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Page content saved to {debug_path}")
            
            # Try multiple selector strategies
            selectors = {
                'cards': [
                    '[data-test="projection-card"]',
                    '.projection-card',
                    '[class*="ProjectionCard"]',
                    '[class*="stat-card"]',
                    'div[class*="card"][class*="stat"]'
                ],
                'player': [
                    '[data-test="player-name"]',
                    '.player-name',
                    '[class*="PlayerName"]',
                    'span[class*="player"]',
                    'div[class*="player"] span'
                ],
                'stat': [
                    '[data-test="stat-type"]',
                    '.stat-type',
                    '[class*="StatType"]',
                    '[class*="stat-label"]',
                    'span[class*="stat"]'
                ],
                'line': [
                    '[data-test="projection-value"]',
                    '.projection-value',
                    '[class*="Line"]',
                    '[class*="projection-number"]',
                    'span[class*="number"]'
                ],
                'team': [
                    '[data-test="team-name"]',
                    '.team-name',
                    '[class*="TeamName"]',
                    'span[class*="team"]'
                ]
            }
            
            # Find all prop cards
            prop_cards = []
            for card_selector in selectors['cards']:
                cards = await self.page.query_selector_all(card_selector)
                if cards:
                    prop_cards = cards
                    logger.info(f"Found {len(cards)} cards with selector: {card_selector}")
                    break
            
            if not prop_cards:
                logger.warning("No prop cards found with any selector")
                return
            
            # Extract data from each card
            for i, card in enumerate(prop_cards):
                try:
                    prop_data = {}
                    
                    # Try to extract each field with multiple selectors
                    for field, field_selectors in selectors.items():
                        if field == 'cards':
                            continue
                            
                        for selector in field_selectors:
                            elem = await card.query_selector(selector)
                            if elem:
                                text = await elem.inner_text()
                                prop_data[field] = text.strip()
                                break
                    
                    # Only add if we have minimum required data
                    if prop_data.get('player') and prop_data.get('stat'):
                        self.props.append({
                            "player_name": prop_data.get('player', 'Unknown'),
                            "team_name": prop_data.get('team', 'Unknown'),
                            "stat_type": prop_data.get('stat', 'Unknown'),
                            "line": float(prop_data.get('line', '0').replace('O', '').replace('U', '').strip()) if prop_data.get('line') else 0.0,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                except Exception as e:
                    logger.warning(f"Error extracting prop {i}: {e}")
                    continue
                    
            logger.info(f"Extracted {len(self.props)} props using DOM method")
            
        except Exception as e:
            logger.error(f"Error during DOM extraction: {e}")
            
    async def extract_props(self):
        """Extract all WNBA props data"""
        # First try JSON method (faster and more reliable if available)
        json_data = await self.extract_props_json_method()
        if json_data:
            # Parse JSON data into our format
            # This will depend on PrizePicks' actual data structure
            pass
        
        # Fall back to DOM parsing
        await self.extract_props_dom_method()
        
    async def save_data(self):
        """Save props to JSON and CSV files"""
        if not self.props:
            logger.warning("No props to save")
            return
            
        # Save JSON
        json_path = self.data_dir / "wnba_prizepicks_props.json"
        with open(json_path, 'w') as f:
            json.dump(self.props, f, indent=2)
        logger.info(f"Saved {len(self.props)} props to {json_path}")
        
        # Save CSV
        csv_path = self.data_dir / "wnba_prizepicks_props.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["player_name", "team_name", "stat_type", "line", "timestamp"])
            writer.writeheader()
            writer.writerows(self.props)
        logger.info(f"Saved {len(self.props)} props to {csv_path}")
        
        # Log summary
        if self.props:
            last_player = self.props[-1]['player_name']
            print(f"\n✓ Scraped {len(self.props)} WNBA props")
            print(f"✓ Last player: {last_player}")
            
    async def close(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")
            
    async def scrape(self):
        """Main scraping workflow"""
        try:
            await self.init_browser()
            await self.navigate_and_wait()
            await self.extract_props()
            await self.save_data()
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise
            
        finally:
            await self.close()


async def main():
    """Entry point"""
    # Start with headless=False to see what's happening
    scraper = WNBAPrizePicks(headless=False)
    
    try:
        await scraper.scrape()
        return 0
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    # Run async main
    sys.exit(asyncio.run(main()))