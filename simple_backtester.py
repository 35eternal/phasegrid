#!/usr/bin/env python3
"""
Simple backtester that works with your existing PredictionEngine.
This bypasses the method name issues and uses your working system.
Save as: simple_backtester.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path

def run_simple_backtest(start_date='2024-06-01', end_date='2024-08-31', 
                       confidence_threshold=0.55, initial_bankroll=10000):
    """
    Run a simple backtest using your existing PredictionEngine.
    
    Args:
        start_date: Start date for backtest
        end_date: End date for backtest  
        confidence_threshold: Minimum confidence to place bet
        initial_bankroll: Starting bankroll amount
    """
    
    print("🏀 SIMPLE WNBA BACKTESTER")
    print("=" * 40)
    
    try:
        # Import your working prediction engine
        from core.prediction_engine import PredictionEngine
        
        # Initialize
        engine = PredictionEngine()
        print("✅ PredictionEngine loaded successfully")
        
        # Load data
        df = pd.read_csv("data/wnba_combined_gamelogs.csv")
        df['Date'] = pd.to_datetime(df['Date'])  # Use the mapped column name
        
        # Filter by date range
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        test_df = df[(df['Date'] >= start_dt) & (df['Date'] <= end_dt)].copy()
        
        print(f"📅 Testing period: {start_date} to {end_date}")
        print(f"📊 Test data: {len(test_df)} game logs")
        
        # Initialize tracking
        bets = []
        current_bankroll = initial_bankroll
        
        # Group by player for sequential testing
        players = test_df['Player'].unique()
        print(f"👥 Testing {len(players)} players...")
        
        for player in players[:10]:  # Test first 10 players for speed
            player_games = test_df[test_df['Player'] == player].sort_values('Date')
            
            if len(player_games) < 5:  # Need minimum games
                continue
                
            print(f"🎯 Testing {player}...")
            
            # Test each game for this player
            for idx in range(5, len(player_games)):  # Start after 5 games for history
                current_game = player_games.iloc[idx]
                game_date = current_game['Date']
                
                # Test PTS prediction
                try:
                    # Get historical data up to this point
                    historical_data = player_games.iloc[:idx]
                    
                    # Generate a realistic prop line (player's recent average + some variance)
                    recent_avg = historical_data['PTS'].tail(10).mean()
                    prop_line = round(recent_avg + np.random.normal(0, 2), 1)
                    
                    if prop_line <= 0:
                        continue
                    
                    # Generate prediction using your working engine
                    # Note: Adapting to whatever method your engine actually has
                    result = engine.generate_prediction(player, 'PTS')
                    
                    if not result:
                        continue
                    
                    # Extract prediction details
                    confidence = result.get('confidence', 0) / 100  # Convert percentage
                    recommendation = result.get('recommendation', 'PASS')
                    
                    # Skip low confidence predictions
                    if confidence < confidence_threshold or recommendation == 'PASS':
                        continue
                    
                    # Determine bet direction and amount
                    actual_points = current_game['PTS']
                    if pd.isna(actual_points):
                        continue
                    
                    # Simple bet sizing (5% of bankroll)
                    bet_amount = current_bankroll * 0.05
                    
                    # Determine if we would bet over or under
                    recent_performance = historical_data['PTS'].tail(5).mean()
                    bet_over = recent_performance > prop_line
                    
                    # Determine outcome
                    if bet_over:
                        won = actual_points > prop_line
                        bet_type = 'OVER'
                    else:
                        won = actual_points < prop_line
                        bet_type = 'UNDER'
                    
                    # Calculate payout (assuming -110 odds)
                    if won:
                        payout = bet_amount * 0.909  # Win
                        current_bankroll += payout
                    else:
                        payout = -bet_amount  # Loss
                        current_bankroll -= bet_amount
                    
                    # Record bet
                    bet_record = {
                        'date': game_date.strftime('%Y-%m-%d'),
                        'player': player,
                        'stat': 'PTS',
                        'prop_line': prop_line,
                        'actual_value': actual_points,
                        'bet_type': bet_type,
                        'bet_amount': bet_amount,
                        'confidence': confidence,
                        'won': won,
                        'payout': payout,
                        'bankroll_after': current_bankroll
                    }
                    
                    bets.append(bet_record)
                    
                    if len(bets) % 10 == 0:
                        print(f"   📈 {len(bets)} bets placed...")
                    
                    # Stop if we have enough bets for testing
                    if len(bets) >= 50:
                        break
                        
                except Exception as e:
                    print(f"   ⚠️ Error with {player}: {e}")
                    continue
            
            if len(bets) >= 50:
                break
        
        # Calculate results
        if not bets:
            print("❌ No bets were placed. Try lowering confidence_threshold.")
            return
        
        total_bets = len(bets)
        wins = sum(1 for bet in bets if bet['won'])
        win_rate = wins / total_bets * 100
        
        total_wagered = sum(bet['bet_amount'] for bet in bets)
        total_profit = sum(bet['payout'] for bet in bets)
        roi = total_profit / total_wagered * 100
        
        final_bankroll = current_bankroll
        bankroll_return = (final_bankroll - initial_bankroll) / initial_bankroll * 100
        
        # Display results
        print(f"\n🎉 BACKTEST RESULTS")
        print(f"=" * 30)
        print(f"📊 Total Bets: {total_bets}")
        print(f"🎯 Win Rate: {win_rate:.1f}%")
        print(f"💰 ROI: {roi:.1f}%")
        print(f"💵 Total Profit: ${total_profit:.2f}")
        print(f"🏦 Final Bankroll: ${final_bankroll:.2f}")
        print(f"📈 Bankroll Return: {bankroll_return:.1f}%")
        
        # Save results
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        results = {
            'config': {
                'start_date': start_date,
                'end_date': end_date,
                'confidence_threshold': confidence_threshold,
                'initial_bankroll': initial_bankroll
            },
            'summary': {
                'total_bets': total_bets,
                'win_rate': win_rate,
                'roi': roi,
                'total_profit': total_profit,
                'final_bankroll': final_bankroll,
                'bankroll_return': bankroll_return
            },
            'bets': bets
        }
        
        with open(output_dir / "simple_backtest_results.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to output/simple_backtest_results.json")
        
        return results
        
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_prediction_engine_methods():
    """Check what methods are available in your PredictionEngine."""
    try:
        from core.prediction_engine import PredictionEngine
        engine = PredictionEngine()
        
        print("🔍 PREDICTION ENGINE METHODS:")
        print("=" * 40)
        
        methods = [method for method in dir(engine) 
                  if not method.startswith('_') and callable(getattr(engine, method))]
        
        for method in methods:
            print(f"   ✅ {method}")
        
        # Test the generate_prediction method that seems to work
        print(f"\n🧪 Testing generate_prediction method...")
        result = engine.generate_prediction('Caitlin Clark', 'PTS')
        
        if result:
            print(f"✅ Method works! Sample result:")
            for key, value in result.items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ Method returned None")
            
        return methods
        
    except Exception as e:
        print(f"❌ Error checking methods: {e}")
        return []

if __name__ == "__main__":
    # First check what methods are available
    methods = check_prediction_engine_methods()
    
    # Run simple backtest
    print(f"\n" + "="*50)
    results = run_simple_backtest(
        start_date='2024-06-01',
        end_date='2024-07-31',
        confidence_threshold=0.50,  # Lower threshold (50% instead of 55%)
        initial_bankroll=10000
    )