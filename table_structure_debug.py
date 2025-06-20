#!/usr/bin/env python3
"""
Debug script to examine the exact table structure on Caitlin Clark's page.
"""

import requests
from bs4 import BeautifulSoup
import time

def debug_caitlin_clark_page():
    """Examine Caitlin Clark's Basketball Reference page in detail."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    url = "https://www.basketball-reference.com/wnba/players/c/clarkca02w.html"
    
    print(f"🔍 Examining: {url}\n")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"✅ Status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all tables
        tables = soup.find_all('table')
        print(f"✅ Found {len(tables)} tables on page\n")
        
        for i, table in enumerate(tables):
            print(f"=== TABLE {i} ===")
            
            # Get table ID if it exists
            table_id = table.get('id', 'No ID')
            print(f"ID: {table_id}")
            
            # Get headers
            headers_row = table.find('thead')
            if headers_row:
                headers = [th.text.strip() for th in headers_row.find_all('th')]
                print(f"Headers: {headers}")
            else:
                print("No thead found, checking first tr...")
                first_row = table.find('tr')
                if first_row:
                    headers = [th.text.strip() for th in first_row.find_all(['th', 'td'])]
                    print(f"First row: {headers}")
            
            # Get first few data rows
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')[:3]  # First 3 rows
                print(f"Sample rows ({len(rows)}):")
                for j, row in enumerate(rows):
                    cells = [td.text.strip() for td in row.find_all(['td', 'th'])]
                    if cells:
                        print(f"  Row {j+1}: {cells}")
            else:
                print("No tbody found")
            
            print()  # Empty line between tables
            
            # If this looks like a game log table, examine it more closely
            if table_id and any(keyword in table_id.lower() for keyword in ['pgl', 'gamelog', 'game']):
                print(f"🎯 POTENTIAL GAME LOG TABLE: {table_id}")
                print("Examining in detail...")
                
                # Get all rows
                all_rows = table.find_all('tr')
                print(f"Total rows: {len(all_rows)}")
                
                # Show first 5 data rows
                for k, row in enumerate(all_rows[1:6]):  # Skip header
                    cells = [td.text.strip() for td in row.find_all(['td', 'th'])]
                    print(f"  Data row {k+1}: {cells}")
                
                print()
        
        # Also look for any game-related content
        print("=== SEARCHING FOR GAME-RELATED CONTENT ===")
        
        # Look for elements with game-related text
        game_elements = soup.find_all(string=lambda text: text and any(
            keyword in text.lower() for keyword in ['2024', 'game', 'pts', 'reb', 'ast']
        ))
        
        print(f"Found {len(game_elements)} elements with game-related text")
        
        # Show some examples
        for elem in game_elements[:5]:
            if len(elem.strip()) > 3:
                print(f"  Game content: '{elem.strip()}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_caitlin_clark_page()