import requests
import json
import re

def find_api_endpoints():
    """Find API endpoints from PrizePicks HTML/JS"""
    url = "https://app.prizepicks.com/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://app.prizepicks.com/"
    }
    
    print("Fetching main page...")
    response = requests.get(url, headers=headers)
    
    # Look for JavaScript files
    js_files = re.findall(r'src="([^"]+\.js[^"]*)"', response.text)
    print(f"\nFound {len(js_files)} JS files:")
    for js in js_files[:5]:  # Show first 5
        print(f"  - {js}")
    
    # Look for API calls in inline scripts
    api_patterns = [
        r'fetch\(["\']([^"\']+)["\']',
        r'axios\.[get|post|put]+\(["\']([^"\']+)["\']',
        r'["\']https://[^"\']*api[^"\']*["\']',
        r'endpoint["\']?\s*[:=]\s*["\']([^"\']+)["\']'
    ]
    
    print("\nSearching for API endpoints...")
    for pattern in api_patterns:
        matches = re.findall(pattern, response.text, re.IGNORECASE)
        if matches:
            print(f"\nPattern '{pattern}' found:")
            for match in matches[:3]:  # Show first 3
                print(f"  - {match}")
    
    # Check if there's a config object
    config_match = re.search(r'window\.config\s*=\s*({[^}]+})', response.text)
    if config_match:
        print("\nFound window.config:")
        print(config_match.group(1))

if __name__ == "__main__":
    find_api_endpoints()
