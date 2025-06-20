#!/usr/bin/env python3
"""
Updated PrizePicks betting strategy based on OVER-only demon/goblin system.
GOBLINS = Good bets (easy overs, lower payout)
DEMONS = Bad bets (trap overs, higher payout)
"""

import pandas as pd
import numpy as np

class PrizePicksOptimalStrategy:
    """
    Optimal betting strategy for PrizePicks demon/goblin system.
    """
    
    def __init__(self):
        self.predictions_file = "data/wnba_prop_predictions.csv"
        self.trap_detection_file = "data/wnba_aggressive_trap_detection.csv"
        
    def load_and_analyze(self):
        """Load data and create betting recommendations."""
        # Load trap detection results
        df = pd.read_csv(self.trap_detection_file)
        
        # Reclassify based on new understanding
        df['betting_recommendation'] = 'SKIP'
        df['expected_value'] = 0
        df['confidence'] = 0
        
        for idx, row in df.iterrows():
            line_diff = row['line_diff']
            
            # GOBLINS (line < predicted) = GOOD BETS
            if line_diff <= -3.0:  # Line is 3+ points below prediction
                df.at[idx, 'betting_recommendation'] = 'BET_GOBLIN'
                df.at[idx, 'confidence'] = min(0.9, 0.5 + abs(line_diff) * 0.1)
                # Lower payout but high probability of winning
                df.at[idx, 'expected_value'] = df.at[idx, 'confidence'] * 0.8 - (1 - df.at[idx, 'confidence'])
                
            # DEMONS (line > predicted) = AVOID
            elif line_diff >= 4.0:  # Line is 4+ points above prediction
                df.at[idx, 'betting_recommendation'] = 'AVOID_DEMON'
                df.at[idx, 'confidence'] = max(0.1, 0.5 - line_diff * 0.1)
                # Higher payout but low probability of winning
                df.at[idx, 'expected_value'] = df.at[idx, 'confidence'] * 1.5 - (1 - df.at[idx, 'confidence'])
                
            # STANDARD props (line ≈ predicted) = NEUTRAL
            elif abs(line_diff) <= 2.0:
                df.at[idx, 'betting_recommendation'] = 'STANDARD_PROP'
                df.at[idx, 'confidence'] = 0.5
                df.at[idx, 'expected_value'] = 0
        
        return df
    
    def generate_optimal_slate(self, df, max_picks=5):
        """Generate optimal betting slate focusing on GOBLINs."""
        # Filter for GOBLIN bets only
        goblins = df[df['betting_recommendation'] == 'BET_GOBLIN'].copy()
        
        if len(goblins) == 0:
            print("No GOBLIN opportunities found!")
            return pd.DataFrame()
        
        # Sort by expected value and confidence
        goblins['combined_score'] = goblins['expected_value'] * goblins['confidence']
        goblins = goblins.sort_values('combined_score', ascending=False)
        
        # Diversify by player
        optimal_slate = []
        players_used = set()
        
        for _, prop in goblins.iterrows():
            if prop['player_name'] not in players_used:
                optimal_slate.append(prop)
                players_used.add(prop['player_name'])
                
                if len(optimal_slate) >= max_picks:
                    break
        
        # If we need more picks, add second props from same players
        if len(optimal_slate) < max_picks:
            for _, prop in goblins.iterrows():
                if len(optimal_slate) >= max_picks:
                    break
                if prop['player_name'] in players_used and prop not in optimal_slate:
                    optimal_slate.append(prop)
        
        return pd.DataFrame(optimal_slate)
    
    def print_strategy_report(self, df, optimal_slate):
        """Print comprehensive strategy report."""
        print("=" * 70)
        print("PRIZEPICKS OPTIMAL BETTING STRATEGY REPORT")
        print("=" * 70)
        print("\nKEY INSIGHT: Both demons and goblins are OVER-only bets!")
        print("- GOBLINS (green): Easy overs with lower payouts - THESE ARE GOOD!")
        print("- DEMONS (red): Hard overs with higher payouts - THESE ARE TRAPS!")
        print("=" * 70)
        
        # Count each type
        goblins = df[df['betting_recommendation'] == 'BET_GOBLIN']
        demons = df[df['betting_recommendation'] == 'AVOID_DEMON']
        standard = df[df['betting_recommendation'] == 'STANDARD_PROP']
        
        print(f"\nPROP ANALYSIS:")
        print(f"Total props: {len(df)}")
        print(f"GOBLIN opportunities (BET THESE): {len(goblins)}")
        print(f"DEMON traps (AVOID THESE): {len(demons)}")
        print(f"Standard props: {len(standard)}")
        
        # Show top GOBLINs
        print(f"\nTOP 10 GOBLIN BETS (Easy Overs):")
        print("-" * 70)
        for i, (_, prop) in enumerate(goblins.head(10).iterrows(), 1):
            print(f"{i}. {prop['player_name']} {prop['stat_type']}: {prop['line']}")
            print(f"   Predicted: {prop['predicted_value']:.1f} (line is {abs(prop['line_diff']):.1f} points LOW)")
            print(f"   Confidence: {prop['confidence']:.0%}")
        
        # Show worst DEMONs to avoid
        print(f"\nWORST DEMON TRAPS (Avoid These):")
        print("-" * 70)
        worst_demons = demons.nlargest(5, 'line_diff')
        for _, trap in worst_demons.iterrows():
            print(f"❌ {trap['player_name']} {trap['stat_type']}: {trap['line']}")
            print(f"   Predicted: {trap['predicted_value']:.1f} (line is {trap['line_diff']:.1f} points HIGH)")
        
        # Optimal slate
        if len(optimal_slate) > 0:
            print(f"\n🎯 OPTIMAL {len(optimal_slate)}-PICK SLATE:")
            print("-" * 70)
            total_confidence = 1
            for i, (_, pick) in enumerate(optimal_slate.iterrows(), 1):
                print(f"{i}. {pick['player_name']} OVER {pick['line']} {pick['stat_type']}")
                print(f"   Predicted: {pick['predicted_value']:.1f} (+{abs(pick['line_diff']):.1f})")
                total_confidence *= pick['confidence']
            
            print(f"\nSlate hit probability: {total_confidence:.1%}")
            print(f"Expected payout: Lower than standard (goblin rates)")
            print(f"Risk level: LOW - these are the easy overs!")
        
        # Specific player analysis
        print(f"\nSPECIFIC PLAYER ANALYSIS:")
        print("-" * 70)
        watch_list = ['Caitlin Clark', 'Aliyah Boston', 'Marina Mabrey', 'Kelsey Mitchell']
        
        for player in watch_list:
            player_props = df[df['player_name'].str.contains(player, na=False)]
            if len(player_props) > 0:
                print(f"\n{player}:")
                for _, prop in player_props.iterrows():
                    icon = "✅" if prop['betting_recommendation'] == 'BET_GOBLIN' else "❌" if prop['betting_recommendation'] == 'AVOID_DEMON' else "➖"
                    print(f"  {icon} {prop['stat_type']}: {prop['line']} vs {prop['predicted_value']:.1f} - {prop['betting_recommendation']}")

def main():
    # Create strategy analyzer
    strategy = PrizePicksOptimalStrategy()
    
    # Load and analyze
    df = strategy.load_and_analyze()
    
    # Generate optimal slate
    optimal_slate = strategy.generate_optimal_slate(df, max_picks=5)
    
    # Print report
    strategy.print_strategy_report(df, optimal_slate)
    
    # Save results
    df.to_csv("data/updated_betting_strategy.csv", index=False)
    if len(optimal_slate) > 0:
        optimal_slate.to_csv("output/optimal_goblin_slate.csv", index=False)
        print(f"\n✅ Saved optimal slate to output/optimal_goblin_slate.csv")

if __name__ == "__main__":
    main()