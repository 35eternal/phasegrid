import pytest
pytest.skip('Temporarily skipping due to missing dependencies', allow_module_level=True)

# Test with lower synthetic line adjustment
import pandas as pd

# Quick test to see synthetic line generation with different adjustments
df = pd.read_csv("data/wnba_combined_gamelogs.csv")
df = df.rename(columns={'GAME_DATE': 'Date', 'PLAYER_NAME': 'Player', 'FG3M': '3PM'})
df['Date'] = pd.to_datetime(df['Date'], format='mixed')

# Filter to July-Sept 2024
start_date = pd.to_datetime("2024-07-01")
end_date = pd.to_datetime("2024-09-01")
df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

print("=== SYNTHETIC LINE COMPARISON ===")

# Sample one player's PTS to compare line generation methods
sample_player = df[df['Player'] == df['Player'].iloc[0]].head(10)
if len(sample_player) > 5:
    recent_avg = sample_player['PTS'].tail(5).mean()
    
    print(f"Player: {sample_player['Player'].iloc[0]}")
    print(f"Recent 5-game PTS average: {recent_avg:.1f}")
    print(f"Current synthetic line (+10%): {(recent_avg * 1.1):.1f}")
    print(f"Reduced synthetic line (+5%): {(recent_avg * 1.05):.1f}")
    print(f"Conservative synthetic line (+2%): {(recent_avg * 1.02):.1f}")
    print(f"Market-neutral line (0%): {recent_avg:.1f}")
    
    print(f"\nActual game results vs different line types:")
    for idx, row in sample_player.tail(3).iterrows():
        actual = row['PTS']
        print(f"  Game: {actual:.0f} pts")
        print(f"    vs +10% line ({(recent_avg * 1.1):.1f}): {'UNDER wins' if actual < (recent_avg * 1.1) else 'OVER wins'}")
        print(f"    vs +5% line ({(recent_avg * 1.05):.1f}): {'UNDER wins' if actual < (recent_avg * 1.05) else 'OVER wins'}")
        print(f"    vs neutral line ({recent_avg:.1f}): {'UNDER wins' if actual < recent_avg else 'OVER wins'}")
        print()

