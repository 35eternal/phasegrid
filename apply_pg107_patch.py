# File: apply_pg107_patch.py
# This script applies the PG-107 enhanced HTML fallback patch

import re

# Read the current prizepicks.py
with open('odds_provider/prizepicks.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the fetch_html_fallback method
pattern = r'(def fetch_html_fallback\(self.*?\n(?:.*?\n)*?)(.*?(?=\n    def|\n\nclass|\Z))'

# Enhanced fetch_html_fallback implementation
new_method = '''def fetch_html_fallback(self, league: str = "NBA") -> List[Dict[str, Any]]:
        """
        Enhanced fallback method that uses the discovered API endpoint
        
        Args:
            league: Sport league (NBA, NFL, etc.)
            
        Returns:
            List of scraped projections
        """
        logger.warning(f"Using enhanced HTML fallback for {league} projections")
        
        # Get league ID
        league_id = self.LEAGUE_IDS.get(league.upper())
        if not league_id:
            logger.error(f"Unknown league: {league}")
            return []
        
        # Use the partner API endpoint directly (discovered during HTML analysis)
        api_url = f"https://partner-api.prizepicks.com/projections?league_id={league_id}"
        
        try:
            self._rate_limit()
            
            # Use same headers as main API
            headers = dict(self.session.headers)
            headers.update({
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://app.prizepicks.com",
                "Referer": "https://app.prizepicks.com/"
            })
            
            response = self.session.get(api_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Use the existing parse_projections_to_slips method
                slips = self.parse_projections_to_slips(data)
                
                if slips:
                    logger.info(f"Enhanced HTML fallback fetched {len(slips)} projections")
                    return slips
                else:
                    logger.warning("API returned empty projections")
                    
            elif response.status_code == 403:
                logger.warning("Got 403 from API endpoint - Cloudflare protection active")
            else:
                logger.warning(f"API endpoint returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Enhanced HTML fallback failed: {e}")
        
        # If enhanced method fails, return empty list
        # (We could keep the original BeautifulSoup code here as additional fallback)
        logger.info("All HTML fallback methods exhausted, returning empty list")
        return []'''

# Replace the method
def replace_method(match):
    return new_method

# Apply the replacement
new_content = re.sub(pattern, replace_method, content, flags=re.MULTILINE | re.DOTALL)

# Write the updated file
with open('odds_provider/prizepicks.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ PG-107 patch applied successfully!")
print("✅ Enhanced HTML fallback now uses the discovered API endpoint")
