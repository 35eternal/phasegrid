"""
Comprehensive test script for WNBA Prediction Engine
Path: tests/test_comprehensive.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports and set working directory
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))
os.chdir(parent_dir)

from core.prediction_engine import PredictionEngine

def test_comprehensive():
    print("🏀 COMPREHENSIVE WNBA PREDICTION ENGINE TEST")
    print("=" * 50)
    print(f"Working directory: {os.getcwd()}")
    
    # Initialize engine
    engine = PredictionEngine(bankroll=1000.0)
    
    # Test scenarios
    test_cases = [
        {"player_name": "Caitlin Clark", "stat_type": "PTS", "prop_line": 16.5},
        {"player_name": "Caitlin Clark", "stat_type": "AST", "prop_line": 8.5},
        {"player_name": "A'ja Wilson", "stat_type": "PTS", "prop_line": 20.5},
        {"player_name": "A'ja Wilson", "stat_type": "REB", "prop_line": 9.5},
        {"player_name": "Breanna Stewart", "stat_type": "PTS", "prop_line": 18.5},
        {"player_name": "Sabrina Ionescu", "stat_type": "PTS", "prop_line": 17.5},
        {"player_name": "Sabrina Ionescu", "stat_type": "AST", "prop_line": 7.5},
    ]
    
    results = []
    
    print("\n🎯 INDIVIDUAL PREDICTIONS:")
    print("-" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['player_name']} - {test_case['stat_type']} O/U {test_case['prop_line']}")
        
        result = engine.predict(**test_case, odds=-110)
        results.append(result)
        
        print(f"   🎲 Recommendation: {result.recommendation}")
        print(f"   📊 Probability: {result.predicted_probability:.1%}")
        print(f"   🎯 Confidence: {result.confidence_score:.1%}")
        print(f"   🔥 Cycle: {result.cycle_state}")
        print(f"   📈 Volatility: {result.volatility_score:.3f}")
        
        if result.kelly_stake_pct:
            print(f"   💰 Kelly Stake: {result.kelly_stake_pct:.1%} (${result.kelly_stake_pct * 1000:.2f})")
            print(f"   💵 Expected Value: ${result.expected_value:.2f}")
        
        print(f"   📝 Notes: {result.debug_notes}")
    
    # Summary
    actionable_bets = [r for r in results if r.recommendation in ["OVER", "UNDER"]]
    
    print(f"\n📈 BETTING SUMMARY:")
    print("-" * 50)
    print(f"Total Predictions: {len(results)}")
    print(f"Actionable Bets: {len(actionable_bets)}")
    print(f"Pass Rate: {(len(results) - len(actionable_bets)) / len(results):.1%}")
    
    if actionable_bets:
        print(f"\n💰 RECOMMENDED BETS:")
        total_stake = 0
        total_ev = 0
        
        for bet in actionable_bets:
            stake_amount = bet.kelly_stake_pct * 1000 if bet.kelly_stake_pct else 0
            total_stake += stake_amount
            total_ev += bet.expected_value if bet.expected_value else 0
            
            print(f"   {bet.player_name} {bet.stat_type} {bet.recommendation}")
            print(f"   └── Stake: ${stake_amount:.2f} | EV: ${bet.expected_value:.2f} | Confidence: {bet.confidence_score:.1%}")
        
        print(f"\n📊 PORTFOLIO SUMMARY:")
        print(f"   Total Recommended Stake: ${total_stake:.2f}")
        print(f"   Total Expected Value: ${total_ev:.2f}")
        print(f"   Portfolio ROI: {(total_ev / total_stake * 100) if total_stake > 0 else 0:.1f}%")
    else:
        print("   No bets meet confidence threshold - conservative approach protecting bankroll!")
    
    # Top players by volume
    print(f"\n👥 TOP PLAYERS BY GAME VOLUME:")
    print("-" * 50)
    
    df = engine.df
    player_counts = df['Player'].value_counts().head(10)
    
    for i, (player, games) in enumerate(player_counts.items(), 1):
        summary = engine.get_player_summary(player)
        if 'stats' in summary and 'PTS' in summary['stats']:
            pts_avg = summary['stats']['PTS']['mean']
            cycle = summary['stats']['PTS']['cycle_state']
            print(f"   {i:2d}. {player}: {games} games | {pts_avg:.1f} PPG | {cycle}")
    
    # Test different confidence thresholds
    print(f"\n🎛️ CONFIDENCE THRESHOLD ANALYSIS:")
    print("-" * 50)
    
    thresholds = [0.55, 0.60, 0.65, 0.70, 0.75]
    original_threshold = engine.config['confidence_threshold']
    
    for threshold in thresholds:
        engine.config['confidence_threshold'] = threshold
        actionable_count = 0
        
        for test_case in test_cases:
            result = engine.predict(**test_case, odds=-110)
            if result.recommendation in ["OVER", "UNDER"]:
                actionable_count += 1
        
        print(f"   {threshold:.0%} threshold: {actionable_count}/{len(test_cases)} actionable bets")
    
    # Reset to original
    engine.config['confidence_threshold'] = original_threshold
    
    print(f"\n✅ COMPREHENSIVE TEST COMPLETE!")

if __name__ == "__main__":
    test_comprehensive()
