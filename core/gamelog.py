import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd

def fetch_gamelog(bbref_id: str, season: int = 2024) -> pd.DataFrame:
    url = f"https://www.basketball-reference.com/wnba/players/{bbref_id[0]}/{bbref_id}/gamelog/{season}/"
    print(f"🌐 Fetching page: {url}")
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Failed to fetch page for {bbref_id}: {response.status_code}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, 'html.parser')
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))

    found_table = None
    for comment in comments:
        comment_soup = BeautifulSoup(comment, 'html.parser')
        table = comment_soup.find('table')
        if table and table.get("id", "").startswith("wnba_pgl_basic"):
            found_table = table
            break

    if found_table is None:
        print("❌ No valid WNBA game log table found in HTML comments.")
        return pd.DataFrame()

    df = pd.read_html(str(found_table))[0]
    df.dropna(how="all", inplace=True)
    df.columns = [col if isinstance(col, str) else col[1] for col in df.columns]

    print(f"✅ Successfully scraped {len(df)} rows for {bbref_id}")
    return df

# For testing
if __name__ == "__main__":
    df = fetch_gamelog("clarkca02w")
    print(df.head())
