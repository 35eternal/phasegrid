#!/usr/bin/env python3
"""
Generate sample betting card data with actual results for testing the backtest engine
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_sample_betting_card():
    """Generate realistic sample betting card data"""
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Sample players and stats
    players = ['Diana Taurasi', 'Breanna Stewart', 'Alyssa Thomas', 'Napheesa Collier', 
               'Sabrina Ionescu', 'Jewell Loyd', 'Kelsey Plum', 'Arike Ogunbowale']
    
    stat_types = ['points', 'rebounds', 'assists', 'pts+rebs+asts', 'threes']
    
    phases = ['follicular', 'ovulatory', 'luteal', 'menstrual']
    risk_tags = ['high_confidence', 'moderate', 'low_confidence', 'phase_aligned']
    
    # Generate bets
    bets = []
    
    for i in range(50):  # Generate 50 sample bets
        player = np.random.choice(players)
        stat = np.random.choice(stat_types)
        
        # Generate realistic lines based on stat type
        if stat == 'points':
            line = np.random.uniform(12, 28)
            prediction = line + np.random.normal(0, 3)  # Some edge
            actual = line + np.random.normal(0.5, 4)   # Slight positive bias (edge exists)
        elif stat == 'rebounds':
            line = np.random.uniform(4, 12)
            prediction = line + np.random.normal(0, 1.5)
            actual = line + np.random.normal(0.3, 2)
        elif stat == 'assists':
            line = np.random.uniform(3, 8)
            prediction = line + np.random.normal(0, 1)
            actual = line + np.random.normal(0.2, 1.5)
        elif stat == 'pts+rebs+asts':
            line = np.random.uniform(20, 40)
            prediction = line + np.random.normal(0, 3)
            actual = line + np.random.normal(0.4, 4)
        else:  # threes
            line = np.random.uniform(1, 5)
            prediction = line + np.random.normal(0, 0.8)
            actual = line + np.random.normal(0.1, 1)
        
        # Calculate edge and Kelly sizing
        edge = (prediction - line) / line
        implied_prob = 0.5  # Assuming standard -110 odds
        win_prob = 0.5 + edge * 2  # Simple edge to probability conversion
        win_prob = np.clip(win_prob, 0.1, 0.9)
        
        # Kelly fraction calculation
        odds = 0.9  # Decimal odds for -110
        kelly_fraction = (win_prob * (odds + 1) - 1) / odds if win_prob > 0.5 else 0
        kelly_fraction = np.clip(kelly_fraction, 0, 0.25)  # Cap at 25%
        
        # Apply Kelly divisor
        kelly_divisor = np.random.uniform(4, 6)
        kelly_used = kelly_fraction / kelly_divisor
        bet_percentage = kelly_used
        
        # Assign phase and risk tag
        phase = np.random.choice(phases)
        
        # Make certain phases more likely to win
        if phase == 'luteal':
            actual += np.random.normal(0.5, 1)  # Extra edge in luteal phase
            risk_tag = np.random.choice(['high_confidence', 'phase_aligned'], p=[0.3, 0.7])
        elif phase == 'menstrual':
            actual -= np.random.normal(0.2, 1)  # Slightly worse in menstrual
            risk_tag = np.random.choice(['moderate', 'low_confidence'], p=[0.6, 0.4])
        else:
            risk_tag = np.random.choice(risk_tags)
        
        bet = {
            'player_name': player,
            'stat_type': stat,
            'line': round(line, 1),
            'adjusted_prediction': round(prediction, 1),
            'actual_result': round(actual, 1),
            'kelly_fraction': round(kelly_fraction, 4),
            'kelly_used': round(kelly_used, 4),
            'bet_percentage': round(bet_percentage, 4),
            'adv_phase': phase,
            'adv_risk_tag': risk_tag,
            'game_date': (datetime.now() - timedelta(days=50-i)).strftime('%Y-%m-%d')
        }
        
        bets.append(bet)
    
    # Create DataFrame
    df = pd.DataFrame(bets)
    
    # Add some null actual_results to simulate incomplete data
    null_indices = np.random.choice(df.index, size=10, replace=False)
    df.loc[null_indices, 'actual_result'] = np.nan
    
    return df

def main():
    """Generate and save sample data"""
    print("🎲 Generating sample betting card data...")
    
    # Create output directory
    os.makedirs('output', exist_ok=True)
    os.makedirs('config', exist_ok=True)
    
    # Generate betting card
    df = generate_sample_betting_card()
    
    # Save to CSV
    df.to_csv('output/daily_betting_card.csv', index=False)
    print(f"✅ Created output/daily_betting_card.csv with {len(df)} bets")
    print(f"   - {df['actual_result'].notna().sum()} bets have actual results")
    print(f"   - Win rate preview: {(df['actual_result'] > df['line']).sum() / df['actual_result'].notna().sum():.1%}")
    
    # Show sample
    print("\n📊 Sample data:")
    print(df.head())
    
    # Create sample config
    config = {"starting_bankroll": 1000}
    import json
    with open('config/starting_bankroll.json', 'w') as f:
        json.dump(config, f, indent=2)
    print("\n✅ Created config/starting_bankroll.json")
    
    print("\n🚀 Ready to run backtest! Use:")
    print("   python scripts/strategy/backtest_engine.py")

if __name__ == "__main__":
    main()