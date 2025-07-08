import requests
from bs4 import BeautifulSoup

url = "https://app.prizepicks.com/projections/wnba"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Save the full HTML
with open('wnba_page_full.html', 'w', encoding='utf-8') as f:
    f.write(response.text)

print(f"Status: {response.status_code}")
print(f"Page length: {len(response.text)} characters")

# Check page title
title = soup.find('title')
if title:
    print(f"Title: {title.get_text()}")

# Look for common React/Vue app indicators
if 'id="root"' in response.text or 'id="app"' in response.text:
    print("This is a client-side rendered app (React/Vue)")
    
# Look for any text mentioning no games/props
text_content = soup.get_text()
if 'no games' in text_content.lower() or 'no props' in text_content.lower():
    print("Page mentions 'no games' or 'no props'")
    
# Check for redirects or meta tags
meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
if meta_refresh:
    print(f"Meta refresh found: {meta_refresh.get('content')}")

# Look for API endpoints in scripts
for script in soup.find_all('script'):
    if script.string and 'api.prizepicks.com' in script.string:
        print("Found API reference in script")
        # Extract a snippet around the API reference
        idx = script.string.find('api.prizepicks.com')
        snippet = script.string[max(0, idx-50):idx+100]
        print(f"Snippet: ...{snippet}...")

print("\nFirst 500 chars of body text:")
print(text_content[:500])
