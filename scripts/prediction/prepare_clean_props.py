#!/usr/bin/env python3
"""
Prepare clean props for betting by filtering out detected traps.
Creates a final dataset of props that are safe to bet.
"""

import pandas as pd
import os

# Configuration
TRAP_FILE = "data/wnba_aggressive_trap_detection.csv"
OUTPUT_CLEAN = "data/wnba_clean_props_for_betting.csv"
OUTPUT_SUMMARY = "output/betting_recommendation_summary.txt"

# Thresholds
SAFE_PROBABILITY_THRESHOLD = 0.3  # Props with trap probability < 30% are considered safe
MAX_DIFF_THRESHOLD = 3.0  # Props within ±3 points of prediction are preferred

def categorize_betting_recommendation(row):
    """
    Categorize each prop with a betting recommendation.
    """
    trap_prob = row['trap_probability']
    line_diff = row['line_diff']
    trap_type = row['trap_type']
    
    # High confidence traps - AVOID
    if trap_prob >= 0.5:
        if trap_type == 'DEMON':
            return 'AVOID_OVER', 'High probability DEMON trap'
        elif trap_type == 'GOBLIN':
            return 'AVOID_UNDER', 'High probability GOBLIN trap'
    
    # Moderate confidence traps - CAUTION
    elif trap_prob >= 0.3:
        if trap_type == 'DEMON':
            return 'CAUTION_OVER', 'Moderate DEMON risk'
        elif trap_type == 'GOBLIN':
            return 'CAUTION_UNDER', 'Moderate GOBLIN risk'
    
    # Clean props - SAFE to bet
    else:
        if abs(line_diff) <= 1.0:
            return 'EXCELLENT', 'Line closely matches prediction'
        elif abs(line_diff) <= MAX_DIFF_THRESHOLD:
            return 'GOOD', 'Line reasonably close to prediction'
        else:
            return 'FAIR', 'Large difference but low trap probability'

def main():
    # Load trap detection results
    print("Loading trap detection results...")
    df = pd.read_csv(TRAP_FILE)
    
    # Add betting recommendations
    df['recommendation'], df['reason'] = zip(*df.apply(categorize_betting_recommendation, axis=1))
    
    # Filter out Fantasy Score props (since predictions are 0)
    df_filtered = df[df['stat_type'] != 'Fantasy Score'].copy()
    
    # Separate into categories
    avoid_props = df_filtered[df_filtered['recommendation'].str.contains('AVOID')]
    caution_props = df_filtered[df_filtered['recommendation'].str.contains('CAUTION')]
    clean_props = df_filtered[df_filtered['recommendation'].isin(['EXCELLENT', 'GOOD', 'FAIR'])]
    
    # Further categorize clean props
    excellent_props = clean_props[clean_props['recommendation'] == 'EXCELLENT']
    good_props = clean_props[clean_props['recommendation'] == 'GOOD']
    fair_props = clean_props[clean_props['recommendation'] == 'FAIR']
    
    # Save clean props for betting
    clean_props_sorted = clean_props.sort_values(['recommendation', 'abs_diff'])
    clean_props_sorted.to_csv(OUTPUT_CLEAN, index=False)
    print(f"[OK] Saved {len(clean_props_sorted)} clean props to {OUTPUT_CLEAN}")
    
    # Create summary report
    with open(OUTPUT_SUMMARY, 'w', encoding='utf-8') as f:
        f.write("WNBA PROP BETTING RECOMMENDATIONS SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Total props analyzed: {len(df_filtered)}\n")
        f.write(f"Props to AVOID: {len(avoid_props)} ({len(avoid_props)/len(df_filtered)*100:.1f}%)\n")
        f.write(f"Props requiring CAUTION: {len(caution_props)} ({len(caution_props)/len(df_filtered)*100:.1f}%)\n")
        f.write(f"CLEAN props for betting: {len(clean_props)} ({len(clean_props)/len(df_filtered)*100:.1f}%)\n\n")
        
        f.write("CLEAN PROPS BREAKDOWN:\n")
        f.write(f"  - EXCELLENT (±1 point): {len(excellent_props)}\n")
        f.write(f"  - GOOD (±3 points): {len(good_props)}\n")
        f.write(f"  - FAIR (larger diff but safe): {len(fair_props)}\n\n")
        
        # Top recommendations
        f.write("TOP 20 BETTING RECOMMENDATIONS (EXCELLENT props):\n")
        f.write("-" * 50 + "\n")
        for _, prop in excellent_props.head(20).iterrows():
            f.write(f"{prop['player_name']} - {prop['stat_type']}: {prop['line']} ")
            f.write(f"(predicted: {prop['predicted_value']:.1f}, diff: {prop['line_diff']:+.1f})\n")
        
        # Specific warnings
        f.write("\n\nSPECIFIC PLAYER WARNINGS:\n")
        f.write("-" * 50 + "\n")
        
        watch_players = ['Caitlin Clark', 'Aliyah Boston', 'Marina Mabrey', 'Kelsey Mitchell']
        for player in watch_players:
            player_props = df_filtered[df_filtered['player_name'].str.contains(player, na=False)]
            if len(player_props) > 0:
                f.write(f"\n{player}:\n")
                for _, prop in player_props.iterrows():
                    if prop['recommendation'] in ['EXCELLENT', 'GOOD']:
                        marker = "[OK]"
                    elif 'CAUTION' in prop['recommendation']:
                        marker = "[WARN]"
                    else:
                        marker = "[AVOID]"
                    f.write(f"  {marker} {prop['stat_type']}: {prop['line']} - {prop['recommendation']} ({prop['reason']})\n")
    
    print(f"[OK] Saved betting summary to {OUTPUT_SUMMARY}")
    
    # Print console summary
    print("\n" + "=" * 60)
    print("BETTING RECOMMENDATIONS SUMMARY")
    print("=" * 60)
    print(f"\nTOTAL PROPS: {len(df_filtered)}")
    print(f"[X] AVOID: {len(avoid_props)} props ({len(avoid_props)/len(df_filtered)*100:.1f}%)")
    print(f"[!] CAUTION: {len(caution_props)} props ({len(caution_props)/len(df_filtered)*100:.1f}%)")
    print(f"[OK] CLEAN: {len(clean_props)} props ({len(clean_props)/len(df_filtered)*100:.1f}%)")
    
    print(f"\nCLEAN PROPS QUALITY:")
    print(f"[***] EXCELLENT (line within ±1): {len(excellent_props)} props")
    print(f"[**] GOOD (line within ±3): {len(good_props)} props")
    print(f"[*] FAIR (larger diff but safe): {len(fair_props)} props")
    
    print(f"\nBEST BETS (Top 10 EXCELLENT props):")
    for _, prop in excellent_props.head(10).iterrows():
        print(f"   {prop['player_name']} {prop['stat_type']}: {prop['line']} (pred: {prop['predicted_value']:.1f})")
    
    # Show trap examples
    print(f"\nWORST TRAPS TO AVOID:")
    worst_demons = avoid_props[avoid_props['trap_type'] == 'DEMON'].nlargest(5, 'trap_probability')
    worst_goblins = avoid_props[avoid_props['trap_type'] == 'GOBLIN'].nlargest(5, 'trap_probability')
    
    if len(worst_demons) > 0:
        print("   DEMON TRAPS (Don't bet OVER):")
        for _, trap in worst_demons.iterrows():
            print(f"     [X] {trap['player_name']} {trap['stat_type']}: {trap['line']} vs {trap['predicted_value']:.1f}")
    
    if len(worst_goblins) > 0:
        print("   GOBLIN TRAPS (Don't bet UNDER):")
        for _, trap in worst_goblins.iterrows():
            print(f"     [X] {trap['player_name']} {trap['stat_type']}: {trap['line']} vs {trap['predicted_value']:.1f}")

if __name__ == "__main__":
    main()