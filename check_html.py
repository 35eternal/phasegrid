import requests
from bs4 import BeautifulSoup

url = "https://app.prizepicks.com/projections/wnba"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print(f"Fetching: {url}")
response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")
print(f"Content length: {len(response.text)}")

if response.status_code == 200:
    # Check if it's a single-page app that needs JavaScript
    if "window.__INITIAL_STATE__" in response.text:
        print("Found __INITIAL_STATE__ - this is a React app")
    
    # Look for any indication of why there's no data
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check for any error messages
    error_divs = soup.find_all('div', class_=['error', 'no-data', 'empty'])
    if error_divs:
        print(f"Found error/empty messages: {[div.get_text() for div in error_divs]}")
    
    # Check page title
    title = soup.find('title')
    if title:
        print(f"Page title: {title.get_text()}")
    
    # Look for script tags
    scripts = soup.find_all('script')
    print(f"Found {len(scripts)} script tags")
    
    # Save the HTML for inspection
    with open('wnba_page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("Saved full HTML to wnba_page.html")
