import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

OUTPUT_CSV = "data/prizepicks_player_map.csv"

def scrape_prizepicks_players():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")

    print("🚀 Launching headless Chrome...")
    driver = webdriver.Chrome(options=options)

    try:
        # Load the board directly
        url = "https://app.prizepicks.com/board"
        driver.get(url)

        print("⏳ Waiting for projection cards to appear...")
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "projection-card"))
            )
            print("✅ Projections loaded.")
        except:
            print("❌ Timed out waiting for props to load.")
            return

        print("🔍 Scraping projection cards...")
        cards = driver.find_elements(By.CLASS_NAME, "projection-card")
        print(f"🔎 Found {len(cards)} total cards.")

        player_map = {}

        for card in cards:
            try:
                name_elem = card.find_element(By.CLASS_NAME, "name")
                player_name = name_elem.text.strip()

                data_id = card.get_attribute("data-id") or card.get_attribute("data-projection-id")

                if player_name and data_id and data_id not in player_map:
                    player_map[data_id] = player_name
            except:
                continue

        print(f"✅ Found {len(player_map)} unique players.")

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["player_id", "player_name"])
            for pid, name in player_map.items():
                writer.writerow([pid, name])

        print(f"📁 Saved to: {OUTPUT_CSV}")

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_prizepicks_players()
