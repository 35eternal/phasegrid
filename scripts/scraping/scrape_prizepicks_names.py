import time
import csv
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

URL = "https://app.prizepicks.com/"
INPUT_CSV = "data/prizepicks_player_ids.csv"
OUTPUT_CSV = "data/prizepicks_player_map.csv"

def scroll_and_collect(driver):
    SCROLL_PAUSE_TIME = 1.5
    last_height = driver.execute_script("return document.body.scrollHeight")

    for _ in range(10):  # Up to 10 scrolls
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    print("✅ Finished scrolling. Extracting data...")

    script = """
    const cards = document.querySelectorAll("div[data-testid='ProjectionCard']");
    const result = [];
    cards.forEach(card => {
        const id = card.getAttribute("data-id");
        const nameEl = card.querySelector("p[data-testid='player-name']");
        if (id && nameEl) {
            result.push({ id: id.trim(), name: nameEl.textContent.trim() });
        }
    });
    return result;
    """
    return driver.execute_script(script)

def scrape_names():
    print("🚀 Launching headless browser...")
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)

    print("🌐 Navigating to PrizePicks WNBA board...")
    driver.get(URL)
    time.sleep(5)  # Wait for initial page load and JS

    raw_data = scroll_and_collect(driver)
    driver.quit()

    # Load known player_ids
    target_ids = set()
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            target_ids.add(row["player_id"])

    player_map = {}
    for item in raw_data:
        if item["id"] in target_ids:
            player_map[item["id"]] = item["name"]

    print(f"✅ Mapped {len(player_map)} / {len(target_ids)} players.")

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["player_id", "player_name"])
        for pid, name in player_map.items():
            writer.writerow([pid, name])

    print(f"📁 Saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    scrape_names()
