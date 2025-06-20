import re
import json
from pathlib import Path
from bs4 import BeautifulSoup

def extract_props_from_html():
    html_path = Path("data/raw_html_prizepicks.html")
    if not html_path.exists():
        print("❌ HTML file not found.")
        return

    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    scripts = soup.find_all("script")

    # Try to find a script with JSON data in it
    props_data = []
    for script in scripts:
        if not script.string:
            continue

        # Look for a block of JSON data
        json_match = re.search(r"\{.*\"league\":\"wnba\".*\}", script.string, re.DOTALL | re.IGNORECASE)
        if json_match:
            try:
                props_json = json.loads(json_match.group())
                props_data.append(props_json)
            except json.JSONDecodeError:
                continue

    if not props_data:
        print("❌ No embedded prop data found in raw HTML.")
        return

    output_path = Path("data/props_from_html.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(props_data, f, indent=2)

    print(f"✅ Found and saved prop data to: {output_path}")

if __name__ == "__main__":
    extract_props_from_html()
