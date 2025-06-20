#!/usr/bin/env python3
"""
Quick fix script to test your existing backtester with proper column names.
Save this as: quick_backtest_test.py
"""

import pandas as pd
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def check_data_format():
    """Check the format of your data file."""
    data_path = "data/wnba_combined_gamelogs.csv"
    
    try:
        df = pd.read_csv(data_path)
        print(f"✅ Data file found: {data_path}")
        print(f"📊 Shape: {df.shape}")
        print(f"🏷️  Columns: {list(df.columns)}")
        print(f"📅 Date range: {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")
        print(f"👥 Players: {df['PLAYER_NAME'].nunique()}")
        
        # Show sample data
        print(f"\n📋 Sample data:")
        print(df.head(3)[['PLAYER_NAME', 'GAME_DATE', 'PTS', 'REB', 'AST']].to_string())
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Data file not found: {data_path}")
        return False
    except Exception as e:
        print(f"❌ Error reading data: {e}")
        return False

def test_existing_backtester():
    """Test your existing backtester."""
    try:
        from core.backtester import WNBABacktester
        print(f"\n✅ Found existing WNBABacktester")
        
        # Create backtester with conservative settings
        config = {
            'confidence_threshold': 0.05,  # Very low to get some bets
            'min_games_threshold': 5,
            'initial_bankroll': 1000,
            'kelly_fraction': 0.1
        }
        
        backtester = WNBABacktester(config=config)
        
        # Test data loading
        data = backtester.load_data()
        print(f"✅ Data loaded: {len(data)} rows")
        
        # Run quick backtest on small date range
        print(f"🔄 Running quick backtest...")
        results = backtester.run_backtest(
            start_date='2024-06-01',
            end_date='2024-06-30'
        )
        
        metrics = results['metrics']
        print(f"\n🎉 QUICK TEST RESULTS:")
        print(f"   Total bets: {metrics.get('total_bets', 0)}")
        print(f"   Hit rate: {metrics.get('hit_rate', 0):.1f}%")
        print(f"   ROI: {metrics.get('roi', 0):.1f}%")
        
        return True
        
    except ImportError as e:
        print(f"❌ Could not import WNBABacktester: {e}")
        return False
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
        return False

def test_original_backtester():
    """Test the original backtester from the document."""
    try:
        # Import the original backtester (the one from your document)
        import importlib.util
        
        # Check if the original file exists
        original_path = Path("core/historical_backtester.py")  # Assuming this name
        if not original_path.exists():
            print(f"⚠️  Original backtester not found at {original_path}")
            return False
            
        # Load and test the original
        spec = importlib.util.spec_from_file_location("historical_backtester", original_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        print(f"✅ Found original HistoricalBacktester")
        
        # Test with corrected column names
        config = module.BacktestConfig(
            start_date="2024-06-01",
            end_date="2024-06-30",
            confidence_threshold=0.5,  # Lower threshold
            min_games_for_prediction=5
        )
        
        backtester = module.HistoricalBacktester(config)
        
        # This will likely fail due to column name issues, but let's see
        try:
            backtester.load_historical_data()
            print(f"✅ Original backtester data loading works!")
            return True
        except Exception as e:
            print(f"❌ Original backtester has column name issues: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Could not test original backtester: {e}")
        return False

def main():
    """Main test function."""
    print("🏀 WNBA Backtester Diagnosis")
    print("=" * 40)
    
    # Step 1: Check data
    if not check_data_format():
        print("❌ Cannot proceed without data file")
        return
    
    # Step 2: Test existing backtester
    print(f"\n🔍 Testing existing backtester...")
    if test_existing_backtester():
        print(f"✅ Your existing backtester works!")
        return
    
    # Step 3: Test original backtester
    print(f"\n🔍 Testing original backtester...")
    if test_original_backtester():
        print(f"✅ Original backtester works!")
        return
    
    print(f"\n📋 RECOMMENDATIONS:")
    print(f"1. Your existing WNBABacktester should work with the data")
    print(f"2. Try running: python -c \"from core.backtester import WNBABacktester; print('Import works!')\"")
    print(f"3. Check that core/__init__.py exists (create empty file if needed)")
    print(f"4. Make sure you're in the right directory")

if __name__ == "__main__":
    main()