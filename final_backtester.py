#!/usr/bin/env python3
"""
Final WNBA Backtester that ignores PASS recommendations and bets on confidence.
Save as: final_backtester.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path

def run_final_backtest(start_date='2024-06-01', end_date='2024-08-31', 
                      confidence_threshold=0.40, initial_bankroll=10000,
                      max_bets=75):
    """
    Final backtest that ignores PASS recommendations and bets on raw confidence/probability.
    
    Args:
        start_date: Start date for backtest
        end_date: End date for backtest  
        confidence_threshold: Minimum confidence (0.0-1.0)
        initial_bankroll: Starting bankroll amount
        max_bets: Maximum number of bets to place
    """
    
    print("🏀 FINAL WNBA BACKTESTER - IGNORE PASS MODE")
    print("=" * 50)
    
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
        print(f"🎯 Confidence threshold: {confidence_threshold*100:.0f}% (IGNORING PASS RECOMMENDATIONS)")
        
        # Initialize tracking
        bets = []
        current_bankroll = initial_bankroll
        prediction_attempts = 0
        pass_recommendations = 0
        
        # Get players with sufficient data
        players = test_df['PLAYER_NAME'].value_counts()
        players_with_data = players[players >= 8].index.tolist()  # At least 8 games
        
        print(f"🎯 Testing {len(players_with_data)} players with sufficient data...")
        
        # Process each player
        for player_idx, player in enumerate(players_with_data[:30]):  # Test more players
            
            if player_idx % 5 == 0:
                print(f"   📊 {player_idx+1}/30: {player}")
            
            player_games = test_df[test_df['PLAYER_NAME'] == player].sort_values('GAME_DATE')
            
            if len(player_games) < 8:
                continue
            
            # Test predictions for this player
            for stat_type in ['PTS', 'REB', 'AST']:
                
                try:
                    prediction_attempts += 1
                    
                    # Use the actual predict method
                    prediction_result = engine.predict(player, stat_type)
                    
                    if not prediction_result:
                        continue
                    
                    # Extract prediction details from PredictionResult object
                    recommendation = getattr(prediction_result, 'recommendation', 'PASS')
                    confidence_score = getattr(prediction_result, 'confidence_score', 0)
                    predicted_probability = getattr(prediction_result, 'predicted_probability', 0.5)
                    volatility_score = getattr(prediction_result, 'volatility_score', 0)
                    
                    # Track PASS recommendations but IGNORE them for betting
                    if recommendation == 'PASS':
                        pass_recommendations += 1
                    
                    # IGNORE PASS - bet based on confidence and probability alone
                    if confidence_score < confidence_threshold:
                        continue
                    
                    # Generate a realistic prop line for backtesting
                    player_stat_data = player_games[stat_type].dropna()
                    if len(player_stat_data) < 5:
                        continue
                    
                    # Use season average with some market variance
                    season_avg = player_stat_data.mean()
                    recent_avg = player_stat_data.tail(10).mean()
                    
                    # Blend season and recent with market adjustment
                    blended_avg = (season_avg * 0.7) + (recent_avg * 0.3)
                    market_noise = np.random.normal(0, blended_avg * 0.08)  # ±8% variance
                    prop_line = round(blended_avg + market_noise, 1)
                    
                    if prop_line <= 0:
                        continue
                    
                    # Pick a recent game to test against
                    recent_games = player_games.tail(6)
                    if len(recent_games) == 0:
                        continue
                    
                    test_game = recent_games.iloc[np.random.randint(0, len(recent_games))]
                    actual_value = test_game[stat_type]
                    
                    if pd.isna(actual_value):
                        continue
                    
                    # Bet direction based on predicted_probability
                    # If probability > 0.5, bet OVER. If < 0.5, bet UNDER
                    if predicted_probability > 0.5:
                        bet_over = True
                        bet_type = 'OVER'
                        edge = predicted_probability - 0.5  # How much above 50%
                    else:
                        bet_over = False
                        bet_type = 'UNDER'
                        edge = 0.5 - predicted_probability  # How much below 50%
                    
                    # Calculate bet size based on confidence AND edge
                    # Higher confidence + higher edge = larger bet
                    combined_score = (confidence_score + edge) / 2
                    bet_fraction = min(0.025, combined_score * 0.04)  # Max 2.5% of bankroll
                    bet_amount = current_bankroll * bet_fraction
                    bet_amount = max(8, min(bet_amount, 75))  # Between $8-$75
                    
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
                        'confidence_score': confidence_score,
                        'predicted_probability': predicted_probability,
                        'original_recommendation': recommendation,
                        'volatility_score': volatility_score,
                        'edge': edge,
                        'combined_score': combined_score,
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
                    # Skip individual prediction errors
                    continue
            
            if len(bets) >= max_bets:
                break
        
        # Calculate results
        if not bets:
            print(f"❌ No bets were placed with confidence threshold {confidence_threshold*100:.0f}%.")
            print(f"💡 Try lowering confidence_threshold to 0.25 (25%) or 0.20 (20%)")
            print(f"📊 Prediction attempts: {prediction_attempts}")
            print(f"🛑 PASS recommendations: {pass_recommendations} ({pass_recommendations/prediction_attempts*100:.1f}%)")
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
        avg_confidence = sum(bet['confidence_score'] for bet in bets) / total_bets
        avg_probability = sum(bet['predicted_probability'] for bet in bets) / total_bets
        avg_edge = sum(bet['edge'] for bet in bets) / total_bets
        
        # Breakdown by stat type
        stat_breakdown = {}
        for bet in bets:
            stat = bet['stat']
            if stat not in stat_breakdown:
                stat_breakdown[stat] = {'bets': 0, 'wins': 0, 'profit': 0, 'avg_confidence': 0}
            stat_breakdown[stat]['bets'] += 1
            if bet['won']:
                stat_breakdown[stat]['wins'] += 1
            stat_breakdown[stat]['profit'] += bet['payout']
            stat_breakdown[stat]['avg_confidence'] += bet['confidence_score']
        
        # Calculate averages
        for stat in stat_breakdown:
            stat_breakdown[stat]['avg_confidence'] /= stat_breakdown[stat]['bets']
        
        # Breakdown by bet type
        over_bets = [bet for bet in bets if bet['bet_type'] == 'OVER']
        under_bets = [bet for bet in bets if bet['bet_type'] == 'UNDER']
        over_win_rate = sum(1 for bet in over_bets if bet['won']) / len(over_bets) * 100 if over_bets else 0
        under_win_rate = sum(1 for bet in under_bets if bet['won']) / len(under_bets) * 100 if under_bets else 0
        
        # Count original recommendations that we overrode
        original_pass = sum(1 for bet in bets if bet['original_recommendation'] == 'PASS')
        
        # Display results
        print(f"\n🎉 FINAL BACKTEST RESULTS")
        print(f"=" * 35)
        print(f"📊 Total Bets: {total_bets}")
        print(f"🎯 Win Rate: {win_rate:.1f}%")
        print(f"💰 ROI: {roi:.1f}%")
        print(f"💵 Total Profit: ${total_profit:.2f}")
        print(f"💸 Total Wagered: ${total_wagered:.2f}")
        print(f"🏦 Final Bankroll: ${final_bankroll:.2f}")
        print(f"📈 Bankroll Return: {bankroll_return:.1f}%")
        print(f"🎲 Avg Confidence: {avg_confidence*100:.1f}%")
        print(f"🎯 Avg Probability: {avg_probability*100:.1f}%")
        print(f"⚡ Avg Edge: {avg_edge*100:.1f}%")
        
        print(f"\n📋 BREAKDOWN BY STAT:")
        for stat, data in stat_breakdown.items():
            stat_win_rate = data['wins'] / data['bets'] * 100 if data['bets'] > 0 else 0
            print(f"   {stat}: {data['bets']} bets, {stat_win_rate:.1f}% win rate, ${data['profit']:.2f} profit, {data['avg_confidence']*100:.1f}% avg conf")
        
        print(f"\n📊 BREAKDOWN BY BET TYPE:")
        print(f"   OVER: {len(over_bets)} bets, {over_win_rate:.1f}% win rate")
        print(f"   UNDER: {len(under_bets)} bets, {under_win_rate:.1f}% win rate")
        
        print(f"\n🛑 PASS OVERRIDE ANALYSIS:")
        print(f"   Total prediction attempts: {prediction_attempts}")
        print(f"   PASS recommendations: {pass_recommendations} ({pass_recommendations/prediction_attempts*100:.1f}%)")
        print(f"   Bets placed despite PASS: {original_pass} ({original_pass/total_bets*100:.1f}% of our bets)")
        
        # Show sample bets
        print(f"\n📝 SAMPLE BETS:")
        for i, bet in enumerate(bets[:5]):
            status = "✅ WIN" if bet['won'] else "❌ LOSS"
            conf_display = f"{bet['confidence_score']*100:.0f}%"
            prob_display = f"{bet['predicted_probability']*100:.0f}%"
            override = " (OVERRODE PASS)" if bet['original_recommendation'] == 'PASS' else ""
            print(f"   {i+1}. {bet['player']} {bet['stat']} {bet['bet_type']} {bet['prop_line']} (actual: {bet['actual_value']:.1f}) - {status} - Conf: {conf_display}, Prob: {prob_display}{override}")
        
        # Performance vs break-even
        break_even_rate = 52.38  # Need 52.38% to break even at -110 odds
        print(f"\n🎯 PERFORMANCE ANALYSIS:")
        if win_rate > break_even_rate:
            print(f"✅ WIN RATE BEATS BREAK-EVEN: {win_rate:.1f}% > {break_even_rate}%")
        else:
            print(f"⚠️  Win rate below break-even: {win_rate:.1f}% < {break_even_rate}%")
            
        if roi > 0:
            print(f"✅ POSITIVE ROI: {roi:.1f}%")
        else:
            print(f"⚠️  Negative ROI: {roi:.1f}%")
        
        if bankroll_return > 0:
            print(f"✅ BANKROLL GREW: {bankroll_return:.1f}%")
        else:
            print(f"⚠️  Bankroll declined: {bankroll_return:.1f}%")
        
        # Save results
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        results = {
            'config': {
                'start_date': start_date,
                'end_date': end_date,
                'confidence_threshold': confidence_threshold,
                'initial_bankroll': initial_bankroll,
                'max_bets': max_bets,
                'ignored_pass_recommendations': True
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
                'avg_probability': avg_probability,
                'avg_edge': avg_edge,
                'prediction_attempts': prediction_attempts,
                'pass_recommendations': pass_recommendations,
                'pass_override_rate': original_pass / total_bets if total_bets > 0 else 0
            },
            'stat_breakdown': stat_breakdown,
            'bet_type_performance': {
                'over_bets': len(over_bets),
                'under_bets': len(under_bets),
                'over_win_rate': over_win_rate,
                'under_win_rate': under_win_rate
            },
            'bets': bets
        }
        
        with open(output_dir / "final_backtest_results.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to output/final_backtest_results.json")
        
        return results
        
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Run final backtest that ignores PASS recommendations
    print("🚀 Starting final backtester that ignores conservative PASS recommendations...")
    
    results = run_final_backtest(
        start_date='2024-06-01',
        end_date='2024-08-31',
        confidence_threshold=0.40,  # 40% confidence minimum
        initial_bankroll=10000,
        max_bets=75  # More bets for better sample size
    )
    
    if results:
        print(f"\n🎊 BACKTEST COMPLETED SUCCESSFULLY!")
        print(f"🎯 Win Rate: {results['summary']['win_rate']:.1f}%")
        print(f"💰 ROI: {results['summary']['roi']:.1f}%")
        print(f"🏦 Final Bankroll: ${results['summary']['final_bankroll']:.2f}")
        print(f"🛑 Overrode {results['summary']['pass_override_rate']*100:.1f}% PASS recommendations")
        
        # Final assessment
        if results['summary']['win_rate'] > 52.38 and results['summary']['roi'] > 0:
            print(f"\n🟢 SYSTEM SHOWS POSITIVE EDGE! Ready for live testing.")
        elif results['summary']['win_rate'] > 50:
            print(f"\n🟡 SYSTEM SHOWS POTENTIAL. Consider parameter tuning.")
        else:
            print(f"\n🔴 SYSTEM NEEDS IMPROVEMENT. Check thresholds and logic.")
    else:
        print(f"\n❌ Try lowering confidence_threshold to 0.35 or 0.30")