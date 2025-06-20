"""
Sample script to generate live_odds.csv for testing the Dynamic Odds Injector
"""

import pandas as pd
import numpy as np

def generate_sample_live_odds():
    """Generate realistic sample odds data from various sportsbooks"""
    
    # Sample odds data reflecting real-world variations
    odds_data = {
        'player_name': [
            'A. Wilson', 'A. Wilson', 'B. Stewart', 'C. Clark', 
            'D. Ionescu', 'E. Delle Donne', 'K. Plum', 'S. Diggins-Smith',
            'N. Howard', 'A. Thomas', 'J. Loyd', 'C. Gray'
        ],
        'stat_type': [
            'points', 'rebounds', 'rebounds', 'fantasy_score',
            'assists', 'points', 'points', 'assists',
            'rebounds', 'points', 'three_pointers', 'steals'
        ],
        'sportsbook': [
            'PrizePicks', 'FanDuel', 'PrizePicks', 'DraftKings',
            'PrizePicks', 'FanDuel', 'PrizePicks', 'BetMGM',
            'PrizePicks', 'FanDuel', 'PrizePicks', 'PrizePicks'
        ],
        'actual_odds': [
            0.87,  # Slightly worse than standard -110
            0.91,  # Standard -110
            0.95,  # Better than standard
            0.98,  # Near EV-neutral for fantasy
            0.88,  # Standard prop
            0.90,  # Standard -110
            0.85,  # Juiced line
            0.92,  # Slightly better than standard
            0.89,  # Standard range
            0.91,  # Standard -110
            0.86,  # Three-pointer props often juiced
            0.93   # Steals sometimes better odds
        ],
        'line': [
            20.5, 9.5, 8.5, 35.5,
            6.5, 18.5, 24.5, 4.5,
            7.5, 16.5, 2.5, 1.5
        ],
        'timestamp': pd.Timestamp.now()
    }
    
    df = pd.DataFrame(odds_data)
    
    # Add some calculated fields for realism
    df['implied_probability'] = 1 / (1 + df['actual_odds'])
    df['american_odds'] = df['actual_odds'].apply(lambda x: 
        -100 / x if x < 1 else (x - 1) * 100
    ).round().astype(int)
    
    # Save to CSV
    df.to_csv('live_odds.csv', index=False)
    print("Generated live_odds.csv with sample data")
    print("\nSample entries:")
    print(df[['player_name', 'stat_type', 'actual_odds', 'american_odds']].head(8))
    
    return df

def demonstrate_odds_variations():
    """Show how different sportsbooks price the same props"""
    
    print("\n" + "="*60)
    print("Common WNBA Prop Bet Odds Variations")
    print("="*60)
    
    variations = {
        'Market Type': ['Points O/U', 'Rebounds O/U', 'Assists O/U', 
                       'Fantasy Score', '3-Pointers', 'Double-Double'],
        'Standard Odds': [0.90, 0.90, 0.90, 0.98, 0.87, 0.83],
        'Player-Friendly': [0.95, 0.93, 0.92, 1.00, 0.90, 0.87],
        'Sportsbook-Friendly': [0.83, 0.85, 0.87, 0.95, 0.83, 0.77],
        'Notes': [
            'Most liquid market',
            'Moderate variance',
            'High variance',
            'Usually near EV-neutral',
            'Often heavily juiced',
            'High juice on parlays'
        ]
    }
    
    odds_df = pd.DataFrame(variations)
    print(odds_df.to_string(index=False))
    
    print("\n" + "="*60)
    print("Decimal to American Odds Conversion Reference")
    print("="*60)
    
    conversions = [
        (0.77, -130), (0.83, -120), (0.87, -115),
        (0.90, -111), (0.91, -110), (0.95, -105),
        (1.00, +100), (1.10, +110), (1.20, +120)
    ]
    
    for decimal, american in conversions:
        print(f"Decimal: {decimal:.2f} → American: {american:+d}")

if __name__ == "__main__":
    # Generate sample live odds file
    generate_sample_live_odds()
    
    # Show odds variations
    demonstrate_odds_variations()
    
    print("\n✅ Sample live_odds.csv created successfully!")
    print("📁 Use this file to test the Dynamic Odds Injector module")