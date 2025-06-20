"""
Basic test script for WNBA Prediction Engine
Path: tests/test_basic.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports and set working directory
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))
os.chdir(parent_dir)  # Ensure we're in the right directory for data paths

from core.prediction_engine import PredictionEngine

def test_basic():
    print("🏀 WNBA Prediction Engine - Basic Test")
    print("=" * 40)
    print(f"Working directory: {os.getcwd()}")
    
    try:
        # Initialize engine
        print("Initializing prediction engine...")
        engine = PredictionEngine(bankroll=1000.0)
        
        # Test prediction
        print("\nGenerating prediction for Caitlin Clark PTS...")
        result = engine.predict(
            player_name="Caitlin Clark",
            stat_type="PTS", 
            prop_line=18.5,
            odds=-110
        )
        
        # Display results
        print("\n📊 PREDICTION RESULTS:")
        print(f"Player: {result.player_name}")
        print(f"Stat: {result.stat_type}")
        print(f"Recommendation: {result.recommendation}")
        print(f"Probability: {result.predicted_probability:.1%}")
        print(f"Confidence: {result.confidence_score:.1%}")
        print(f"Cycle State: {result.cycle_state}")
        print(f"Volatility: {result.volatility_score:.3f}")
        
        if result.kelly_stake_pct:
            print(f"Kelly Stake: {result.kelly_stake_pct:.1%}")
            print(f"Stake Amount: ${result.kelly_stake_pct * 1000:.2f}")
        else:
            print("Kelly Stake: N/A")
        
        if result.expected_value:
            print(f"Expected Value: ${result.expected_value:.2f}")
        else:
            print("Expected Value: N/A")
        
        print(f"Debug Notes: {result.debug_notes}")
        
        # Test player summary
        print("\n📈 PLAYER SUMMARY:")
        summary = engine.get_player_summary("Caitlin Clark")
        if "error" not in summary:
            print(f"Total Games: {summary['total_games']}")
            print(f"Date Range: {summary['date_range']}")
            
            for stat, data in summary['stats'].items():
                if stat in ['PTS', 'AST', 'REB']:  # Show main stats only
                    print(f"\n{stat}:")
                    print(f"  Average: {data['mean']:.1f}")
                    print(f"  Range: {data['min']:.1f} - {data['max']:.1f}")
                    print(f"  Volatility: {data['volatility']:.3f}")
                    print(f"  Cycle State: {data['cycle_state']}")
        else:
            print(summary['error'])
        
        print("\n✅ BASIC TEST COMPLETED SUCCESSFULLY!")
        return True
            
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Make sure your data file exists at: data/wnba_combined_gamelogs.csv")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic()
    sys.exit(0 if success else 1)