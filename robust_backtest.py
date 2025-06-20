from core.backtester import HistoricalBacktester, BacktestConfig
import pandas as pd

def main():
    print("Starting WNBA Backtester with robust date handling...")
    
    column_mapping = {
        'GAME_DATE': 'Date',
        'PLAYER_NAME': 'Player', 
        'FG3M': '3PM'
    }
    
    config = BacktestConfig(
        start_date="2024-07-01",
        end_date="2024-09-01",
        min_games_for_prediction=3
    )
    
    try:
        backtester = HistoricalBacktester(config)
        
        # Load and check data
        df = pd.read_csv("data/wnba_combined_gamelogs.csv")
        print(f"Original data shape: {df.shape}")
        
        # Apply column mapping
        df = df.rename(columns=column_mapping)
        
        # Try different date parsing approaches
        try:
            # Method 1: Specify format
            df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
        except:
            try:
                # Method 2: Let pandas infer
                df['Date'] = pd.to_datetime(df['Date'], infer_datetime_format=True)
            except:
                # Method 3: Force mixed format
                df['Date'] = pd.to_datetime(df['Date'], format='mixed')
        
        print(f"Date parsing successful. Date range: {df['Date'].min()} to {df['Date'].max()}")
        
        # Set the data
        backtester.historical_data = df
        
        # Filter by date range
        start_date = pd.to_datetime(config.start_date)
        end_date = pd.to_datetime(config.end_date)
        backtester.historical_data = backtester.historical_data[
            (backtester.historical_data['Date'] >= start_date) & 
            (backtester.historical_data['Date'] <= end_date)
        ].sort_values(['Player', 'Date']).reset_index(drop=True)
        
        print(f"Filtered to {len(backtester.historical_data)} game logs")
        print(f"Players: {backtester.historical_data['Player'].nunique()}")
        
        # Continue pipeline
        print("Generating props...")
        backtester.load_historical_props()
        print(f"Generated {len(backtester.synthetic_props)} props")
        
        print("Running predictions...")
        backtester.simulate_predictions()
        
        print("Calculating results...")
        results = backtester.calculate_actual_results()
        
        # Results
        print(f"\n=== RESULTS ===")
        if results.get('total_bets', 0) > 0:
            print(f"Total Bets: {results['total_bets']}")
            print(f"Win Rate: {results['win_rate']}%")
            print(f"ROI: {results['roi']}%")
            
            over_bets = results.get('over_bets', 0)
            under_bets = results.get('under_bets', 0)
            total = over_bets + under_bets
            
            if total > 0:
                under_pct = (under_bets / total) * 100
                print(f"UNDER Bias: {under_pct:.1f}%")
                
                if under_pct > 75:
                    print("🚨 STRONG UNDER BIAS - This confirms your observation!")
                    print("   Possible causes:")
                    print("   - Synthetic lines too high (market overestimates)")
                    print("   - Players underperform late in season")
                    print("   - Volatility model favoring unders")
        else:
            print("❌ No bets placed - confidence thresholds too high")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
