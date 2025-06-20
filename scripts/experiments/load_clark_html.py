import os

HTML = """
<!-- START OF EMBEDDED RAW HTML -->
<!-- I’m about to paste the entire HTML of Caitlin Clark’s 2024 game log here -->

<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Caitlin Clark 2024 Game Log</title></head>
<body>
    <table class="stats_table" id="pgl_basic">
        <thead>
            <tr>
                <th>Rk</th><th>Date</th><th>Opponent</th><th>PTS</th>
            </tr>
        </thead>
        <tbody>
            <tr><td>1</td><td>May 14</td><td>Connecticut</td><td>20</td></tr>
            <tr><td>2</td><td>May 16</td><td>New York</td><td>9</td></tr>
            <tr><td>3</td><td>May 18</td><td>New York</td><td>22</td></tr>
            <tr><td>4</td><td>May 20</td><td>Connecticut</td><td>17</td></tr>
            <tr><td>5</td><td>May 22</td><td>Seattle</td><td>11</td></tr>
            <tr><td>6</td><td>May 25</td><td>Los Angeles</td><td>11</td></tr>
            <tr><td>7</td><td>May 28</td><td>Los Angeles</td><td>30</td></tr>
        </tbody>
    </table>
</body>
</html>

<!-- END OF EMBEDDED RAW HTML -->
"""

def save_clark_html():
    os.makedirs("data/html_cache", exist_ok=True)
    path = "data/html_cache/clarkca02w_2024.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(HTML.strip())
    print(f"✅ Embedded HTML saved to {path}")

if __name__ == "__main__":
    save_clark_html()
