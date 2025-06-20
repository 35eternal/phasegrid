#!/usr/bin/env python3
"""
Fixed Working WNBA Backtester that properly handles PredictionResult objects.
Save as: fixed_working_backtester.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path

def run_fixed_backtest(start_date='2024-06-01', end_date='2024-08-31', 
                      confidence_threshold=0.40, initial_bankroll=10000,
                      max_bets=50):
    """
    Run a fixed backtest that properly handles PredictionResult objects.
    
    Args:
        start_date: Start date for backtest
        end_date: End date for backtest  
        confidence_threshold: Minimum confidence (0.0-1.0, e.g., 0.40 = 40%)
        initial_bankroll: Starting bankroll amount
        max_bets: Maximum number of bets to place
    """
    
    print("🏀 FIXED WORKING WNBA BACKTESTER")
    print("=" * 40)
    
    try:
        # Import your working prediction engine
        from core.prediction_engine import PredictionEngine
        
        # Initialize
        engine = PredictionEngine()
        print("✅ PredictionEngine loaded successfully")
        
        # Load raw data directly
        df = pd.read_csv("data/wnba_combined_gamelogs.csv")
        print(f"✅ Raw data loaded: {len(df)} rows")
        
        # Handle date format properly
        df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'], format='mixed', errors='coerce')
        
        # Filter by date range
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        test_df = df[(df['GAME_DATE'] >= start_dt) & (df['GAME_DATE'] <= end_dt)].copy()
        
        print(f"📅 Testing period: {start_date} to {end_date}")
        print(f"📊 Test data: {len(test_df)} game logs")
        print(f"👥 Players in test period: {test_df['PLAYER_NAME'].nunique()}")
        print(f"🎯 Confidence threshold: {confidence_threshold*100:.0f}%")
        
        # Initialize tracking
        bets = []
        current_bankroll = initial_bankroll
        
        # Get players with sufficient data
        players = test_df['PLAYER_NAME'].value_counts()
        players_with_data = players[players >= 5].index.tolist()
        
        print(f"🎯 Testing {len(players_with_data)} players with sufficient data...")
        
        # Process each player
        for player_idx, player in enumerate(players_with_data[:25]):  # Test first 25 players
            
            if player_idx % 5 == 0:
                print(f"   📊 {player_idx+1}/25: {player}")
            
            player_games = test_df[test_df['PLAYER_NAME'] == player].sort_values('GAME_DATE')
            
            if len(player_games) < 5:
                continue
            
            # Test predictions for this player
            for stat_type in ['PTS', 'REB', 'AST']:
                
                try:
                    # Use the actual predict method
                    prediction_result = engine.predict(player, stat_type)
                    
                    if not prediction_result:
                        continue
                    
                    # Extract prediction details from PredictionResult object
                    # Based on your test output, these are the available attributes
                    recommendation = getattr(prediction_result, 'recommendation', 'PASS')
                    confidence_pct = getattr(prediction_result, 'confidence', '0%')
                    probability_pct = getattr(prediction_result, 'probability', '50%')
                    
                    # Convert percentage strings to floats
                    try:
                        if isinstance(confidence_pct, str) and '%' in confidence_pct:
                            confidence = float(confidence_pct.replace('%', '')) / 100
                        else:
                            confidence = float(confidence_pct) if confidence_pct else 0
                    except:
                        confidence = 0
                    
                    try:
                        if isinstance(probability_pct, str) and '%' in probability_pct:
                            probability = float(probability_pct.replace('%', '')) / 100
                        else:
                            probability = float(probability_pct) if probability_pct else 0.5
                    except:
                        probability = 0.5
                    
                    # Skip low confidence or PASS recommendations
                    if confidence < confidence_threshold or recommendation == 'PASS':
                        continue
                    
                    # Generate a realistic prop line for backtesting
                    player_stat_data = player_games[stat_type].dropna()
                    if len(player_stat_data) < 3:
                        continue
                    
                    # Use recent average + some market adjustment as prop line
                    recent_avg = player_stat_data.tail(8).mean()
                    market_adjustment = np.random.normal(0, recent_avg * 0.1)  # ±10% variance
                    prop_line = round(recent_avg + market_adjustment, 1)
                    
                    if prop_line <= 0:
                        continue
                    
                    # For backtesting, pick a random recent game as "the bet"
                    recent_games = player_games.tail(5)  # Last 5 games in test period
                    if len(recent_games) == 0:
                        continue
                    
                    test_game = recent_games.iloc[np.random.randint(0, len(recent_games))]
                    actual_value = test_game[stat_type]
                    
                    if pd.isna(actual_value):
                        continue
                    
                    # Determine bet direction based on probability
                    if probability > 0.5:
                        bet_over = True
                        bet_type = 'OVER'
                    else:
                        bet_over = False
                        bet_type = 'UNDER'
                    
                    # Calculate bet size based on confidence (Kelly-like sizing)
                    # Higher confidence = larger bet, but capped at 3% of bankroll
                    bet_fraction = min(0.03, confidence * 0.05)  # Max 3% of bankroll
                    bet_amount = current_bankroll * bet_fraction
                    bet_amount = max(5, min(bet_amount, 50))  # Between $5-$50
                    
                    # Determine outcome
                    if bet_over:
                        won = actual_value > prop_line
                    else:
                        won = actual_value < prop_line
                    
                    # Calculate payout (assuming -110 odds)
                    if won:
                        payout = bet_amount * 0.909  # Win
                        current_bankroll += payout
                    else:
                        payout = -bet_amount  # Loss
                        current_bankroll -= bet_amount
                    
                    # Record bet
                    bet_record = {
                        'date': test_game['GAME_DATE'].strftime('%Y-%m-%d'),
                        'player': player,
                        'stat': stat_type,
                        'prop_line': prop_line,
                        'actual_value': actual_value,
                        'bet_type': bet_type,
                        'bet_amount': bet_amount,
                        'confidence': confidence,
                        'probability': probability,
                        'recommendation': recommendation,
                        'won': won,
                        'payout': payout,
                        'bankroll_after': current_bankroll
                    }
                    
                    bets.append(bet_record)
                    
                    if len(bets) % 10 == 0:
                        print(f"      💰 {len(bets)} bets placed, bankroll: ${current_bankroll:.2f}")
                    
                    # Stop if we have enough bets
                    if len(bets) >= max_bets:
                        break
                        
                except Exception as e:
                    # Skip individual prediction errors but show a few for debugging
                    if len(bets) < 5:
                        print(f"      ⚠️ Error with {player} {stat_type}: {e}")
                    continue
            
            if len(bets) >= max_bets:
                break
        
        # Calculate results
        if not bets:
            print(f"❌ No bets were placed with confidence threshold {confidence_threshold*100:.0f}%.")
            print(f"💡 Try lowering confidence_threshold to 0.30 (30%) or 0.25 (25%)")
            return None
        
        total_bets = len(bets)
        wins = sum(1 for bet in bets if bet['won'])
        win_rate = wins / total_bets * 100
        
        total_wagered = sum(bet['bet_amount'] for bet in bets)
        total_profit = sum(bet['payout'] for bet in bets)
        roi = total_profit / total_wagered * 100
        
        final_bankroll = current_bankroll
        bankroll_return = (final_bankroll - initial_bankroll) / initial_bankroll * 100
        
        # Calculate additional metrics
        avg_confidence = sum(bet['confidence'] for bet in bets) / total_bets * 100
        avg_probability = sum(bet['probability'] for bet in bets) / total_bets * 100
        
        # Breakdown by stat type
        stat_breakdown = {}
        for bet in bets:
            stat = bet['stat']
            if stat not in stat_breakdown:
                stat_breakdown[stat] = {'bets': 0, 'wins': 0, 'profit': 0}
            stat_breakdown[stat]['bets'] += 1
            if bet['won']:
                stat_breakdown[stat]['wins'] += 1
            stat_breakdown[stat]['profit'] += bet['payout']
        
        # Breakdown by bet type
        over_bets = [bet for bet in bets if bet['bet_type'] == 'OVER']
        under_bets = [bet for bet in bets if bet['bet_type'] == 'UNDER']
        over_win_rate = sum(1 for bet in over_bets if bet['won']) / len(over_bets) * 100 if over_bets else 0
        under_win_rate = sum(1 for bet in under_bets if bet['won']) / len(under_bets) * 100 if under_bets else 0
        
        # Display results
        print(f"\n🎉 BACKTEST RESULTS")
        print(f"=" * 30)
        print(f"📊 Total Bets: {total_bets}")
        print(f"🎯 Win Rate: {win_rate:.1f}%")
        print(f"💰 ROI: {roi:.1f}%")
        print(f"💵 Total Profit: ${total_profit:.2f}")
        print(f"💸 Total Wagered: ${total_wagered:.2f}")
        print(f"🏦 Final Bankroll: ${final_bankroll:.2f}")
        print(f"📈 Bankroll Return: {bankroll_return:.1f}%")
        print(f"🎲 Avg Confidence: {avg_confidence:.1f}%")
        print(f"🎯 Avg Probability: {avg_probability:.1f}%")
        
        print(f"\n📋 BREAKDOWN BY STAT:")
        for stat, data in stat_breakdown.items():
            stat_win_rate = data['wins'] / data['bets'] * 100 if data['bets'] > 0 else 0
            print(f"   {stat}: {data['bets']} bets, {stat_win_rate:.1f}% win rate, ${data['profit']:.2f} profit")
        
        print(f"\n📊 BREAKDOWN BY BET TYPE:")
        print(f"   OVER: {len(over_bets)} bets, {over_win_rate:.1f}% win rate")
        print(f"   UNDER: {len(under_bets)} bets, {under_win_rate:.1f}% win rate")
        
        # Show sample bets
        print(f"\n📝 SAMPLE BETS:")
        for i, bet in enumerate(bets[:5]):
            status = "✅ WIN" if bet['won'] else "❌ LOSS"
            conf_display = f"{bet['confidence']*100:.0f}%"
            print(f"   {i+1}. {bet['player']} {bet['stat']} {bet['bet_type']} {bet['prop_line']} (actual: {bet['actual_value']:.1f}) - {status} - Conf: {conf_display}")
        
        # Show confidence distribution
        confidence_ranges = {
            'Very High (60%+)': [b for b in bets if b['confidence'] >= 0.60],
            'High (50-60%)': [b for b in bets if 0.50 <= b['confidence'] < 0.60],
            'Medium (40-50%)': [b for b in bets if 0.40 <= b['confidence'] < 0.50],
            'Low (30-40%)': [b for b in bets if 0.30 <= b['confidence'] < 0.40],
        }
        
        print(f"\n📈 CONFIDENCE DISTRIBUTION:")
        for range_name, range_bets in confidence_ranges.items():
            if range_bets:
                range_wins = sum(1 for bet in range_bets if bet['won'])
                range_win_rate = range_wins / len(range_bets) * 100
                print(f"   {range_name}: {len(range_bets)} bets, {range_win_rate:.1f}% win rate")
        
        # Save results
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        results = {
            'config': {
                'start_date': start_date,
                'end_date': end_date,
                'confidence_threshold': confidence_threshold,
                'initial_bankroll': initial_bankroll,
                'max_bets': max_bets
            },
            'summary': {
                'total_bets': total_bets,
                'win_rate': win_rate,
                'roi': roi,
                'total_profit': total_profit,
                'total_wagered': total_wagered,
                'final_bankroll': final_bankroll,
                'bankroll_return': bankroll_return,
                'avg_confidence': avg_confidence,
                'avg_probability': avg_probability
            },
            'stat_breakdown': stat_breakdown,
            'confidence_ranges': {k: len(v) for k, v in confidence_ranges.items()},
            'bet_type_performance': {
                'over_bets': len(over_bets),
                'under_bets': len(under_bets),
                'over_win_rate': over_win_rate,
                'under_win_rate': under_win_rate
            },
            'bets': bets
        }
        
        with open(output_dir / "fixed_backtest_results.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to output/fixed_backtest_results.json")
        
        return results
        
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_prediction_result_object():
    """Test what attributes the PredictionResult object actually has."""
    try:
        from core.prediction_engine import PredictionEngine
        engine = PredictionEngine()
        
        print("🧪 TESTING PREDICTION RESULT OBJECT")
        print("=" * 40)
        
        # Get a prediction result
        result = engine.predict('Caitlin Clark', 'PTS')
        
        if result:
            print(f"✅ PredictionResult object created")
            print(f"   Type: {type(result)}")
            
            # Show all attributes
            print(f"   Available attributes:")
            for attr in dir(result):
                if not attr.startswith('_'):
                    try:
                        value = getattr(result, attr)
                        if not callable(value):
                            print(f"      {attr}: {value} ({type(value)})")
                    except:
                        print(f"      {attr}: <could not access>")
        else:
            print(f"❌ No prediction result returned")
            
    except Exception as e:
        print(f"❌ Could not test prediction result: {e}")

if __name__ == "__main__":
    # First test the prediction result object
    test_prediction_result_object()
    
    # Run fixed backtest with lower confidence threshold
    print(f"\n" + "="*50)
    results = run_fixed_backtest(
        start_date='2024-06-01',
        end_date='2024-08-31',
        confidence_threshold=0.30,  # 30% threshold - much lower
        initial_bankroll=10000,
        max_bets=50
    )
    
    if results:
        print(f"\n🎊 BACKTEST COMPLETED SUCCESSFULLY!")
        print(f"🎯 Win Rate: {results['summary']['win_rate']:.1f}%")
        print(f"💰 ROI: {results['summary']['roi']:.1f}%")
        print(f"🏦 Final Bankroll: ${results['summary']['final_bankroll']:.2f}")
        
        # Success criteria
        win_rate = results['summary']['win_rate']
        roi = results['summary']['roi']
        
        if win_rate > 52.38:  # Break-even at -110 odds
            print(f"✅ WIN RATE BEATS BREAK-EVEN: {win_rate:.1f}% > 52.38%")
        else:
            print(f"⚠️  Win rate below break-even: {win_rate:.1f}% < 52.38%")
            
        if roi > 0:
            print(f"✅ POSITIVE ROI: {roi:.1f}%")
        else:
            print(f"⚠️  Negative ROI: {roi:.1f}%")
            
    else:
        print(f"\n❌ Try an even lower confidence threshold (0.25 or 0.20)")