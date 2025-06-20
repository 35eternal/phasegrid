#!/usr/bin/env python3
"""
Phase Performance Updater Module
Updates historical phase win rates based on actual betting outcomes.
"""

import pandas as pd
import numpy as np
from datetime import datetime


class PhasePerformanceUpdater:
    """Updates cumulative phase performance statistics based on betting results."""
    
    def __init__(self):
        self.betting_results = None
        self.phase_performance = None
        self.today_summary = {}
        self.confidence_changes = []
        
    def load_data(self):
        """Load betting results and existing phase performance data."""
        try:
            # Load today's betting results
            self.betting_results = pd.read_csv('output/final_betting_card.csv')
            print(f"✓ Loaded betting results: {len(self.betting_results)} bets")
            
            # Load existing phase performance
            self.phase_performance = pd.read_csv('output/backtest_by_phase.csv')
            print(f"✓ Loaded phase performance: {len(self.phase_performance)} phases")
            
            # Standardize column names
            column_mapping = {
                'Phase': 'phase',
                'Total Bets': 'total_bets',
                'Win Rate': 'win_rate',
                'Total Wins': 'total_wins',
                'wins': 'total_wins',
                'bets': 'total_bets'
            }
            
            # Rename columns if needed
            for old_name, new_name in column_mapping.items():
                if old_name in self.phase_performance.columns:
                    self.phase_performance.rename(columns={old_name: new_name}, inplace=True)
                    
            # Ensure phase column is lowercase
            if 'phase' in self.phase_performance.columns:
                self.phase_performance['phase'] = self.phase_performance['phase'].str.lower()
                
            # Calculate missing columns if needed
            if 'total_wins' not in self.phase_performance.columns and 'win_rate' in self.phase_performance.columns:
                # Ensure win_rate is in decimal format (0-1)
                if self.phase_performance['win_rate'].max() > 1:
                    self.phase_performance['win_rate'] = self.phase_performance['win_rate'] / 100
                    
                # Calculate total_wins from win_rate and total_bets
                self.phase_performance['total_wins'] = (
                    self.phase_performance['win_rate'] * self.phase_performance['total_bets']
                ).round().astype(int)
                print("  ℹ️  Calculated total_wins from win_rate")
                
            print(f"  📋 Columns: {list(self.phase_performance.columns)}")
            
        except FileNotFoundError as e:
            print(f"❌ Error loading files: {e}")
            raise
            
    def calculate_today_performance(self):
        """Calculate wins and losses for each phase from today's bets."""
        
        # Ensure we have the required columns
        required_cols = ['adv_phase', 'actual_result', 'line']
        missing_cols = [col for col in required_cols if col not in self.betting_results.columns]
        
        if missing_cols:
            print(f"⚠️  Warning: Missing columns {missing_cols}")
            return
            
        # Filter out rows with missing data
        valid_bets = self.betting_results.dropna(subset=['adv_phase', 'actual_result', 'line'])
        print(f"\n📊 Processing {len(valid_bets)} bets with complete data (out of {len(self.betting_results)} total)")
        
        # Calculate wins per phase
        for phase in valid_bets['adv_phase'].str.lower().unique():
            phase_bets = valid_bets[valid_bets['adv_phase'].str.lower() == phase]
            
            # Count total bets and wins
            total_bets = len(phase_bets)
            wins = len(phase_bets[phase_bets['actual_result'] > phase_bets['line']])
            
            self.today_summary[phase] = {
                'new_bets': total_bets,
                'new_wins': wins,
                'today_win_rate': wins / total_bets if total_bets > 0 else 0
            }
            
    def update_cumulative_performance(self):
        """Update the cumulative phase performance with today's results."""
        
        # Store original values for comparison
        original_performance = self.phase_performance.copy()
        
        # Update each phase
        for phase, today_stats in self.today_summary.items():
            # Find the phase in existing data
            phase_mask = self.phase_performance['phase'] == phase
            
            if phase_mask.any():
                # Update existing phase
                idx = self.phase_performance[phase_mask].index[0]
                
                # Get current values
                current_total_bets = self.phase_performance.loc[idx, 'total_bets']
                current_total_wins = self.phase_performance.loc[idx, 'total_wins']
                
                # Calculate new totals
                new_total_bets = current_total_bets + today_stats['new_bets']
                new_total_wins = current_total_wins + today_stats['new_wins']
                new_win_rate = new_total_wins / new_total_bets if new_total_bets > 0 else 0
                
                # Update the dataframe
                self.phase_performance.loc[idx, 'total_bets'] = new_total_bets
                self.phase_performance.loc[idx, 'total_wins'] = new_total_wins
                self.phase_performance.loc[idx, 'win_rate'] = new_win_rate
                
                # Check for confidence level changes
                self.check_confidence_changes(phase, current_total_bets, new_total_bets, new_win_rate)
                
            else:
                # Add new phase
                new_row = {
                    'phase': phase,
                    'total_bets': today_stats['new_bets'],
                    'total_wins': today_stats['new_wins'],
                    'win_rate': today_stats['today_win_rate']
                }
                self.phase_performance = pd.concat([self.phase_performance, pd.DataFrame([new_row])], 
                                                 ignore_index=True)
                
    def check_confidence_changes(self, phase, old_total, new_total, win_rate):
        """Check if phase crossed confidence thresholds."""
        
        # Ensure win_rate is in decimal format for comparison
        if win_rate > 1:
            win_rate = win_rate / 100
        
        # Check 20-bet threshold
        if old_total < 20 <= new_total:
            if win_rate >= 0.6:
                self.confidence_changes.append({
                    'phase': phase,
                    'change': 'Reached 20+ bets with 60%+ win rate → Can upgrade to MEDIUM confidence',
                    'new_total': new_total,
                    'win_rate': win_rate
                })
                
        # Check 30-bet threshold  
        if old_total < 30 <= new_total:
            if win_rate >= 0.7:
                self.confidence_changes.append({
                    'phase': phase,
                    'change': 'Reached 30+ bets with 70%+ win rate → Can upgrade to HIGH confidence',
                    'new_total': new_total,
                    'win_rate': win_rate
                })
                
    def save_updated_performance(self):
        """Save the updated phase performance data."""
        
        # Sort by phase for consistency
        self.phase_performance = self.phase_performance.sort_values('phase').reset_index(drop=True)
        
        # Ensure we have all required columns in the right order
        required_columns = ['phase', 'total_bets', 'total_wins', 'win_rate']
        
        # Ensure win_rate is in decimal format for consistency
        if 'win_rate' in self.phase_performance.columns:
            if self.phase_performance['win_rate'].max() > 1:
                self.phase_performance['win_rate'] = self.phase_performance['win_rate'] / 100
        
        # Select only required columns in the right order
        self.phase_performance = self.phase_performance[required_columns]
        
        # Save to CSV
        self.phase_performance.to_csv('output/backtest_by_phase.csv', index=False)
        print(f"\n✓ Updated phase performance saved to: output/backtest_by_phase.csv")
        
    def print_summary(self):
        """Print detailed summary of updates."""
        
        print("\n" + "="*70)
        print("PHASE PERFORMANCE UPDATE SUMMARY")
        print("="*70)
        print(f"Update Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Today's results
        print("\n📈 TODAY'S BETTING RESULTS BY PHASE:")
        print("-"*70)
        print(f"{'Phase':<15} {'New Bets':<12} {'New Wins':<12} {'Today Win %':<15}")
        print("-"*70)
        
        total_new_bets = 0
        total_new_wins = 0
        
        for phase in sorted(self.today_summary.keys()):
            stats = self.today_summary[phase]
            today_win_pct = stats['today_win_rate'] * 100
            print(f"{phase:<15} {stats['new_bets']:<12} {stats['new_wins']:<12} {today_win_pct:<15.1f}")
            total_new_bets += stats['new_bets']
            total_new_wins += stats['new_wins']
            
        print("-"*70)
        overall_today = (total_new_wins / total_new_bets * 100) if total_new_bets > 0 else 0
        print(f"{'TOTAL':<15} {total_new_bets:<12} {total_new_wins:<12} {overall_today:<15.1f}")
        
        # Updated cumulative stats
        print("\n\n📊 UPDATED CUMULATIVE PHASE PERFORMANCE:")
        print("-"*70)
        print(f"{'Phase':<15} {'Total Bets':<12} {'Total Wins':<12} {'Win Rate %':<15} {'Status':<20}")
        print("-"*70)
        
        for _, row in self.phase_performance.iterrows():
            phase = row['phase']
            total_bets = int(row['total_bets'])
            total_wins = int(row['total_wins'])
            win_rate = row['win_rate']
            
            # Convert to percentage if needed
            if win_rate <= 1:
                win_rate = win_rate * 100
            
            # Determine confidence status
            if win_rate >= 70 and total_bets >= 30:
                status = "✅ HIGH confidence"
            elif win_rate >= 60 and total_bets >= 20:
                status = "🟨 MEDIUM confidence"
            else:
                status = "🔴 LOW confidence"
                
            print(f"{phase:<15} {total_bets:<12} {total_wins:<12} {win_rate:<15.1f} {status:<20}")
            
        # Confidence changes
        if self.confidence_changes:
            print("\n\n🚨 CONFIDENCE LEVEL CHANGES:")
            print("-"*70)
            for change in self.confidence_changes:
                print(f"▸ {change['phase'].upper()}: {change['change']}")
                print(f"  → {change['new_total']} total bets, {change['win_rate']*100:.1f}% win rate")
        else:
            print("\n\n✓ No phases crossed confidence thresholds today")
            
        # Overall stats
        total_all_bets = self.phase_performance['total_bets'].sum()
        total_all_wins = self.phase_performance['total_wins'].sum()
        overall_win_rate = (total_all_wins / total_all_bets * 100) if total_all_bets > 0 else 0
        
        print(f"\n\n📈 OVERALL SYSTEM PERFORMANCE:")
        print(f"Total Historical Bets: {total_all_bets}")
        print(f"Total Historical Wins: {total_all_wins}")
        print(f"Overall Win Rate: {overall_win_rate:.1f}%")
        
        print("\n" + "="*70)
        
    def run(self):
        """Execute the full performance update pipeline."""
        print("🔄 Starting Phase Performance Update...")
        
        # Load data
        self.load_data()
        
        # Calculate today's performance
        self.calculate_today_performance()
        
        # Update cumulative stats
        self.update_cumulative_performance()
        
        # Save results
        self.save_updated_performance()
        
        # Print summary
        self.print_summary()
        
        print("\n✅ Phase Performance Update Complete!")
        print("→ Run phase_risk_adapter.py to apply updated confidence levels to future bets")


def main():
    """Main execution function."""
    updater = PhasePerformanceUpdater()
    updater.run()


if __name__ == "__main__":
    main()