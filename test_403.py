import requests

url = "https://app.prizepicks.com/projections/wnba"

# Full Chrome headers
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

print(f"Testing {url} with full headers...")
response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 403:
    print("\n403 Response headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    # Check if it's Cloudflare
    if "CF-Ray" in response.headers:
        print("\nThis is Cloudflare protection!")
        
    # Save the 403 page
    with open("403_page.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("\nSaved 403 response to 403_page.html")
