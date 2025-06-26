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
        
        # Ensure we have required columns
        required_cols = ['date', 'stake', 'payout', 'grade']
        if not all(col in df.columns for col in required_cols):
            logger.error(f"Missing required columns. Found: {df.columns.tolist()}")
            return pd.DataFrame()
            
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter by days
        cutoff_date = datetime.now() - timedelta(days=days)
        df = df[df['date'] >= cutoff_date]
        
        return df
    
    def calculate_daily_roi(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate ROI statistics by day"""
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
        
        # Add win rate if we have grade data
        if 'grade' in df.columns:
            win_stats = df[df['grade'] == 'WIN'].groupby(df['date'].dt.date).size()
            daily_stats['wins'] = win_stats.reindex(daily_stats.index, fill_value=0)
            daily_stats['win_rate'] = ((daily_stats['wins'] / daily_stats['bet_count']) * 100).round(2)
        
        return daily_stats.reset_index()
    
    def generate_plotly_table(self, stats_df: pd.DataFrame, title: str = "Daily ROI Statistics") -> str:
        """Generate a Plotly table from statistics dataframe"""
        if stats_df.empty:
            return "<p>No data available for the selected period.</p>"
        
        # Determine which columns to show
        columns = ['date', 'bet_count', 'total_stake', 'total_payout', 'net_profit', 'roi_percent']
        if 'win_rate' in stats_df.columns:
            columns.append('win_rate')
        
        # Create column headers with better names
        header_names = {
            'date': 'Date',
            'bet_count': 'Bets',
            'total_stake': 'Stake ($)',
            'total_payout': 'Payout ($)',
            'net_profit': 'Profit ($)',
            'roi_percent': 'ROI (%)',
            'win_rate': 'Win Rate (%)'
        }
        
        # Format data for display
        formatted_data = []
        for col in columns:
            if col in stats_df.columns:
                if col == 'date':
                    formatted_data.append(stats_df[col].astype(str))
                elif col in ['total_stake', 'total_payout', 'net_profit']:
                    formatted_data.append(['${:.2f}'.format(x) for x in stats_df[col]])
                elif col in ['roi_percent', 'win_rate']:
                    formatted_data.append(['{}%'.format(x) for x in stats_df[col]])
                else:
                    formatted_data.append(stats_df[col].tolist())
        
        # Create the table
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=[header_names.get(col, col) for col in columns if col in stats_df.columns],
                fill_color='paleturquoise',
                align='center',
                font=dict(size=12, color='black')
            ),
            cells=dict(
                values=formatted_data,
                fill_color=[['lightcyan' if i % 2 == 0 else 'white' for i in range(len(stats_df))]],
                align='center',
                font=dict(size=11)
            )
        )])
        
        fig.update_layout(
            title=title,
            title_x=0.5,
            width=800,
            height=400
        )
        
        return to_html(fig, include_plotlyjs='cdn')


@click.command()
@click.option('--days', default=7, help='Number of days to analyze (default: 7)')
@click.option('--output', type=click.Choice(['console', 'html', 'json']), default='console', 
              help='Output format (default: console)')
@click.option('--source', type=click.Choice(['csv', 'db']), default='csv',
              help='Data source (default: csv)')
@click.option('--save-to', help='Save output to file')
def main(days: int, output: str, source: str, save_to: Optional[str]):
    """PhaseGrid Stats CLI - View daily ROI statistics"""
    try:
        click.echo(f"📊 Generating stats for the last {days} days...")
        
        # Initialize stats generator
        generator = StatsGenerator(data_source=source)
        
        # Load and process data
        df = generator.load_data(days=days)
        if df.empty:
            click.echo("❌ No data found for the specified period", err=True)
            sys.exit(1)
        
        # Calculate statistics
        stats = generator.calculate_daily_roi(df)
        
        # Output based on format
        if output == 'console':
            # Console table output
            click.echo("\n" + "="*60)
            click.echo(f"{'Date':<12} {'Bets':<6} {'Stake':<10} {'Payout':<10} {'Profit':<10} {'ROI':<8}")
            click.echo("="*60)
            
            for _, row in stats.iterrows():
                click.echo(
                    f"{row['date']!s:<12} "
                    f"{row['bet_count']:<6} "
                    f"${row['total_stake']:<9.2f} "
                    f"${row['total_payout']:<9.2f} "
                    f"${row['net_profit']:<9.2f} "
                    f"{row['roi_percent']:<7.2f}%"
                )
            
            click.echo("="*60)
            
            # Summary
            total_stake = stats['total_stake'].sum()
            total_payout = stats['total_payout'].sum()
            total_profit = stats['net_profit'].sum()
            overall_roi = (total_profit / total_stake * 100) if total_stake > 0 else 0
            
            click.echo(f"\n📈 Summary:")
            click.echo(f"   Total Bets: {stats['bet_count'].sum()}")
            click.echo(f"   Total Stake: ${total_stake:.2f}")
            click.echo(f"   Total Payout: ${total_payout:.2f}")
            click.echo(f"   Total Profit: ${total_profit:.2f}")
            click.echo(f"   Overall ROI: {overall_roi:.2f}%")
            
        elif output == 'html':
            html_content = generator.generate_plotly_table(stats)
            if save_to:
                Path(save_to).write_text(html_content)
                click.echo(f"✅ HTML table saved to {save_to}")
            else:
                click.echo(html_content)
                
        elif output == 'json':
            json_data = stats.to_dict(orient='records')
            json_output = json.dumps(json_data, indent=2, default=str)
            if save_to:
                Path(save_to).write_text(json_output)
                click.echo(f"✅ JSON data saved to {save_to}")
            else:
                click.echo(json_output)
        
    except Exception as e:
        logger.error(f"Error generating stats: {e}")
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
