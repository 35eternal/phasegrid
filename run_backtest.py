#!/usr/bin/env python3
"""
PowerShell-friendly backtest runner for WNBA prediction system.
Run with: python run_backtest.py [options]
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.integrated_backtester import IntegratedWNBABacktester, BacktestConfig
    print("✅ Successfully imported integrated backtester")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run WNBA Prop Betting Backtest')
    
    parser.add_argument('--start-date', type=str, default='2024-05-01',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default='2024-09-30',
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--confidence', type=float, default=0.12,
                       help='Confidence threshold (0.05-0.30)')
    parser.add_argument('--kelly', type=float, default=0.20,
                       help='Kelly fraction (0.10-0.50)')
    parser.add_argument('--bankroll', type=float, default=10000,
                       help='Initial bankroll amount')
    parser.add_argument('--optimize', action='store_true',
                       help='Run parameter optimization')
    parser.add_argument('--quick', action='store_true',
                       help='Quick test (last 2 months only)')
    parser.add_argument('--data-path', type=str, default='data/wnba_combined_gamelogs.csv',
                       help='Path to historical data CSV')
    
    return parser.parse_args()

def main():
    """Main execution function."""
    print("🏀 WNBA Integrated Backtesting System")
    print("=" * 50)
    
    args = parse_arguments()
    
    # Quick mode uses recent data only
    if args.quick:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)  # Last 2 months
        args.start_date = start_date.strftime('%Y-%m-%d')
        args.end_date = end_date.strftime('%Y-%m-%d')
        print(f"🚀 Quick mode: Testing {args.start_date} to {args.end_date}")
    
    # Create configuration
    config = BacktestConfig(
        start_date=args.start_date,
        end_date=args.end_date,
        confidence_threshold=args.confidence,
        kelly_fraction=args.kelly,
        initial_bankroll=args.bankroll
    )
    
    print(f"📊 Configuration:")
    print(f"   Period: {config.start_date} to {config.end_date}")
    print(f"   Confidence Threshold: {config.confidence_threshold}")
    print(f"   Kelly Fraction: {config.kelly_fraction}")
    print(f"   Initial Bankroll: ${config.initial_bankroll:,.2f}")
    print(f"   Optimization: {'Yes' if args.optimize else 'No'}")
    
    try:
        # Initialize and run backtester
        backtester = IntegratedWNBABacktester(config)
        
        print(f"\n🔄 Starting backtest...")
        results = backtester.run_full_backtest(
            data_path=args.data_path,
            optimize=args.optimize,
            save_results=True
        )
        
        # Display results
        metrics = results['metrics']
        print(f"\n🎉 BACKTEST RESULTS")
        print(f"=" * 30)
        print(f"📈 Total Bets: {metrics.get('total_bets', 0)}")
        print(f"🎯 Win Rate: {metrics.get('win_rate', 0):.1f}%")
        print(f"💰 ROI: {metrics.get('roi', 0):.1f}%")
        print(f"💵 Total Profit: ${metrics.get('total_profit', 0):,.2f}")
        print(f"🏦 Final Bankroll: ${metrics.get('final_bankroll', 0):,.2f}")
        print(f"📊 Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        
        if args.optimize and results.get('optimization'):
            opt = results['optimization']
            print(f"\n🔧 OPTIMIZATION RESULTS")
            print(f"=" * 25)
            print(f"🎯 Optimized ROI: {opt.get('optimized_roi', 0):.1f}%")
            print(f"📏 Best Confidence: {opt.get('confidence_threshold', 0):.3f}")
            print(f"💪 Best Kelly: {opt.get('kelly_fraction', 0):.3f}")
        
        # Show file locations
        print(f"\n📁 OUTPUT FILES:")
        print(f"   📄 Report: output/integrated_backtest_report.txt")
        print(f"   📊 Data: output/integrated_backtest_results.json")
        
        return 0
        
    except FileNotFoundError:
        print(f"❌ Data file not found: {args.data_path}")
        print("   Make sure the data file exists and path is correct")
        return 1
        
    except Exception as e:
        print(f"❌ Backtest failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)