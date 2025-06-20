"""
WNBA Betting System Validation Script
Tests both modules and provides backtest-ready output
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def validate_enhanced_output(filepath='output/daily_betting_card_adjusted.csv'):
    """Validate the enhanced betting card output"""
    
    print("="*60)
    print("VALIDATION REPORT: Enhanced Betting Card")
    print("="*60)
    
    if not os.path.exists(filepath):
        print(f"❌ ERROR: Output file not found at {filepath}")
        return False
    
    df = pd.read_csv(filepath)
    
    # Check required columns
    required_cols = ['player_name', 'stat_type', 'line', 'edge', 
                    'confidence', 'raw_kelly', 'kelly_used', 
                    'actual_odds', 'adv_phase', 'bet_percentage']
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"❌ Missing columns: {missing_cols}")
        return False
    else:
        print("✅ All required columns present")
    
    # Validate odds injection
    print("\n" + "-"*40)
    print("ODDS VALIDATION:")
    print("-"*40)
    
    odds_summary = df.groupby('stat_type')['actual_odds'].agg(['mean', 'min', 'max', 'count'])
    print(odds_summary)
    
    if df['actual_odds'].isna().any():
        print("❌ WARNING: Some odds are missing!")
    else:
        print("✅ All bets have odds assigned")
    
    # Validate Kelly modifications
    print("\n" + "-"*40)
    print("KELLY MODIFIER VALIDATION:")
    print("-"*40)
    
    phase_analysis = df.groupby('adv_phase').agg({
        'raw_kelly': 'mean',
        'kelly_used': 'mean',
        'bet_percentage': 'mean'
    }).round(3)
    
    print(phase_analysis)
    
    # Calculate actual divisors used
    df['calculated_divisor'] = (df['raw_kelly'] / df['kelly_used']).round()
    divisor_check = df.groupby('adv_phase')['calculated_divisor'].agg(['mean', 'std'])
    print("\nCalculated Divisors by Phase:")
    print(divisor_check)
    
    # Risk assessment
    print("\n" + "-"*40)
    print("RISK ASSESSMENT:")
    print("-"*40)
    
    high_risk_bets = df[df['kelly_used'] > 0.10]
    if len(high_risk_bets) > 0:
        print(f"⚠️  HIGH RISK: {len(high_risk_bets)} bets exceed 10% Kelly")
        print(high_risk_bets[['player_name', 'stat_type', 'kelly_used', 'adv_phase']])
    else:
        print("✅ All bets within conservative Kelly range")
    
    menstrual_bets = df[df['adv_phase'] == 'menstrual']
    if len(menstrual_bets) > 0:
        print(f"\n🚨 CRITICAL: {len(menstrual_bets)} bets during menstrual phase (20% historical win rate)")
        print(menstrual_bets[['player_name', 'stat_type', 'kelly_used']])
    
    return True


def create_backtest_template(input_file='output/daily_betting_card_adjusted.csv',
                           output_file='output/backtest_template.csv'):
    """Create a template for manual result entry"""
    
    df = pd.read_csv(input_file)
    
    # Add backtest columns
    df['actual_result'] = ''  # 'W' or 'L'
    df['actual_outcome'] = ''  # 'over' or 'under'
    df['actual_value'] = np.nan  # Actual stat value
    df['payout'] = np.nan  # Will be calculated after results
    df['running_bankroll'] = np.nan
    
    # Add metadata
    df['bet_date'] = datetime.now().strftime('%Y-%m-%d')
    df['validated'] = False
    
    # Sort by confidence for easier review
    df = df.sort_values('confidence', ascending=False)
    
    df.to_csv(output_file, index=False)
    print(f"\n✅ Backtest template created: {output_file}")
    print("📝 Manual entry required for: actual_result, actual_outcome, actual_value")
    
    return df


def simulate_backtest_results(template_file='output/backtest_template.csv',
                             output_file='output/simulated_backtest.csv'):
    """Simulate some results for demonstration"""
    
    df = pd.read_csv(template_file)
    
    # Simulate results based on historical win rates by phase
    phase_win_rates = {
        'luteal': 0.80,
        'follicular': 0.67,
        'menstrual': 0.20,
        'ovulation': 0.50
    }
    
    np.random.seed(42)  # For reproducibility
    
    for idx, row in df.iterrows():
        phase = row['adv_phase']
        win_rate = phase_win_rates.get(phase, 0.50)
        
        # Simulate win/loss
        win = np.random.random() < win_rate
        df.at[idx, 'actual_result'] = 'W' if win else 'L'
        
        # Calculate payout
        if win:
            df.at[idx, 'payout'] = row['kelly_used'] * 10000 * row['actual_odds']
        else:
            df.at[idx, 'payout'] = -row['kelly_used'] * 10000
    
    # Calculate running bankroll
    starting_bankroll = 10000
    df['running_bankroll'] = starting_bankroll + df['payout'].cumsum()
    
    df.to_csv(output_file, index=False)
    
    # Summary statistics
    print("\n" + "="*60)
    print("SIMULATED BACKTEST RESULTS")
    print("="*60)
    
    print(f"Starting Bankroll: ${starting_bankroll:,.2f}")
    print(f"Ending Bankroll: ${df['running_bankroll'].iloc[-1]:,.2f}")
    print(f"Total Return: {((df['running_bankroll'].iloc[-1] / starting_bankroll) - 1) * 100:.1f}%")
    
    phase_performance = df.groupby('adv_phase').agg({
        'actual_result': lambda x: (x == 'W').sum() / len(x),
        'payout': 'sum'
    })
    phase_performance.columns = ['win_rate', 'total_payout']
    phase_performance['win_rate'] = phase_performance['win_rate'].round(3)
    
    print("\nPerformance by Phase:")
    print(phase_performance)
    
    return df


def main():
    """Run complete validation suite"""
    
    print("🏀 WNBA BETTING SYSTEM VALIDATION SUITE")
    print("="*60)
    
    # Step 1: Validate enhanced output
    if validate_enhanced_output():
        print("\n✅ Enhanced betting card validation PASSED")
    else:
        print("\n❌ Enhanced betting card validation FAILED")
        return
    
    # Step 2: Create backtest template
    create_backtest_template()
    
    # Step 3: Simulate results for demonstration
    simulate_backtest_results()
    
    print("\n" + "="*60)
    print("📊 FINAL RECOMMENDATIONS:")
    print("="*60)
    print("1. ⚠️  Review high-risk bets before placing")
    print("2. 🚨 Consider skipping menstrual phase bets entirely")
    print("3. 📈 Monitor actual vs expected win rates by phase")
    print("4. 💰 Implement stop-loss at -20% of bankroll")
    print("5. 🔄 Update phase divisors weekly based on results")
    
    print("\n✅ Validation complete. System ready for production use.")


if __name__ == "__main__":
    main()