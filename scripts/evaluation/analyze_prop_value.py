import pandas as pd

# Load merged file
df = pd.read_csv("data/merged_props_with_gamelogs.csv")

# Rename columns for consistency
df = df.rename(columns={
    'Stat Type': 'stat_type',
    'Line': 'line_score'
})

# Remove rows missing required data
df = df.dropna(subset=['stat_type', 'line_score', 'PTS', 'AST', 'TRB'])

# Clean stat_type values
df['stat_type'] = df['stat_type'].str.lower()

# Map stat_type to gamelog stat columns
stat_map = {
    'points': 'PTS',
    'assists': 'AST',
    'rebounds': 'TRB',
    'pra': ['PTS', 'AST', 'TRB']
}

# Calculate rolling average for each stat
results = []

for _, row in df.iterrows():
    stat = row['stat_type']
    player = row['Player Name']
    bbref_id = row['BBRefID']
    line = row['line_score']
    
    # Filter for that player
    player_rows = df[(df['BBRefID'] == bbref_id)]

    # Sort by date for rolling window
    player_rows = player_rows.sort_values('Date')

    # Determine which stat(s) to use
    if stat not in stat_map:
        continue

    if stat == 'pra':
        player_rows['stat_avg'] = player_rows[['PTS', 'AST', 'TRB']].sum(axis=1).rolling(window=5).mean()
        latest_stat = player_rows[['PTS', 'AST', 'TRB']].iloc[-1].sum()
    else:
        stat_col = stat_map[stat]
        player_rows['stat_avg'] = player_rows[stat_col].rolling(window=5).mean()
        latest_stat = player_rows[stat_col].iloc[-1]

    stat_avg = player_rows['stat_avg'].iloc[-1]

    # Compare to line
    edge = stat_avg - line
    results.append({
        'Player': player,
        'Stat': stat,
        'Line': line,
        '5-Game Avg': round(stat_avg, 2),
        'Last Game': latest_stat,
        'Edge': round(edge, 2)
    })

# Convert to DataFrame
results_df = pd.DataFrame(results)

# Sort by edge
results_df = results_df.sort_values(by='Edge', ascending=False)

# Display
print("\n📈 Top Edges (Based on 5-game Avg - Line):\n")
print(results_df.to_string(index=False))
