"""
PG-111: Fixed Admin Interface - Super Simple Version
"""
import os
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Create our app
app = FastAPI(title="PhaseGrid Admin")

# Set up templates - use absolute path
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Data files
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "uuid_mappings.json"


def load_players():
    """Load players from JSON"""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_players(players):
    """Save players to JSON"""
    with open(DATA_FILE, 'w') as f:
        json.dump(players, f, indent=2)


def normalize_name(name):
    """Normalize player name"""
    import re
    clean = re.sub(r'[^\w\s]', '', name.lower())
    return ' '.join(clean.split())


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main page"""
    players = load_players()
    player_list = []
    
    for norm_name, data in players.items():
        player_list.append({
            'uuid': data['uuid'],
            'name': data.get('original_name', norm_name),
            'normalized': norm_name,
            'created': data.get('created_at', 'Unknown')
        })
    
    # Create a simple HTML response if templates don't work
    if not (BASE_DIR / "templates" / "index.html").exists():
        html_content = f"""
        <html>
        <head>
            <title>PhaseGrid Admin</title>
            <style>
                body {{ font-family: Arial; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background: #4CAF50; color: white; }}
                .button {{ background: #4CAF50; color: white; padding: 10px; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>🏀 PhaseGrid Player Manager</h1>
            <p>Total Players: {len(player_list)}</p>
            <a href="/add" class="button">➕ Add New Player</a>
            <h2>Players</h2>
            <table>
                <tr>
                    <th>Name</th>
                    <th>UUID</th>
                    <th>Created</th>
                </tr>
        """
        
        for player in player_list:
            html_content += f"""
                <tr>
                    <td>{player['name']}</td>
                    <td>{player['uuid'][:8]}...</td>
                    <td>{player['created'][:10] if player['created'] != 'Unknown' else 'Unknown'}</td>
                </tr>
            """
        
        html_content += """
            </table>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    # Use template if it exists
    return templates.TemplateResponse("index.html", {
        "request": request,
        "players": player_list,
        "player_count": len(player_list)
    })


@app.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    """Add player form"""
    html_content = """
    <html>
    <head>
        <title>Add Player - PhaseGrid</title>
        <style>
            body { font-family: Arial; margin: 20px; }
            input { padding: 10px; margin: 10px 0; width: 300px; }
            .button { background: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>➕ Add New Player</h1>
        <form method="post" action="/add">
            <label>Player Name:</label><br>
            <input type="text" name="name" required placeholder="e.g., A'ja Wilson"><br>
            <button type="submit" class="button">Add Player</button>
            <a href="/" style="margin-left: 10px;">Cancel</a>
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/add")
async def add_player(name: str = Form(...)):
    """Add a new player"""
    players = load_players()
    norm_name = normalize_name(name)
    
    if norm_name not in players:
        players[norm_name] = {
            'uuid': str(uuid4()),
            'original_name': name,
            'created_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat()
        }
        save_players(players)
    
    return RedirectResponse(url="/", status_code=302)


@app.get("/test")
async def test():
    """Test endpoint"""
    return {"status": "working", "message": "PhaseGrid Admin is running!"}


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("🚀 Starting PhaseGrid Admin Interface!")
    print("📍 Visit: http://localhost:8000")
    print("📍 Test: http://localhost:8000/test")
    print("Press CTRL+C to stop")
    print("="*50 + "\n")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)