import pandas as pd

print("🔍 Inspecting wnba_prizepicks_props.csv...")
props_df = pd.read_csv("../data/wnba_prizepicks_props.csv")
print("📄 Props Columns:", props_df.columns.tolist())

print("\n🔍 Inspecting player_directory.csv...")
players_df = pd.read_csv("../data/player_directory.csv")
print("📄 Player Directory Columns:", players_df.columns.tolist())
