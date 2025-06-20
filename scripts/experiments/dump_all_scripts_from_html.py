from bs4 import BeautifulSoup
from pathlib import Path

def dump_all_scripts():
    html_path = Path("data/raw_html_prizepicks.html")
    output_dir = Path("data/html_scripts")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not html_path.exists():
        print("❌ HTML file not found.")
        return

    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    scripts = soup.find_all("script")
    print(f"📦 Found {len(scripts)} <script> tags. Saving...")

    count = 0
    for i, script in enumerate(scripts):
        content = script.string
        if content:
            filename = output_dir / f"script_{i:02}.txt"
            with open(filename, "w", encoding="utf-8") as f_out:
                f_out.write(content)
            count += 1

    print(f"✅ Saved {count} scripts to {output_dir}/")

if __name__ == "__main__":
    dump_all_scripts()
