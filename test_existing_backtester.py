#!/usr/bin/env python3
"""
Simple test to work with your existing backtester, whatever it's called.
Save as: test_existing_backtester.py
"""

import pandas as pd
import sys
import importlib.util
from pathlib import Path

def load_and_inspect_backtester():
    """Load your existing backtester and figure out how to use it."""
    print("🔍 Inspecting your existing backtester...")
    
    try:
        # Load the backtester module
        spec = importlib.util.spec_from_file_location("backtester", "core/backtester.py")
        backtester_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(backtester_module)
        
        print("✅ Successfully loaded backtester module")
        
        # Find all classes
        classes = []
        for name in dir(backtester_module):
            obj = getattr(backtester_module, name)
            if isinstance(obj, type) and name[0].isupper() and 'Backtest' in name:
                classes.append((name, obj))
                print(f"   📋 Found class: {name}")
        
        if not classes:
            print("❌ No backtester classes found")
            return None
        
        # Try to use the first backtester class
        class_name, BacktesterClass = classes[0]
        print(f"🧪 Testing class: {class_name}")
        
        # Try to instantiate it
        backtester = BacktesterClass()
        print(f"✅ Successfully created {class_name} instance")
        
        # Check if it has a run method
        if hasattr(backtester, 'run_full_backtest'):
            print("✅ Found run_full_backtest method")
            
            # Try to run it
            print("🚀 Running full backtest...")
            results = backtester.run_full_backtest()
            
            print("🎉 BACKTEST RESULTS:")
            if isinstance(results, dict) and 'results' in results:
                metrics = results['results']
                print(f"   Total Bets: {metrics.get('total_bets', 'Unknown')}")
                print(f"   Win Rate: {metrics.get('win_rate', 'Unknown')}%")
                print(f"   ROI: {metrics.get('roi', 'Unknown')}%")
            else:
                print(f"   Results: {type(results)}")
                print(f"   Keys: {list(results.keys()) if isinstance(results, dict) else 'Not a dict'}")
            
            return results
            
        elif hasattr(backtester, 'load_historical_data'):
            print("✅ Found load_historical_data method")
            
            # Try to load data
            data = backtester.load_historical_data()
            print(f"✅ Loaded data: {len(data)} rows")
            
            # Try to run predictions if method exists
            if hasattr(backtester, 'load_historical_props'):
                print("🔄 Generating props...")
                props = backtester.load_historical_props()
                print(f"✅ Generated {len(props)} props")
                
                if hasattr(backtester, 'simulate_predictions'):
                    print("🎯 Simulating predictions...")
                    predictions = backtester.simulate_predictions()
                    print(f"✅ Generated {len(predictions)} predictions")
                    
                    if hasattr(backtester, 'calculate_actual_results'):
                        print("📊 Calculating results...")
                        results = backtester.calculate_actual_results()
                        print("🎉 BACKTEST RESULTS:")
                        print(f"   Total Bets: {results.get('total_bets', 'Unknown')}")
                        print(f"   Win Rate: {results.get('win_rate', 'Unknown')}%") 
                        print(f"   ROI: {results.get('roi', 'Unknown')}%")
                        
                        return results
            
            return {"status": "data_loaded", "rows": len(data)}
        
        else:
            print("❌ No recognized methods found")
            print(f"   Available methods: {[m for m in dir(backtester) if not m.startswith('_')]}")
            return None
            
    except Exception as e:
        print(f"❌ Error testing backtester: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_with_your_prediction_engine():
    """Test using your prediction engine directly."""
    print("\n🔧 Testing your PredictionEngine...")
    
    try:
        from core.prediction_engine import PredictionEngine
        
        engine = PredictionEngine()
        print("✅ PredictionEngine imported successfully")
        
        # Load your data
        df = pd.read_csv("data/wnba_combined_gamelogs.csv")
        print(f"✅ Data loaded: {len(df)} rows")
        
        # Test prediction on a sample player
        sample_player = df['PLAYER_NAME'].iloc[0]
        player_data = df[df['PLAYER_NAME'] == sample_player].sort_values('GAME_DATE')
        
        if len(player_data) > 10:
            # Test PTS prediction
            pts_data = player_data['PTS'].dropna().values[:10]  # First 10 games
            line_value = pts_data.mean() + 2  # Slightly above average
            
            prediction = engine.predict_over_under(
                pts_data, 
                line_value,
                volatility_window=5,
                cycle_window=3
            )
            
            print(f"✅ Sample prediction for {sample_player}:")
            print(f"   Line: {line_value:.1f}")
            print(f"   Recommendation: {prediction.get('recommendation', 'Unknown')}")
            print(f"   Confidence: {prediction.get('confidence', 'Unknown')}")
            print(f"   Expected Value: {prediction.get('expected_value', 'Unknown')}")
            
            return True
        else:
            print(f"❌ Not enough data for {sample_player}")
            return False
            
    except Exception as e:
        print(f"❌ PredictionEngine test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🏀 TESTING YOUR EXISTING SYSTEM")
    print("=" * 50)
    
    # Test 1: Your existing backtester
    results = load_and_inspect_backtester()
    
    if not results:
        # Test 2: Your prediction engine
        print("\n" + "=" * 50)
        if test_with_your_prediction_engine():
            print("\n✅ Your PredictionEngine works! We can build a simple backtester around it.")
        else:
            print("\n❌ Both tests failed. Let's debug further.")
    else:
        print(f"\n✅ Your existing backtester works!")

if __name__ == "__main__":
    main()