from core.backtester import HistoricalBacktester, BacktestConfig

def main():
    print("Starting WNBA Backtester with correct column mapping...")
    
    # Your actual column mapping based on the CSV structure
    column_mapping = {
        'GAME_DATE': 'Date',
        'PLAYER_NAME': 'Player', 
        'FG3M': '3PM'
        # PTS, REB, AST, STL, BLK already match
    }
    
    config = BacktestConfig(
        start_date="2024-07-01",
        end_date="2024-09-01",
        min_games_for_prediction=3
    )
    
    try:
        backtester = HistoricalBacktester(config)
        
        # Load data with manual column mapping
        import pandas as pd
        df = pd.read_csv("data/wnba_combined_gamelogs.csv")
        
        # Apply the column mapping
        df = df.rename(columns=column_mapping)
        
        # Set the renamed dataframe directly
        backtester.historical_data = df
        
        # Convert date with proper format - FIX FOR DATE PARSING
        backtester.historical_data['Date'] = pd.to_datetime(backtester.historical_data['Date'], format='%Y-%m-%d')
        start_date = pd.to_datetime(config.start_date)
        end_date = pd.to_datetime(config.end_date)
        backtester.historical_data = backtester.historical_data[
            (backtester.historical_data['Date'] >= start_date) & 
            (backtester.historical_data['Date'] <= end_date)
        ].sort_values(['Player', 'Date']).reset_index(drop=True)
        
        print(f"Loaded {len(backtester.historical_data)} game logs")
        print(f"Date range: {backtester.historical_data['Date'].min()} to {backtester.historical_data['Date'].max()}")
        print(f"Unique players: {backtester.historical_data['Player'].nunique()}")
        
        # Continue with the backtesting pipeline
        print("2. Generating synthetic props...")
        backtester.load_historical_props()
        
        print("3. Simulating predictions...")
        backtester.simulate_predictions()
        
        print("4. Calculating results...")
        results = backtester.calculate_actual_results()
        
        # Print results
        print(f"\n=== BACKTEST RESULTS ===")
        print(f"Total Bets: {results.get('total_bets', 0)}")
        print(f"Win Rate: {results.get('win_rate', 0)}%")
        print(f"ROI: {results.get('roi', 0)}%")
        print(f"Profit/Loss: ")
        print(f"Over Bets: {results.get('over_bets', 0)}")
        print(f"Under Bets: {results.get('under_bets', 0)}")
        
        # Check for UNDER bias
        total_directional = results.get('over_bets', 0) + results.get('under_bets', 0)
        if total_directional > 0:
            under_pct = (results.get('under_bets', 0) / total_directional) * 100
            print(f"UNDER Bias: {under_pct:.1f}%")
            
            if under_pct > 75:
                print("⚠️  HIGH UNDER BIAS DETECTED!")
            elif under_pct < 25:
                print("⚠️  HIGH OVER BIAS DETECTED!")
            else:
                print("✅ Reasonable prediction balance")
        
        # Detailed breakdown by stat type
        placed_bets = [r for r in backtester.prediction_results if r.result != 'NO_BET']
        if placed_bets:
            print(f"\n=== STAT BREAKDOWN ===")
            for stat in ['PTS', 'REB', 'AST', 'STL', 'BLK', '3PM']:
                stat_bets = [r for r in placed_bets if r.stat_type == stat]
                if stat_bets:
                    stat_wins = len([r for r in stat_bets if r.result == 'WIN'])
                    stat_unders = len([r for r in stat_bets if r.prediction == 'UNDER'])
                    win_rate = (stat_wins / len(stat_bets)) * 100
                    under_pct = (stat_unders / len(stat_bets)) * 100
                    print(f"{stat}: {len(stat_bets)} bets, {win_rate:.1f}% win rate, {under_pct:.1f}% UNDER")
        
        return results
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
