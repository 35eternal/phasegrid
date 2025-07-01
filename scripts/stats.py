#!/usr/bin/env python3
"""
PhaseGrid Stats CLI
Displays daily ROI statistics from metrics database or CSV
"""
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import click
import plotly.graph_objects as go
from plotly.io import to_html
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StatsGenerator:
    """Generate statistics from betting data"""

    def __init__(self, data_source: str = 'csv'):
        self.data_source = data_source
        self.data_path = Path('data')
        self.metrics_path = self.data_path / 'metrics'
        self.bets_log_path = Path('bets_log.csv')

    def load_data(self, days: int = 7) -> pd.DataFrame:
        """Load betting data for the specified number of days"""
        if self.data_source == 'csv' and self.bets_log_path.exists():
            # Load from CSV
            df = pd.read_csv(self.bets_log_path)
            logger.info(f"Loaded {len(df)} records from {self.bets_log_path}")
        else:
            # Try to load from individual daily CSVs
            all_data = []
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y%m%d')
                csv_file = self.data_path / f'bets_{date_str}.csv'

                if csv_file.exists():
                    daily_df = pd.read_csv(csv_file)
                    all_data.append(daily_df)
                    logger.info(f"Loaded {len(daily_df)} records from {csv_file}")

                current_date += timedelta(days=1)

            if all_data:
                df = pd.concat(all_data, ignore_index=True)
            else:
                logger.warning("No betting data found")
                return pd.DataFrame()

        # Map columns to expected names
        column_mapping = {
            'Date': 'date',
            'Bet ID': 'bet_id',
            'Stake': 'stake', 
            'Payout': 'payout',
            'Result': 'result',
            'Status': 'status',
            'grade': 'result'  # In case grade is used instead of result
        }
        
        # Apply column mapping
        df.rename(columns=column_mapping, inplace=True)
        
        # Ensure we have required columns
        required_cols = ['date', 'stake', 'payout']
        if not all(col in df.columns for col in required_cols):
            logger.error(f"Missing required columns. Found: {df.columns.tolist()}")
            return pd.DataFrame()

        # Convert date column to datetime
        try:
            df['date'] = pd.to_datetime(df['date'])
        except:
            logger.error("Failed to convert date column to datetime")
            return pd.DataFrame()

        # Filter by days
        cutoff_date = datetime.now() - timedelta(days=days)
        df = df[df['date'] >= cutoff_date]

        return df

    def calculate_daily_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate daily statistics"""
        if df.empty:
            return pd.DataFrame()
            
        # Group by date
        daily_stats = df.groupby(df['date'].dt.date).agg({
            'stake': ['sum', 'count'],
            'payout': 'sum'
        }).round(2)

        daily_stats.columns = ['total_stake', 'bet_count', 'total_payout']
        daily_stats['net_profit'] = daily_stats['total_payout'] - daily_stats['total_stake']
        daily_stats['roi_percent'] = ((daily_stats['net_profit'] / daily_stats['total_stake']) * 100).round(2)
        daily_stats.reset_index(inplace=True)
        
        return daily_stats

    def calculate_daily_roi(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate ROI statistics by day"""
        return self.calculate_daily_stats(df)

    def generate_summary_stats(self, df: pd.DataFrame) -> Dict[str, float]:
        """Generate summary statistics"""
        if df.empty:
            return {
                'total_bets': 0,
                'total_stake': 0,
                'total_payout': 0,
                'net_profit': 0,
                'roi_percent': 0,
                'win_rate': 0
            }

        total_stake = df['stake'].sum()
        total_payout = df['payout'].sum()
        net_profit = total_payout - total_stake
        roi_percent = (net_profit / total_stake * 100) if total_stake > 0 else 0

        # Calculate win rate if we have result data
        win_rate = 0
        if 'result' in df.columns:
            wins = df[df['result'].str.upper().isin(['WON', 'WIN', 'W'])].shape[0]
            total_bets = df.shape[0]
            win_rate = (wins / total_bets * 100) if total_bets > 0 else 0

        return {
            'total_bets': len(df),
            'total_stake': round(total_stake, 2),
            'total_payout': round(total_payout, 2),
            'net_profit': round(net_profit, 2),
            'roi_percent': round(roi_percent, 2),
            'win_rate': round(win_rate, 2)
        }

    def create_roi_chart(self, daily_stats: pd.DataFrame) -> go.Figure:
        """Create ROI chart using Plotly"""
        fig = go.Figure()

        # Add ROI line
        fig.add_trace(go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['roi_percent'],
            mode='lines+markers',
            name='Daily ROI %',
            line=dict(color='blue', width=2),
            marker=dict(size=8)
        ))

        # Add profit bars
        fig.add_trace(go.Bar(
            x=daily_stats['date'],
            y=daily_stats['net_profit'],
            name='Net Profit ($)',
            yaxis='y2',
            opacity=0.7,
            marker_color='green'
        ))

        # Update layout
        fig.update_layout(
            title='Daily ROI and Profit',
            xaxis_title='Date',
            yaxis=dict(
                title='ROI %',
                side='left'
            ),
            yaxis2=dict(
                title='Net Profit ($)',
                overlaying='y',
                side='right'
            ),
            hovermode='x unified',
            template='plotly_white'
        )

        return fig

    def export_html_report(self, daily_stats: pd.DataFrame, 
                          summary_stats: Dict[str, float],
                          output_file: str = 'betting_stats.html'):
        """Export HTML report with charts"""
        # Create the chart
        fig = self.create_roi_chart(daily_stats)
        
        # Create HTML content
        html_content = f"""
        <html>
        <head>
            <title>Betting Statistics Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background-color: #f0f0f0; padding: 20px; border-radius: 10px; }}
                .stat-item {{ margin: 10px 0; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
            </style>
        </head>
        <body>
            <h1>Betting Statistics Report</h1>
            <div class="summary">
                <h2>Summary Statistics</h2>
                <div class="stat-item">Total Bets: {summary_stats['total_bets']}</div>
                <div class="stat-item">Total Stake: ${summary_stats['total_stake']}</div>
                <div class="stat-item">Total Payout: ${summary_stats['total_payout']}</div>
                <div class="stat-item">Net Profit: ${summary_stats['net_profit']}</div>
                <div class="stat-item">ROI: {summary_stats['roi_percent']}%</div>
                <div class="stat-item">Win Rate: {summary_stats['win_rate']}%</div>
            </div>
            
            {fig.to_html(include_plotlyjs='cdn', div_id="roi-chart")}
            
            <h2>Daily Statistics</h2>
            {daily_stats.to_html(index=False, classes='daily-stats-table')}
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        return output_file


# CLI Commands
@click.command()
@click.option('--days', default=7, help='Number of days to analyze')
@click.option('--output', type=click.Choice(['text', 'json', 'html']), 
              default='text', help='Output format')
@click.option('--file', default=None, help='Output file path')
def cli(days: int, output: str, file: Optional[str]):
    """Generate betting statistics report"""
    generator = StatsGenerator()
    
    click.echo(f"📊 Generating stats for the last {days} days...")
    
    # Load data
    data = generator.load_data(days=days)
    if data.empty:
        click.echo("❌ No data found for the specified period")
        sys.exit(1)
    
    # Calculate stats
    daily_stats = generator.calculate_daily_stats(data)
    summary_stats = generator.generate_summary_stats(data)
    
    # Output based on format
    if output == 'json':
        result = {
            'summary': summary_stats,
            'daily': daily_stats.to_dict('records')
        }
        if file:
            with open(file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            click.echo(f"✅ Stats saved to {file}")
        else:
            click.echo(json.dumps(result, indent=2, default=str))
            
    elif output == 'html':
        output_file = file or 'betting_stats.html'
        generator.export_html_report(daily_stats, summary_stats, output_file)
        click.echo(f"✅ HTML report saved to {output_file}")
        
    else:  # text output
        click.echo("\n📈 Summary Statistics:")
        click.echo(f"  Total Bets: {summary_stats['total_bets']}")
        click.echo(f"  Total Stake: ${summary_stats['total_stake']}")
        click.echo(f"  Total Payout: ${summary_stats['total_payout']}")
        click.echo(f"  Net Profit: ${summary_stats['net_profit']}")
        click.echo(f"  ROI: {summary_stats['roi_percent']}%")
        click.echo(f"  Win Rate: {summary_stats['win_rate']}%")
        
        click.echo("\n📅 Daily Breakdown:")
        for _, row in daily_stats.iterrows():
            click.echo(f"  {row['date']}: {row['bet_count']} bets, "
                      f"${row['net_profit']} profit, {row['roi_percent']}% ROI")


def main():
    """Main entry point with error handling"""
    try:
        cli()
    except Exception as e:
        logger.error(f"Error generating stats: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()