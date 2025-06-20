#!/usr/bin/env python3
"""
Working WNBA Backtester that uses your actual PredictionEngine methods.
This handles the column name and date format issues correctly.
Save as: working_backtester.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path

def run_working_backtest(start_date='2024-06-01', end_date='2024-08-31', 
                        confidence_threshold=50, initial_bankroll=10000,
                        max_bets=100):
    """
    Run a working backtest using your actual PredictionEngine methods.
    
    Args:
        start_date: Start date for backtest
        end_date: End date for backtest  
        confidence_threshold: Minimum confidence % to place bet (0-100)
        initial_bankroll: Starting bankroll amount
        max_bets: Maximum number of bets to place (for testing)
    """
    
    print("🏀 WORKING WNBA BACKTESTER")
    print("=" * 40)
    
    try:
        # Import your working prediction engine
        from core.prediction_engine import PredictionEngine
        
        # Initialize
        engine = PredictionEngine()
        print("✅ PredictionEngine loaded successfully")
        
        # Load raw data directly (avoid the column mapping issues)
        df = pd.read_csv("data/wnba_combined_gamelogs.csv")
        print(f"✅ Raw data loaded: {len(df)} rows")
        
        # Handle date format properly - use the original GAME_DATE column
        df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'], format='mixed', errors='coerce')
        
        # Filter by date range
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        test_df = df[(df['GAME_DATE'] >= start_dt) & (df['GAME_DATE'] <= end_dt)].copy()
        
        print(f"📅 Testing period: {start_date} to {end_date}")
        print(f"📊 Test data: {len(test_df)} game logs")
        print(f"👥 Players in test period: {test_df['PLAYER_NAME'].nunique()}")
        
        # Initialize tracking
        bets = []
        current_bankroll = initial_bankroll
        
        # Get players with sufficient data
        players = test_df['PLAYER_NAME'].value_counts()
        players_with_data = players[players >= 5].index.tolist()  # At least 5 games
        
        print(f"🎯 Testing {len(players_with_data)} players with sufficient data...")
        
        # Process each player
        for player_idx, player in enumerate(players_with_data[:20]):  # Test first 20 players
            
            print(f"   📊 {player_idx+1}/20: {player}")
            
            player_games = test_df[test_df['PLAYER_NAME'] == player].sort_values('GAME_DATE')
            
            if len(player_games) < 5:
                continue
            
            # Test predictions for this player
            for stat_type in ['PTS', 'REB', 'AST']:
                
                try:
                    # Use the actual predict method with the correct format
                    prediction_result = engine.predict(player, stat_type)
                    
                    if not prediction_result:
                        continue
                    
                    # Extract prediction details
                    confidence = prediction_result.get('confidence', 0)
                    recommendation = prediction_result.get('recommendation', 'PASS')
                    
                    # Convert confidence if it's a percentage string
                    if isinstance(confidence, str) and '%' in confidence:
                        confidence = float(confidence.replace('%', ''))
                    elif isinstance(confidence, str):
                        try:
                            confidence = float(confidence)
                        except:
                            confidence = 0
                    
                    # Skip low confidence or PASS recommendations
                    if confidence < confidence_threshold or recommendation == 'PASS':
                        continue
                    
                    # Generate a realistic prop line for backtesting
                    player_stat_data = player_games[stat_type].dropna()
                    if len(player_stat_data) < 3:
                        continue
                    
                    # Use recent average + some market adjustment as prop line
                    recent_avg = player_stat_data.tail(10).mean()
                    prop_line = round(recent_avg + np.random.normal(0, 1.5), 1)
                    
                    if prop_line <= 0:
                        continue
                    
                    # For backtesting, pick a random recent game as "the bet"
                    recent_games = player_games.tail(3)  # Last 3 games in test period
                    if len(recent_games) == 0:
                        continue
                    
                    test_game = recent_games.iloc[-1]  # Most recent game
                    actual_value = test_game[stat_type]
                    
                    if pd.isna(actual_value):
                        continue
                    
                    # Determine bet direction based on prediction recommendation
                    if recommendation.upper() == 'OVER' or 'over' in recommendation.lower():
                        bet_over = True
                        bet_type = 'OVER'
                    elif recommendation.upper() == 'UNDER' or 'under' in recommendation.lower():
                        bet_over = False  
                        bet_type = 'UNDER'
                    else:
                        # If unclear, use confidence vs recent performance
                        bet_over = recent_avg > prop_line
                        bet_type = 'OVER' if bet_over else 'UNDER'
                    
                    # Calculate bet size (conservative 2% of bankroll)
                    bet_fraction = min(0.02, confidence / 100 * 0.05)  # Max 2% or confidence-based
                    bet_amount = current_bankroll * bet_fraction
                    bet_amount = max(10, min(bet_amount, 100))  # Between $10-$100
                    
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
                        'recommendation': recommendation,
                        'won': won,
                        'payout': payout,
                        'bankroll_after': current_bankroll
                    }
                    
                    bets.append(bet_record)
                    
                    if len(bets) % 5 == 0:
                        print(f"      💰 {len(bets)} bets placed, bankroll: ${current_bankroll:.2f}")
                    
                    # Stop if we have enough bets
                    if len(bets) >= max_bets:
                        break
                        
                except Exception as e:
                    # Skip individual prediction errors
                    continue
            
            if len(bets) >= max_bets:
                break
        
        # Calculate results
        if not bets:
            print("❌ No bets were placed. Try lowering confidence_threshold.")
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
        avg_confidence = sum(bet['confidence'] for bet in bets) / total_bets
        
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
        
        print(f"\n📋 BREAKDOWN BY STAT:")
        for stat, data in stat_breakdown.items():
            stat_win_rate = data['wins'] / data['bets'] * 100 if data['bets'] > 0 else 0
            print(f"   {stat}: {data['bets']} bets, {stat_win_rate:.1f}% win rate, ${data['profit']:.2f} profit")
        
        # Show sample bets
        print(f"\n📝 SAMPLE BETS:")
        for i, bet in enumerate(bets[:5]):
            status = "✅ WIN" if bet['won'] else "❌ LOSS"
            print(f"   {i+1}. {bet['player']} {bet['stat']} {bet['bet_type']} {bet['prop_line']} (actual: {bet['actual_value']}) - {status}")
        
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
                'avg_confidence': avg_confidence
            },
            'stat_breakdown': stat_breakdown,
            'bets': bets
        }
        
        with open(output_dir / "working_backtest_results.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to output/working_backtest_results.json")
        
        return results
        
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_prediction_methods():
    """Test what prediction methods actually work."""
    try:
        from core.prediction_engine import PredictionEngine
        engine = PredictionEngine()
        
        print("🧪 TESTING PREDICTION METHODS")
        print("=" * 40)
        
        # Test the predict method
        print("Testing predict method...")
        try:
            result = engine.predict('Caitlin Clark', 'PTS')
            print(f"✅ predict() works!")
            if result:
                print(f"   Sample result keys: {list(result.keys())}")
                for key, value in result.items():
                    print(f"   {key}: {value}")
            else:
                print(f"   Result is None")
        except Exception as e:
            print(f"❌ predict() failed: {e}")
        
        # Test get_player_summary
        print(f"\nTesting get_player_summary method...")
        try:
            summary = engine.get_player_summary('Caitlin Clark')
            print(f"✅ get_player_summary() works!")
            if summary:
                print(f"   Summary type: {type(summary)}")
                if isinstance(summary, dict):
                    print(f"   Summary keys: {list(summary.keys())}")
        except Exception as e:
            print(f"❌ get_player_summary() failed: {e}")
        
        # Test batch_predict  
        print(f"\nTesting batch_predict method...")
        try:
            batch_result = engine.batch_predict(['Caitlin Clark'], ['PTS'])
            print(f"✅ batch_predict() works!")
            if batch_result:
                print(f"   Batch result type: {type(batch_result)}")
        except Exception as e:
            print(f"❌ batch_predict() failed: {e}")
            
    except Exception as e:
        print(f"❌ Could not test prediction methods: {e}")

if __name__ == "__main__":
    # First test the prediction methods
    test_prediction_methods()
    
    # Run working backtest
    print(f"\n" + "="*50)
    results = run_working_backtest(
        start_date='2024-06-01',
        end_date='2024-08-31',
        confidence_threshold=45,  # Lower threshold to get more bets
        initial_bankroll=10000,
        max_bets=50  # Test with 50 bets
    )
    
    if results:
        print(f"\n🎊 BACKTEST COMPLETED SUCCESSFULLY!")
        print(f"🎯 Key Metric: {results['summary']['win_rate']:.1f}% win rate")
        print(f"💰 Key Metric: {results['summary']['roi']:.1f}% ROI")
    else:
        print(f"\n❌ Backtest failed - check the error messages above")