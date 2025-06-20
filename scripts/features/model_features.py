import pandas as pd

GAMES_PATH = "data/wnba_2024_gamelogs.csv"
FEATURE_COLS = [
    "MIN", "FGA", "FG_PCT", "FG3A", "FG3_PCT", "FTA", "FT_PCT",
    "OREB", "DREB", "REB", "AST", "TOV", "STL", "BLK", "PFD"
]

def get_model_input_features(player_name):
    df = pd.read_csv(GAMES_PATH)
    player_df = df[df["PLAYER_NAME"].str.lower() == player_name.lower()]
    if player_df.empty:
        print(f"❌ No games found for {player_name}")
        return None

    latest_game = player_df.sort_values("GAME_DATE", ascending=False).iloc[0]
    features = latest_game[FEATURE_COLS].values
    return features
