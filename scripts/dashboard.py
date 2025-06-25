# scripts/dashboard.py - PhaseGrid Monitoring Dashboard

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import seaborn as sns
from datetime import datetime, timedelta
import argparse
import logging
from typing import Dict, Tuple, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.metrics_database import MetricsDatabase


class TradingDashboard:
    """Generate visual dashboard for paper trading metrics"""
    
    def __init__(self, db_path: str = "data/paper_metrics.db"):
        self.db = MetricsDatabase(db_path)
        self.style_config()
    
    def style_config(self):
        """Configure matplotlib style"""
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
        plt.rcParams['figure.figsize'] = (15, 10)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12
    
    def generate_dashboard(self, days: int = 30, output_path: str = "dashboard.html") -> str:
        """
        Generate comprehensive dashboard
        
        Args:
            days: Number of days to include
            output_path: Path to save dashboard
            
        Returns:
            str: Path to generated dashboard
        """
        # Calculate date range
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Fetch data
        metrics_df = self.db.get_metrics_range(start_date, end_date)
        
        if metrics_df.empty:
            logging.warning("No data available for dashboard")
            return self._generate_empty_dashboard(output_path)
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 12))
        
        # Define grid layout
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Daily ROI Chart (top left, spans 2 columns)
        ax1 = fig.add_subplot(gs[0, :2])
        self._plot_daily_roi(ax1, metrics_df)
        
        # 2. Win Rate Trend (top right)
        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_win_rate_trend(ax2, metrics_df)
        
        # 3. Cumulative Profit (middle left, spans 2 columns)
        ax3 = fig.add_subplot(gs[1, :2])
        self._plot_cumulative_profit(ax3, metrics_df)
        
        # 4. Trade Volume (middle right)
        ax4 = fig.add_subplot(gs[1, 2])
        self._plot_trade_volume(ax4, metrics_df)
        
        # 5. Rolling Metrics (bottom left)
        ax5 = fig.add_subplot(gs[2, 0])
        self._plot_rolling_metrics(ax5, metrics_df)
        
        # 6. Best/Worst Days (bottom middle)
        ax6 = fig.add_subplot(gs[2, 1])
        self._plot_best_worst_days(ax6)
        
        # 7. Summary Stats (bottom right)
        ax7 = fig.add_subplot(gs[2, 2])
        self._plot_summary_stats(ax7, metrics_df)
        
        # Add title and timestamp
        fig.suptitle(f'PhaseGrid Paper Trading Dashboard - Last {days} Days', 
                    fontsize=16, fontweight='bold')
        fig.text(0.99, 0.01, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 
                ha='right', va='bottom', fontsize=8, alpha=0.5)
        
        # Save as image
        img_path = output_path.replace('.html', '.png')
        plt.savefig(img_path, dpi=300, bbox_inches='tight')
        
        # Generate HTML report
        html_content = self._generate_html_report(metrics_df, img_path, days)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logging.info(f"Dashboard generated: {output_path}")
        plt.close()
        
        return output_path
    
    def _plot_daily_roi(self, ax, df):
        """Plot daily ROI with color coding"""
        df['date'] = pd.to_datetime(df['date'])
        
        # Create bar colors based on positive/negative ROI
        colors = ['green' if roi > 0 else 'red' for roi in df['roi']]
        
        bars = ax.bar(df['date'], df['roi'], color=colors, alpha=0.7)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            if abs(height) > 5:  # Only label significant bars
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}%', ha='center', va='bottom' if height > 0 else 'top',
                       fontsize=8)
        
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_title('Daily ROI Performance')
        ax.set_xlabel('Date')
        ax.set_ylabel('ROI (%)')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(df) // 10)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def _plot_win_rate_trend(self, ax, df):
        """Plot win rate trend with moving average"""
        df['date'] = pd.to_datetime(df['date'])
        
        # Plot actual win rate
        ax.plot(df['date'], df['win_rate'], 'b-', label='Daily', alpha=0.5)
        
        # Add 7-day moving average if enough data
        if len(df) >= 7:
            df['win_rate_ma'] = df['win_rate'].rolling(window=7).mean()
            ax.plot(df['date'], df['win_rate_ma'], 'r-', label='7-day MA', linewidth=2)
        
        # Add target line
        ax.axhline(y=55, color='green', linestyle='--', alpha=0.5, label='Target (55%)')
        
        ax.set_title('Win Rate Trend')
        ax.set_ylabel('Win Rate (%)')
        ax.set_ylim(0, 100)
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_cumulative_profit(self, ax, df):
        """Plot cumulative profit with drawdown shading"""
        df['date'] = pd.to_datetime(df['date'])
        df['cumulative_profit'] = df['total_profit'].cumsum()
        
        # Calculate running maximum and drawdown
        df['running_max'] = df['cumulative_profit'].cummax()
        df['drawdown'] = df['cumulative_profit'] - df['running_max']
        
        # Plot cumulative profit
        ax.plot(df['date'], df['cumulative_profit'], 'b-', linewidth=2, label='Cumulative Profit')
        
        # Shade drawdown periods
        ax.fill_between(df['date'], df['cumulative_profit'], df['running_max'],
                       where=df['drawdown'] < 0, alpha=0.3, color='red', label='Drawdown')
        
        # Add zero line
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        ax.set_title('Cumulative Profit & Drawdown')
        ax.set_xlabel('Date')
        ax.set_ylabel('Profit ($)')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_trade_volume(self, ax, df):
        """Plot trade volume distribution"""
        # Create box plot of daily trade volumes
        trade_volumes = df['total_trades'].values
        
        box = ax.boxplot(trade_volumes, vert=True, patch_artist=True)
        box['boxes'][0].set_facecolor('lightblue')
        
        # Add individual points
        y = trade_volumes
        x = [1] * len(y)
        ax.scatter(x, y, alpha=0.5, s=30)
        
        # Add statistics
        mean_trades = trade_volumes.mean()
        ax.axhline(y=mean_trades, color='red', linestyle='--', label=f'Mean: {mean_trades:.1f}')
        
        ax.set_title('Daily Trade Volume Distribution')
        ax.set_ylabel('Number of Trades')
        ax.set_xticklabels(['Daily Trades'])
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_rolling_metrics(self, ax, df):
        """Plot 7-day rolling metrics"""
        rolling_df = self.db.calculate_rolling_metrics(days=7)
        
        if not rolling_df.empty:
            rolling_df['date'] = pd.to_datetime(rolling_df['date'])
            
            ax2 = ax.twinx()
            
            # Plot rolling win rate on left axis
            line1 = ax.plot(rolling_df['date'], rolling_df['rolling_win_rate'], 
                          'b-', label='7-day Win Rate', linewidth=2)
            ax.set_ylabel('Win Rate (%)', color='b')
            ax.tick_params(axis='y', labelcolor='b')
            
            # Plot rolling ROI on right axis
            line2 = ax2.plot(rolling_df['date'], rolling_df['rolling_roi'], 
                           'r-', label='7-day ROI', linewidth=2)
            ax2.set_ylabel('ROI (%)', color='r')
            ax2.tick_params(axis='y', labelcolor='r')
            
            # Combine legends
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax.legend(lines, labels, loc='upper left')
            
            ax.set_title('7-Day Rolling Averages')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        else:
            ax.text(0.5, 0.5, 'Insufficient data\nfor rolling metrics', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('7-Day Rolling Averages')
    
    def _plot_best_worst_days(self, ax):
        """Plot best and worst performing days"""
        best_worst = self.db.get_best_worst_days(limit=3)
        
        if not best_worst['best'].empty:
            # Prepare data
            best_days = best_worst['best'][['date', 'roi']].values
            worst_days = best_worst['worst'][['date', 'roi']].values
            
            # Create horizontal bar chart
            y_pos = range(len(best_days) + len(worst_days))
            dates = [f"{d[0]}" for d in best_days] + [f"{d[0]}" for d in worst_days]
            rois = [d[1] for d in best_days] + [d[1] for d in worst_days]
            colors = ['green'] * len(best_days) + ['red'] * len(worst_days)
            
            bars = ax.barh(y_pos, rois, color=colors, alpha=0.7)
            
            # Add value labels
            for i, (bar, roi) in enumerate(zip(bars, rois)):
                ax.text(roi, bar.get_y() + bar.get_height()/2,
                       f'{roi:.1f}%', ha='left' if roi > 0 else 'right',
                       va='center', fontsize=9)
            
            ax.set_yticks(y_pos)
            ax.set_yticklabels(dates, fontsize=8)
            ax.set_xlabel('ROI (%)')
            ax.set_title('Best & Worst Days')
            ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        else:
            ax.text(0.5, 0.5, 'No data available', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Best & Worst Days')
    
    def _plot_summary_stats(self, ax, df):
        """Display summary statistics"""
        ax.axis('off')
        
        # Calculate statistics
        total_days = len(df)
        profitable_days = (df['roi'] > 0).sum()
        total_profit = df['total_profit'].sum()
        avg_roi = df['roi'].mean()
        best_roi = df['roi'].max()
        worst_roi = df['roi'].min()
        total_trades = df['total_trades'].sum()
        avg_win_rate = df['win_rate'].mean()
        
        # Sharpe ratio approximation (assuming 0% risk-free rate)
        if df['roi'].std() > 0:
            sharpe = (avg_roi * 252**0.5) / (df['roi'].std() * 252**0.5)
        else:
            sharpe = 0
        
        # Create text summary
        stats_text = f"""
📊 SUMMARY STATISTICS
━━━━━━━━━━━━━━━━━━━━
Trading Days: {total_days}
Profitable Days: {profitable_days} ({profitable_days/total_days*100:.1f}%)

💰 PROFIT METRICS
Total Profit: ${total_profit:,.2f}
Average ROI: {avg_roi:.2f}%
Best Day: {best_roi:.1f}%
Worst Day: {worst_roi:.1f}%
Sharpe Ratio: {sharpe:.2f}

🎯 TRADE METRICS
Total Trades: {total_trades:,}
Avg Trades/Day: {total_trades/total_days:.1f}
Avg Win Rate: {avg_win_rate:.1f}%
"""
        
        ax.text(0.1, 0.95, stats_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='top',
               fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def _generate_html_report(self, df, img_path, days):
        """Generate HTML report with embedded image and stats"""
        total_profit = df['total_profit'].sum()
        avg_roi = df['roi'].mean()
        avg_win_rate = df['win_rate'].mean()
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>PhaseGrid Trading Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }}
        .summary {{
            display: flex;
            justify-content: space-around;
            margin-bottom: 30px;
        }}
        .metric {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-value {{
            font-size: 36px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-label {{
            color: #7f8c8d;
            margin-top: 5px;
        }}
        .positive {{ color: #27ae60; }}
        .negative {{ color: #e74c3c; }}
        .dashboard-image {{
            width: 100%;
            max-width: 1400px;
            margin: 0 auto;
            display: block;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            border-radius: 10px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>PhaseGrid Paper Trading Dashboard</h1>
        <p>Performance Summary - Last {days} Days</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <div class="metric-value {'' if total_profit >= 0 else 'negative'}">${total_profit:,.2f}</div>
            <div class="metric-label">Total Profit</div>
        </div>
        <div class="metric">
            <div class="metric-value {'' if avg_roi >= 0 else 'negative'}">{avg_roi:.1f}%</div>
            <div class="metric-label">Average ROI</div>
        </div>
        <div class="metric">
            <div class="metric-value">{avg_win_rate:.1f}%</div>
            <div class="metric-label">Win Rate</div>
        </div>
    </div>
    
    <img src="{os.path.basename(img_path)}" alt="Trading Dashboard" class="dashboard-image">
    
    <div class="footer">
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>PhaseGrid Trading System v1.0</p>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_empty_dashboard(self, output_path):
        """Generate placeholder dashboard when no data available"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>PhaseGrid Trading Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: #f5f5f5;
        }
        .message {
            text-align: center;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <div class="message">
        <h1>No Trading Data Available</h1>
        <p>Please run some paper trades before generating the dashboard.</p>
    </div>
</body>
</html>
"""
        with open(output_path, 'w') as f:
            f.write(html)
        return output_path
    
    def generate_ci_badge(self, output_path: str = "badge.svg") -> str:
        """Generate CI badge with current metrics"""
        # Get latest metrics
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        df = self.db.get_metrics_range(start_date, end_date)
        
        if df.empty:
            roi = 0
            color = "lightgray"
            text = "No Data"
        else:
            roi = df['roi'].mean()
            if roi > 10:
                color = "brightgreen"
            elif roi > 0:
                color = "green"
            elif roi > -5:
                color = "yellow"
            else:
                color = "red"
            text = f"{roi:.1f}%"
        
        # Generate SVG badge
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="120" height="20">
    <linearGradient id="b" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
    </linearGradient>
    <rect rx="3" width="120" height="20" fill="#555"/>
    <rect rx="3" x="70" width="50" height="20" fill="{color}"/>
    <rect rx="3" width="120" height="20" fill="url(#b)"/>
    <g fill="#fff" text-anchor="middle" font-family="Arial,sans-serif" font-size="11">
        <text x="35" y="14">7d ROI</text>
        <text x="95" y="14">{text}</text>
    </g>
</svg>"""
        
        with open(output_path, 'w') as f:
            f.write(svg)
        
        return output_path


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Generate PhaseGrid Trading Dashboard')
    parser.add_argument('--days', type=int, default=30, help='Number of days to include')
    parser.add_argument('--output', default='dashboard.html', help='Output file path')
    parser.add_argument('--badge', action='store_true', help='Generate CI badge')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    dashboard = TradingDashboard()
    
    if args.badge:
        badge_path = dashboard.generate_ci_badge()
        print(f"Badge generated: {badge_path}")
    else:
        output_path = dashboard.generate_dashboard(args.days, args.output)
        print(f"Dashboard generated: {output_path}")


if __name__ == "__main__":
    main()
