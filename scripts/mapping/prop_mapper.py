import json
import pandas as pd

def load_props_and_map_players(props_path: str, mapping_path: str) -> pd.DataFrame:
    """
    Loads PrizePicks props JSON and maps each prop to a player using BBRef ID mapping.
    Returns a DataFrame with projection info and BBRef ID attached.
    """
    with open(props_path, "r", encoding="utf-8") as f:
        props_json = json.load(f)

    data = props_json.get("data", [])
    included = props_json.get("included", [])

    # Build mapping from player ID to full player object
    player_id_to_obj = {
        player["id"]: player
        for player in included
        if player["type"] == "new_player"
    }

    df_rows = []

    for projection in data:
        try:
            rel = projection["relationships"]["new_player"]["data"]
            player_id = rel["id"]
            player_obj = player_id_to_obj.get(player_id)

            if not player_obj:
                continue

            attributes = projection["attributes"]
            name = player_obj["attributes"]["name"]
            stat_type = attributes.get("stat_type")
            line_score = attributes.get("line_score")

            df_rows.append({
                "Player Name": name,
                "Stat Type": stat_type,
                "Line": line_score
            })
        except Exception as e:
            print(f"⚠️ Skipped a projection due to error: {e}")

    props_df = pd.DataFrame(df_rows)

    # Load BBRef ID mapping
    mapping_df = pd.read_csv(mapping_path)

    # Merge on player name
    merged_df = pd.merge(props_df, mapping_df, how="left", left_on="Player Name", right_on="name")

    return merged_df
