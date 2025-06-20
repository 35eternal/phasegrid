#!/usr/bin/env python3
"""
Aggressive trap detection for WNBA props.
Uses multiple detection methods to catch ALL potential DEMON and GOBLIN props.
"""

import pandas as pd
import numpy as np
import os

# Configuration
INPUT_FILE = "data/wnba_prop_predictions.csv"
OUTPUT_FILE = "data/wnba_aggressive_trap_detection.csv"
OUTPUT_SUMMARY = "output/trap_detection_summary.csv"

# Aggressive thresholds
DEMON_DIFF_THRESHOLD = 4.0  # Line 4+ points above predicted
GOBLIN_DIFF_THRESHOLD = -3.0  # Line 3+ points below predicted
EXTREME_DEMON_THRESHOLD = 7.0
EXTREME_GOBLIN_THRESHOLD = -5.0

def calculate_trap_probability(line, predicted, stat_type):
    """
    Calculate probability of a prop being a trap based on multiple factors.
    """
    diff = line - predicted
    abs_diff = abs(diff)
    
    # Base probability from difference
    if diff >= EXTREME_DEMON_THRESHOLD:
        base_prob = 0.9
        trap_type = "DEMON"
    elif diff >= DEMON_DIFF_THRESHOLD:
        base_prob = 0.5 + (diff - DEMON_DIFF_THRESHOLD) * 0.1
        trap_type = "DEMON"
    elif diff <= EXTREME_GOBLIN_THRESHOLD:
        base_prob = 0.9
        trap_type = "GOBLIN"
    elif diff <= GOBLIN_DIFF_THRESHOLD:
        base_prob = 0.5 + (abs(diff) - abs(GOBLIN_DIFF_THRESHOLD)) * 0.1
        trap_type = "GOBLIN"
    else:
        base_prob = 0.1
        trap_type = "NORMAL"
    
    # Adjust for stat volatility
    volatile_stats = ['3-Pointers Made', 'Steals', 'Blocks', 'Turnovers']
    if stat_type in volatile_stats and abs_diff >= 2:
        base_prob = min(1.0, base_prob * 1.3)
    
    # Extreme cases get maximum probability
    if abs_diff >= 8:
        base_prob = 0.95
    
    return trap_type, min(1.0, base_prob)

def analyze_line_setter_intent(line, predicted, player_name):
    """
    Analyze potential sportsbook intent based on line setting patterns.
    """
    diff = line - predicted
    intent = ""
    
    # Round number bias
    if line % 5 == 0 and abs(diff) >= 3:
        intent += "ROUND_NUMBER_TRAP "
    
    # Psychological barriers
    psychological_barriers = [10, 15, 20, 25, 30]
    if any(abs(line - barrier) < 0.5 for barrier in psychological_barriers) and abs(diff) >= 3:
        intent += "PSYCHOLOGICAL_BARRIER "
    
    # Star player bias
    star_players = ['Caitlin Clark', 'A\'ja Wilson', 'Breanna Stewart', 'Arike Ogunbowale']
    if any(star in player_name for star in star_players) and abs(diff) >= 4:
        intent += "STAR_PLAYER_TRAP "
    
    return intent.strip()

def main():
    # Read input data
    df = pd.read_csv(INPUT_FILE)
    
    # Initialize detection columns
    df['line_diff'] = df['line'] - df['predicted_value']
    df['abs_diff'] = df['line_diff'].abs()
    df['trap_type'] = 'NORMAL'
    df['trap_probability'] = 0.0
    df['detection_method'] = ''
    df['line_intent'] = ''
    df['action_required'] = 'NONE'
    
    # Process each prop
    for idx, row in df.iterrows():
        # Calculate trap probability
        trap_type, trap_prob = calculate_trap_probability(
            row['line'], 
            row['predicted_value'], 
            row['stat_type']
        )
        
        df.at[idx, 'trap_type'] = trap_type
        df.at[idx, 'trap_probability'] = trap_prob
        
        # Analyze line setter intent
        intent = analyze_line_setter_intent(
            row['line'],
            row['predicted_value'],
            row['player_name']
        )
        df.at[idx, 'line_intent'] = intent
        
        # Determine detection method
        methods = []
        
        # Method 1: Extreme difference
        if row['line_diff'] >= EXTREME_DEMON_THRESHOLD:
            methods.append('EXTREME_DEMON_DIFF')
        elif row['line_diff'] <= EXTREME_GOBLIN_THRESHOLD:
            methods.append('EXTREME_GOBLIN_DIFF')
        
        # Method 2: Moderate difference
        elif row['line_diff'] >= DEMON_DIFF_THRESHOLD:
            methods.append('MODERATE_DEMON_DIFF')
        elif row['line_diff'] <= GOBLIN_DIFF_THRESHOLD:
            methods.append('MODERATE_GOBLIN_DIFF')
        
        # Method 3: Intent-based
        if intent:
            methods.append('INTENT_BASED')
        
        # Method 4: High-confidence trap probability
        if trap_prob >= 0.7:
            methods.append('HIGH_PROBABILITY')
        
        df.at[idx, 'detection_method'] = ', '.join(methods)
        
        # Determine action
        if trap_type == 'DEMON' and trap_prob >= 0.5:
            df.at[idx, 'action_required'] = 'AVOID_OVER'
        elif trap_type == 'GOBLIN' and trap_prob >= 0.5:
            df.at[idx, 'action_required'] = 'AVOID_UNDER'
        elif trap_prob >= 0.7:
            df.at[idx, 'action_required'] = 'INVESTIGATE'
    
    # Sort by trap probability for better visibility
    df = df.sort_values(['trap_probability', 'abs_diff'], ascending=[False, False])
    
    # Save full results
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✓ Saved full analysis to {OUTPUT_FILE}")
    
    # Create summary of high-risk props
    high_risk = df[df['trap_probability'] >= 0.5].copy()
    
    if len(high_risk) > 0:
        # Group summary by trap type
        summary_data = []
        
        for trap_type in ['DEMON', 'GOBLIN']:
            type_props = high_risk[high_risk['trap_type'] == trap_type]
            if len(type_props) > 0:
                summary_data.append({
                    'trap_type': trap_type,
                    'count': len(type_props),
                    'avg_diff': type_props['line_diff'].mean(),
                    'max_diff': type_props['line_diff'].max() if trap_type == 'DEMON' else type_props['line_diff'].min(),
                    'avg_probability': type_props['trap_probability'].mean()
                })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(OUTPUT_SUMMARY, index=False)
        print(f"✓ Saved trap summary to {OUTPUT_SUMMARY}")
    
    # Print results
    print(f"\n🎯 TRAP DETECTION RESULTS:")
    print(f"Total props analyzed: {len(df)}")
    print(f"\n⚠️  HIGH-RISK PROPS (probability ≥ 0.5): {len(high_risk)}")
    
    demons = df[df['trap_type'] == 'DEMON']
    goblins = df[df['trap_type'] == 'GOBLIN']
    
    print(f"\n👹 DEMON PROPS: {len(demons)}")
    print(f"   - Extreme (diff ≥ {EXTREME_DEMON_THRESHOLD}): {len(demons[demons['line_diff'] >= EXTREME_DEMON_THRESHOLD])}")
    print(f"   - Moderate (diff ≥ {DEMON_DIFF_THRESHOLD}): {len(demons[demons['line_diff'] >= DEMON_DIFF_THRESHOLD])}")
    
    print(f"\n👺 GOBLIN PROPS: {len(goblins)}")
    print(f"   - Extreme (diff ≤ {EXTREME_GOBLIN_THRESHOLD}): {len(goblins[goblins['line_diff'] <= EXTREME_GOBLIN_THRESHOLD])}")
    print(f"   - Moderate (diff ≤ {GOBLIN_DIFF_THRESHOLD}): {len(goblins[goblins['line_diff'] <= GOBLIN_DIFF_THRESHOLD])}")
    
    # Show top traps
    print(f"\n🚨 TOP 10 MOST LIKELY TRAPS:")
    top_traps = df.nlargest(10, 'trap_probability')[['player_name', 'stat_type', 'line', 'predicted_value', 'line_diff', 'trap_type', 'trap_probability']]
    for _, trap in top_traps.iterrows():
        icon = "👹" if trap['trap_type'] == 'DEMON' else "👺"
        print(f"   {icon} {trap['player_name']} {trap['stat_type']}: {trap['line']} (pred: {trap['predicted_value']:.1f}, diff: {trap['line_diff']:+.1f}) - {trap['trap_probability']:.0%} confidence")
    
    # Check for specific players
    print(f"\n🔍 SPECIFIC PLAYER CHECK:")
    watch_list = ['Aliyah Boston', 'Kelsey Mitchell', 'Marina Mabrey', 'Caitlin Clark']
    for player in watch_list:
        player_props = df[df['player_name'].str.contains(player, na=False)]
        if len(player_props) > 0:
            print(f"\n   {player}:")
            for _, prop in player_props.iterrows():
                if prop['trap_type'] != 'NORMAL':
                    icon = "👹" if prop['trap_type'] == 'DEMON' else "👺"
                    print(f"     {icon} {prop['stat_type']}: {prop['line']} vs {prop['predicted_value']:.1f} (diff: {prop['line_diff']:+.1f}) - {prop['trap_type']} {prop['trap_probability']:.0%}")

if __name__ == "__main__":
    main()

# Sample output structure:
# player_name,stat_type,line,predicted_value,line_diff,abs_diff,trap_type,trap_probability,detection_method,line_intent,action_required
# Aliyah Boston,Points,9.5,13.9,-4.4,4.4,GOBLIN,0.74,MODERATE_GOBLIN_DIFF,HIGH_PROBABILITY,,AVOID_UNDER
# Marina Mabrey,Points,24.5,15.8,8.7,8.7,DEMON,0.95,EXTREME_DEMON_DIFF,HIGH_PROBABILITY,ROUND_NUMBER_TRAP,AVOID_OVER
# Kelsey Mitchell,Points,14.5,21.3,-6.8,6.8,GOBLIN,0.90,EXTREME_GOBLIN_DIFF,HIGH_PROBABILITY,STAR_PLAYER_TRAP,AVOID_UNDER