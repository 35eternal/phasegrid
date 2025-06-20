"""
Phase Risk Analysis and Safe Betting Card Generator
Analyzes phase distribution and creates filtered betting cards
"""

import pandas as pd
import numpy as np
from datetime import datetime

def analyze_phase_risk(betting_card_path='output/daily_betting_card_adjusted.csv'):
    """Comprehensive phase risk analysis"""
    
    df = pd.read_csv(betting_card_path)
    
    print('='*60)
    print('PHASE RISK ANALYSIS')
    print('='*60)
    
    # Overall phase statistics
    print('\nBets by Phase:')
    phase_stats = df.groupby('adv_phase').agg({
        'kelly_used': ['count', 'sum', 'mean'],
        'bet_percentage': 'sum'
    }).round(4)
    print(phase_stats)
    
    # Phase exposure analysis
    print('\n' + '-'*40)
    print('PHASE EXPOSURE BREAKDOWN:')
    print('-'*40)
    
    for phase in df['adv_phase'].unique():
        phase_df = df[df['adv_phase'] == phase]
        pct_of_bets = len(phase_df) / len(df) * 100
        total_exposure = phase_df['bet_percentage'].sum()
        
        # Historical win rates
        win_rates = {
            'luteal': 80,
            'follicular': 67,
            'menstrual': 20,
            'ovulation': 50
        }
        
        win_rate = win_rates.get(phase, 50)
        risk_level = 'HIGH' if win_rate < 50 else 'MODERATE' if win_rate < 70 else 'LOW'
        
        print(f"\n{phase.upper()}:")
        print(f"  Bets: {len(phase_df)} ({pct_of_bets:.1f}% of total)")
        print(f"  Bankroll Exposure: {total_exposure:.2f}%")
        print(f"  Historical Win Rate: {win_rate}%")
        print(f"  Risk Level: {risk_level}")
    
    # Critical alerts
    print('\n' + '='*60)
    print('🚨 CRITICAL ALERTS:')
    print('='*60)
    
    # Menstrual phase analysis
    menstrual = df[df['adv_phase'] == 'menstrual']
    if len(menstrual) > 0:
        print(f"\n⚠️  MENSTRUAL PHASE WARNING:")
        print(f"   - {len(menstrual)} bets at only 20% historical win rate")
        print(f"   - Total exposure: {menstrual['bet_percentage'].sum():.2f}% of bankroll")
        print(f"   - Expected loss: {menstrual['bet_percentage'].sum() * 0.6:.2f}% of bankroll")
        
        print("\n   Top 5 Menstrual Phase Bets (AVOID THESE):")
        top_menstrual = menstrual.nlargest(5, 'kelly_used')[
            ['player_name', 'stat_type', 'kelly_used', 'bet_percentage', 'line', 'adjusted_prediction']
        ]
        print(top_menstrual.to_string(index=False))
    
    # High exposure bets
    high_exposure = df[df['bet_percentage'] > 2.0]
    if len(high_exposure) > 0:
        print(f"\n⚠️  HIGH EXPOSURE BETS (>2% of bankroll):")
        print(high_exposure[['player_name', 'stat_type', 'bet_percentage', 'adv_phase']].to_string(index=False))
    
    return df


def create_safe_betting_card(df, output_path='output/daily_betting_card_safe.csv'):
    """Create a safer betting card by filtering risky bets"""
    
    print('\n' + '='*60)
    print('CREATING SAFE BETTING CARD')
    print('='*60)
    
    original_count = len(df)
    original_exposure = df['bet_percentage'].sum()
    
    # Filter out menstrual phase bets
    df_safe = df[df['adv_phase'] != 'menstrual'].copy()
    
    # Additional safety filters
    # Remove very low confidence bets
    df_safe = df_safe[df_safe['kelly_used'] > 0.001]
    
    # Cap maximum exposure
    df_safe.loc[df_safe['bet_percentage'] > 2.0, 'bet_percentage'] = 2.0
    df_safe.loc[df_safe['kelly_used'] > 0.02, 'kelly_used'] = 0.02
    
    # Recalculate totals
    safe_count = len(df_safe)
    safe_exposure = df_safe['bet_percentage'].sum()
    
    print(f"\nOriginal betting card:")
    print(f"  - Bets: {original_count}")
    print(f"  - Total exposure: {original_exposure:.2f}%")
    
    print(f"\nSafe betting card:")
    print(f"  - Bets: {safe_count}")
    print(f"  - Total exposure: {safe_exposure:.2f}%")
    print(f"  - Removed: {original_count - safe_count} risky bets")
    
    # Phase distribution in safe card
    print("\nSafe card phase distribution:")
    safe_phase_dist = df_safe['adv_phase'].value_counts()
    for phase, count in safe_phase_dist.items():
        print(f"  {phase}: {count} bets ({count/len(df_safe)*100:.1f}%)")
    
    # Save safe betting card
    df_safe.to_csv(output_path, index=False)
    print(f"\n✅ Safe betting card saved to: {output_path}")
    
    # Create summary report
    summary = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'original_bets': original_count,
        'safe_bets': safe_count,
        'removed_bets': original_count - safe_count,
        'original_exposure': f"{original_exposure:.2f}%",
        'safe_exposure': f"{safe_exposure:.2f}%",
        'phase_distribution': safe_phase_dist.to_dict()
    }
    
    import json
    with open('output/safe_betting_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    return df_safe


def create_optimal_slate(df_safe, max_bets=10, output_path='output/optimal_betting_slate.csv'):
    """Create an optimal slate of the best bets"""
    
    print('\n' + '='*60)
    print('OPTIMAL BETTING SLATE')
    print('='*60)
    
    # Prioritize by:
    # 1. Luteal phase (80% win rate)
    # 2. High Kelly values
    # 3. Phase-aligned risk tags
    
    df_optimal = df_safe.copy()
    
    # Add phase scores
    phase_scores = {
        'luteal': 1.0,
        'follicular': 0.7,
        'ovulation': 0.5,
        'menstrual': 0.0  # Should already be filtered out
    }
    
    df_optimal['phase_score'] = df_optimal['adv_phase'].map(phase_scores).fillna(0.5)
    
    # Add risk tag scores
    risk_scores = {
        'phase_aligned': 1.0,
        'high_confidence': 0.8,
        'moderate_confidence': 0.5,
        'low_confidence': 0.2
    }
    
    df_optimal['risk_score'] = df_optimal['adv_risk_tag'].map(risk_scores).fillna(0.5)
    
    # Calculate composite score
    df_optimal['composite_score'] = (
        df_optimal['kelly_used'] * 
        df_optimal['phase_score'] * 
        df_optimal['risk_score']
    )
    
    # Select top bets
    optimal_slate = df_optimal.nlargest(max_bets, 'composite_score')
    
    # Display optimal slate
    print(f"\nTop {max_bets} Optimal Bets:")
    display_cols = ['player_name', 'stat_type', 'line', 'kelly_used', 
                   'bet_percentage', 'adv_phase', 'adv_risk_tag', 'composite_score']
    print(optimal_slate[display_cols].to_string(index=False))
    
    # Calculate slate metrics
    total_exposure = optimal_slate['bet_percentage'].sum()
    phase_dist = optimal_slate['adv_phase'].value_counts()
    
    print(f"\nSlate Metrics:")
    print(f"  Total exposure: {total_exposure:.2f}%")
    print(f"  Average Kelly: {optimal_slate['kelly_used'].mean():.4f}")
    print(f"  Phase distribution: {phase_dist.to_dict()}")
    
    # Save optimal slate
    optimal_slate.drop(['phase_score', 'risk_score', 'composite_score'], axis=1, inplace=True)
    optimal_slate.to_csv(output_path, index=False)
    print(f"\n✅ Optimal betting slate saved to: {output_path}")
    
    return optimal_slate


def main():
    """Run complete phase risk analysis and generate safe betting cards"""
    
    # Run phase risk analysis
    df = analyze_phase_risk()
    
    # Create safe betting card
    df_safe = create_safe_betting_card(df)
    
    # Create optimal betting slate
    optimal_slate = create_optimal_slate(df_safe, max_bets=10)
    
    print('\n' + '='*60)
    print('📊 FINAL RECOMMENDATIONS:')
    print('='*60)
    print("1. ❌ AVOID all menstrual phase bets (20% win rate)")
    print("2. ✅ FOCUS on luteal phase bets (80% win rate)")
    print("3. 📉 CAP individual bets at 2% of bankroll")
    print("4. 🎯 USE the optimal slate for best risk/reward")
    print("5. 📈 TRACK actual results to validate phase performance")
    

if __name__ == "__main__":
    main()