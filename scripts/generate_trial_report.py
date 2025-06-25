"""
Weekly Trial Report Generator - Fixed with proper encoding
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json

def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """Calculate Sharpe ratio for the returns"""
    if len(returns) == 0:
        return 0
    excess_returns = returns - risk_free_rate/252
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std() if excess_returns.std() > 0 else 0

def calculate_max_drawdown(cumulative_returns):
    """Calculate maximum drawdown from cumulative returns"""
    if len(cumulative_returns) == 0:
        return 0
    rolling_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - rolling_max) / rolling_max
    return drawdown.min()

def generate_weekly_report(start_date=None, end_date=None):
    """Generate comprehensive weekly performance report"""
    
    if not end_date:
        end_date = datetime.now().date()
    if not start_date:
        start_date = end_date - timedelta(days=7)
    
    print(f"Generating report for {start_date} to {end_date}")
    
    try:
        # Read CSV with no header
        metrics_df = pd.read_csv('output/paper_metrics.csv', header=None)
        
        # Filter for rows with exactly 8 columns (summary rows)
        summary_rows = metrics_df[metrics_df.count(axis=1) == 8]
        
        if len(summary_rows) > 0:
            summary_data = []
            for _, row in summary_rows.iterrows():
                try:
                    sim_id = str(row[0])
                    
                    # Extract date from timestamp or simulation ID
                    if 'today' in sim_id:
                        date_obj = datetime.now().date()
                    elif '_' in sim_id:
                        date_part = sim_id.split('_')[1]
                        if '-' in date_part:
                            date_obj = datetime.strptime(date_part, '%Y-%m-%d').date()
                        else:
                            # Try to parse from timestamp column
                            timestamp = pd.to_datetime(row[1])
                            date_obj = timestamp.date()
                    else:
                        continue
                    
                    summary_data.append({
                        'date': date_obj,
                        'starting_bankroll': float(row[2]),
                        'bets_placed': int(row[3]),
                        'bets_won': int(row[4]),
                        'bets_lost': int(row[5]),
                        'roi': float(row[6]),
                        'ending_bankroll': float(row[7])
                    })
                except Exception as e:
                    print(f"Skipping row due to error: {e}")
                    continue
            
            if summary_data:
                week_metrics = pd.DataFrame(summary_data)
                week_metrics = week_metrics[(week_metrics['date'] >= start_date) & (week_metrics['date'] <= end_date)]
            else:
                print("No valid summary data found!")
                return None
        else:
            print("No summary rows found in metrics file!")
            return None
            
    except FileNotFoundError:
        print("No metrics file found!")
        return None
    except Exception as e:
        print(f"Error loading metrics: {e}")
        return None
    
    if len(week_metrics) == 0:
        print("No data for specified date range!")
        return None
    
    # Calculate statistics
    week_metrics['profit'] = week_metrics['ending_bankroll'] - week_metrics['starting_bankroll']
    week_metrics['total_staked'] = week_metrics['starting_bankroll'] * 0.1
    week_metrics['cumulative_profit'] = week_metrics['profit'].cumsum()
    
    stats = {
        'period': f"{start_date} to {end_date}",
        'total_bets': int(week_metrics['bets_placed'].sum()),
        'winning_bets': int(week_metrics['bets_won'].sum()),
        'total_staked': float(week_metrics['total_staked'].sum()),
        'total_profit': float(week_metrics['profit'].sum()),
        'avg_daily_roi': float(week_metrics['roi'].mean()),
        'best_day_roi': float(week_metrics['roi'].max()),
        'worst_day_roi': float(week_metrics['roi'].min()),
        'win_rate': float(week_metrics['bets_won'].sum() / week_metrics['bets_placed'].sum()) if week_metrics['bets_placed'].sum() > 0 else 0,
        'sharpe_ratio': float(calculate_sharpe_ratio(week_metrics['roi'])),
        'max_drawdown': float(calculate_max_drawdown(week_metrics['cumulative_profit'])),
        'days_traded': int(len(week_metrics))
    }
    
    # Generate report
    report_dir = 'reports/weekly'
    os.makedirs(report_dir, exist_ok=True)
    
    report_filename = f"{report_dir}/weekly_report_{start_date}_{end_date}.md"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(f"# PhaseGrid Paper Trading Weekly Report\n\n")
        f.write(f"**Period**: {stats['period']}\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"- **Total Bets Placed**: {stats['total_bets']}\n")
        f.write(f"- **Win Rate**: {stats['win_rate']:.1%}\n")
        f.write(f"- **Total Profit**: ${stats['total_profit']:.2f}\n")
        f.write(f"- **Average Daily ROI**: {stats['avg_daily_roi']:.1%}\n")
        f.write(f"- **Sharpe Ratio**: {stats['sharpe_ratio']:.2f}\n\n")
        
        f.write("## Performance Metrics\n\n")
        f.write(f"- Best Day ROI: {stats['best_day_roi']:.1%}\n")
        f.write(f"- Worst Day ROI: {stats['worst_day_roi']:.1%}\n")
        f.write(f"- Maximum Drawdown: {stats['max_drawdown']:.1%}\n")
        f.write(f"- Days Traded: {stats['days_traded']}\n\n")
        
        f.write("## Daily Performance\n\n")
        f.write("| Date | Bets | Won | Lost | ROI | Profit |\n")
        f.write("|------|------|-----|------|-----|--------|\n")
        for _, day in week_metrics.iterrows():
            f.write(f"| {day['date']} | {day['bets_placed']} | {day['bets_won']} | {day['bets_lost']} | {day['roi']:.1%} | ${day['profit']:.2f} |\n")
        f.write("\n")
        
        f.write("## Recommendations\n\n")
        if stats['sharpe_ratio'] < 0.5:
            f.write("- [!] Low Sharpe ratio indicates high volatility relative to returns\n")
        if stats['win_rate'] < 0.52:
            f.write("- [!] Win rate below 52% threshold for profitable -110 odds betting\n")
        if stats['max_drawdown'] < -0.15:
            f.write("- [!] Significant drawdown detected - consider reducing position sizes\n")
        if stats['avg_daily_roi'] > 0.05:
            f.write("- [OK] Strong positive ROI - current strategy performing well\n")
    
    with open(f"{report_dir}/weekly_summary_{start_date}_{end_date}.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    print(f"Report saved to: {report_filename}")
    
    return stats

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate weekly paper trading report')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--period', type=str, choices=['daily', 'weekly', 'monthly'], 
                       default='weekly', help='Report period')
    
    args = parser.parse_args()
    
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
    else:
        start_date = None
        
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
    else:
        end_date = None
    
    generate_weekly_report(start_date, end_date)