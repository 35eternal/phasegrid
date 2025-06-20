#!/usr/bin/env python3
"""
Backtest Engine for WNBA Betting System
Simulates historical performance using actual results to calculate P&L and validate assumptions
"""

import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class BacktestEngine:
    def __init__(self, starting_bankroll=1000):
        """Initialize backtest engine with starting bankroll"""
        self.starting_bankroll = starting_bankroll
        self.bankroll = starting_bankroll
        self.bankroll_history = [starting_bankroll]
        self.results = []
        self.daily_returns = []
        
    def load_betting_card(self, filepath='output/daily_betting_card.csv'):
        """Load daily betting card with actual results"""
        try:
            df = pd.read_csv(filepath)
            # Filter for rows with actual results
            df = df[df['actual_result'].notna()]
            print(f"Loaded {len(df)} bets with actual results")
            return df
        except Exception as e:
            print(f"Error loading betting card: {e}")
            return None
    
    def calculate_bet_outcome(self, row):
        """Calculate win/loss for a single bet"""
        try:
            # Determine win/loss
            is_win = row['actual_result'] > row['line']
            
            # Calculate bet size and payout
            bet_size = self.bankroll * row['bet_percentage']
            
            if is_win:
                # Win: 90% payout (0.9x)
                payout = bet_size * 0.9
                profit = payout
            else:
                # Loss: lose bet amount
                profit = -bet_size
            
            # Update bankroll
            self.bankroll += profit
            self.bankroll_history.append(self.bankroll)
            
            # Calculate daily return for Sharpe ratio
            daily_return = profit / (self.bankroll - profit)
            self.daily_returns.append(daily_return)
            
            # Store result
            result = {
                'player_name': row['player_name'],
                'stat_type': row['stat_type'],
                'line': row['line'],
                'prediction': row['adjusted_prediction'],
                'actual': row['actual_result'],
                'is_win': is_win,
                'bet_percentage': row['bet_percentage'],
                'bet_size': bet_size,
                'profit': profit,
                'bankroll_after': self.bankroll,
                'phase': row.get('adv_phase', 'unknown'),
                'risk_tag': row.get('adv_risk_tag', 'unknown'),
                'kelly_fraction': row.get('kelly_fraction', 0),
                'kelly_used': row.get('kelly_used', 0)
            }
            
            self.results.append(result)
            return result
            
        except Exception as e:
            print(f"Error calculating bet outcome: {e}")
            return None
    
    def run_backtest(self, betting_card_df):
        """Run backtest on all bets"""
        print("\n🎲 Running Backtest...")
        
        for idx, row in betting_card_df.iterrows():
            if pd.notna(row.get('bet_percentage', None)) and row['bet_percentage'] > 0:
                self.calculate_bet_outcome(row)
        
        print(f"✅ Processed {len(self.results)} bets")
        print(f"💰 Final bankroll: ${self.bankroll:.2f}")
        
    def calculate_metrics(self):
        """Calculate overall performance metrics"""
        if not self.results:
            return None
        
        df = pd.DataFrame(self.results)
        
        # Basic metrics
        total_bets = len(df)
        wins = df['is_win'].sum()
        win_rate = wins / total_bets if total_bets > 0 else 0
        
        # Profit metrics
        total_profit = self.bankroll - self.starting_bankroll
        roi = total_profit / self.starting_bankroll
        
        # Drawdown calculation
        bankroll_series = pd.Series(self.bankroll_history)
        rolling_max = bankroll_series.expanding().max()
        drawdown = (bankroll_series - rolling_max) / rolling_max
        max_drawdown = abs(drawdown.min())
        
        # Average bet percentage
        avg_bet_pct = df['bet_percentage'].mean()
        
        # Sharpe ratio (using 0% risk-free rate)
        if len(self.daily_returns) > 1:
            returns_array = np.array(self.daily_returns)
            avg_return = np.mean(returns_array)
            std_return = np.std(returns_array)
            sharpe_ratio = avg_return / std_return * np.sqrt(252) if std_return > 0 else np.nan
        else:
            sharpe_ratio = np.nan
        
        metrics = {
            'total_bets': total_bets,
            'total_profit': round(total_profit, 2),
            'final_bankroll': round(self.bankroll, 2),
            'win_rate': round(win_rate, 3),
            'max_drawdown': round(max_drawdown, 3),
            'avg_bet_pct': round(avg_bet_pct, 3),
            'sharpe_ratio': round(sharpe_ratio, 2) if not np.isnan(sharpe_ratio) else 'NaN',
            'roi': round(roi, 3)
        }
        
        return metrics
    
    def calculate_metrics_by_phase(self):
        """Calculate metrics grouped by menstrual phase"""
        if not self.results:
            return None
        
        df = pd.DataFrame(self.results)
        phase_metrics = []
        
        for phase in df['phase'].unique():
            if phase and phase != 'unknown':
                phase_df = df[df['phase'] == phase]
                
                total_bets = len(phase_df)
                if total_bets > 0:
                    wins = phase_df['is_win'].sum()
                    win_rate = wins / total_bets
                    profit = phase_df['profit'].sum()
                    avg_bet = phase_df['bet_percentage'].mean()
                    
                    # Phase-specific Sharpe
                    phase_returns = phase_df['profit'] / phase_df['bet_size']
                    phase_returns = phase_returns[phase_returns.notna()]
                    
                    if len(phase_returns) > 1:
                        sharpe = phase_returns.mean() / phase_returns.std() * np.sqrt(252)
                    else:
                        sharpe = np.nan
                    
                    phase_metrics.append({
                        'phase': phase,
                        'total_bets': total_bets,
                        'win_rate': round(win_rate, 3),
                        'profit': round(profit, 2),
                        'avg_bet': round(avg_bet, 3),
                        'sharpe_ratio': round(sharpe, 2) if not np.isnan(sharpe) else 'NaN'
                    })
        
        return pd.DataFrame(phase_metrics)
    
    def calculate_metrics_by_risk_tag(self):
        """Calculate metrics grouped by risk tag"""
        if not self.results:
            return None
        
        df = pd.DataFrame(self.results)
        risk_metrics = []
        
        for risk_tag in df['risk_tag'].unique():
            if risk_tag and risk_tag != 'unknown':
                risk_df = df[df['risk_tag'] == risk_tag]
                
                total_bets = len(risk_df)
                if total_bets > 0:
                    wins = risk_df['is_win'].sum()
                    win_rate = wins / total_bets
                    profit = risk_df['profit'].sum()
                    avg_bet = risk_df['bet_percentage'].mean()
                    
                    risk_metrics.append({
                        'risk_tag': risk_tag,
                        'total_bets': total_bets,
                        'win_rate': round(win_rate, 3),
                        'profit': round(profit, 2),
                        'avg_bet': round(avg_bet, 3)
                    })
        
        return pd.DataFrame(risk_metrics)
    
    def plot_bankroll_curve(self, save_path='output/bankroll_curve.png'):
        """Plot bankroll progression over time"""
        plt.figure(figsize=(12, 6))
        
        # Create bet numbers for x-axis
        bet_numbers = range(len(self.bankroll_history))
        
        # Plot bankroll curve
        plt.plot(bet_numbers, self.bankroll_history, 'b-', linewidth=2, label='Bankroll')
        
        # Add starting bankroll reference line
        plt.axhline(y=self.starting_bankroll, color='gray', linestyle='--', 
                   alpha=0.5, label=f'Starting: ${self.starting_bankroll}')
        
        # Highlight drawdown periods
        bankroll_series = pd.Series(self.bankroll_history)
        rolling_max = bankroll_series.expanding().max()
        
        # Fill area between rolling max and actual bankroll
        plt.fill_between(bet_numbers, rolling_max, bankroll_series, 
                        where=(rolling_max > bankroll_series), 
                        color='red', alpha=0.2, label='Drawdown')
        
        # Formatting
        plt.title('Bankroll Progression', fontsize=14, fontweight='bold')
        plt.xlabel('Bet Number', fontsize=12)
        plt.ylabel('Bankroll ($)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.legend(loc='best')
        
        # Add final bankroll annotation
        final_bankroll = self.bankroll_history[-1]
        plt.annotate(f'Final: ${final_bankroll:.2f}', 
                    xy=(len(self.bankroll_history)-1, final_bankroll),
                    xytext=(10, 10), textcoords='offset points',
                    ha='left', fontsize=10,
                    bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Bankroll curve saved to {save_path}")
    
    def save_results(self):
        """Save all backtest results to CSV files"""
        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)
        
        # 1. Overall summary
        metrics = self.calculate_metrics()
        if metrics:
            summary_df = pd.DataFrame([metrics])
            summary_df.to_csv('output/backtest_summary.csv', index=False)
            print("📊 Saved backtest_summary.csv")
        
        # 2. Metrics by phase
        phase_metrics = self.calculate_metrics_by_phase()
        if phase_metrics is not None and not phase_metrics.empty:
            phase_metrics.to_csv('output/backtest_by_phase.csv', index=False)
            print("📊 Saved backtest_by_phase.csv")
        
        # 3. Metrics by risk tag
        risk_metrics = self.calculate_metrics_by_risk_tag()
        if risk_metrics is not None and not risk_metrics.empty:
            risk_metrics.to_csv('output/backtest_by_risk.csv', index=False)
            print("📊 Saved backtest_by_risk.csv")
        
        # 4. Detailed results
        if self.results:
            results_df = pd.DataFrame(self.results)
            results_df.to_csv('output/backtest_detailed.csv', index=False)
            print("📊 Saved backtest_detailed.csv")
    
    def print_summary(self):
        """Print backtest summary to console"""
        print("\n" + "="*60)
        print("📈 BACKTEST SUMMARY")
        print("="*60)
        
        metrics = self.calculate_metrics()
        if metrics:
            print(f"\n💰 Financial Performance:")
            print(f"   Starting Bankroll: ${self.starting_bankroll}")
            print(f"   Final Bankroll: ${metrics['final_bankroll']}")
            print(f"   Total Profit: ${metrics['total_profit']}")
            print(f"   ROI: {metrics['roi']*100:.1f}%")
            
            print(f"\n📊 Betting Statistics:")
            print(f"   Total Bets: {metrics['total_bets']}")
            print(f"   Win Rate: {metrics['win_rate']*100:.1f}%")
            print(f"   Avg Bet Size: {metrics['avg_bet_pct']*100:.1f}% of bankroll")
            
            print(f"\n⚠️  Risk Metrics:")
            print(f"   Max Drawdown: {metrics['max_drawdown']*100:.1f}%")
            print(f"   Sharpe Ratio: {metrics['sharpe_ratio']}")
        
        # Phase breakdown
        phase_metrics = self.calculate_metrics_by_phase()
        if phase_metrics is not None and not phase_metrics.empty:
            print(f"\n🌙 Performance by Menstrual Phase:")
            for _, row in phase_metrics.iterrows():
                print(f"   {row['phase'].title()}: {row['total_bets']} bets, "
                      f"{row['win_rate']*100:.1f}% win rate, ${row['profit']:.2f} profit")
        
        print("\n" + "="*60)


def main():
    """Main execution function"""
    print("🚀 Starting WNBA Betting Backtest Engine...")
    
    # Check for starting bankroll config
    starting_bankroll = 1000
    if os.path.exists('config/starting_bankroll.json'):
        try:
            with open('config/starting_bankroll.json', 'r') as f:
                config = json.load(f)
                starting_bankroll = config.get('starting_bankroll', 1000)
                print(f"📋 Loaded starting bankroll: ${starting_bankroll}")
        except:
            print("⚠️  Error loading config, using default bankroll: $1000")
    
    # Initialize backtest engine
    engine = BacktestEngine(starting_bankroll=starting_bankroll)
    
    # Load betting card
    betting_card = engine.load_betting_card()
    if betting_card is None or betting_card.empty:
        print("❌ No betting card data found!")
        return
    
    # Run backtest
    engine.run_backtest(betting_card)
    
    # Generate outputs
    engine.save_results()
    engine.plot_bankroll_curve()
    engine.print_summary()
    
    print("\n✅ Backtest complete! Check output/ directory for results.")


if __name__ == "__main__":
    main()