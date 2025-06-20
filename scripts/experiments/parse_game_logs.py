import pandas as pd
import os
from bs4 import BeautifulSoup, Comment

# Output folder
output_dir = "data/player_gamelogs"
os.makedirs(output_dir, exist_ok=True)

# Input folder
html_dir = "data/game_logs"
files = [f for f in os.listdir(html_dir) if f.endswith(".html")]

for file in files:
    bbref_id = file.replace(".html", "")
    file_path = os.path.join(html_dir, file)

    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Try direct table first (just in case it exists normally)
    table = soup.find("table", {"id": "pgl_basic"})
    
    if not table:
        # Look through commented-out HTML for the table
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if "id=\"pgl_basic\"" in comment:
                table = BeautifulSoup(comment, "html.parser").find("table", {"id": "pgl_basic"})
                break

    if table:
        try:
            df = pd.read_html(str(table))[0]
            df = df[df["Rk"] != "Rk"]
            df = df.reset_index(drop=True)
            df["BBRefID"] = bbref_id

            output_path = os.path.join(output_dir, f"{bbref_id}_2024.csv")
            df.to_csv(output_path, index=False)
            print(f"✅ Parsed & saved: {output_path}")
        except Exception as e:
            print(f"❌ Parsing error for {bbref_id}: {e}")
    else:
        print(f"⚠️  No game log table found for {bbref_id} – likely hasn't played yet or page is empty.")
