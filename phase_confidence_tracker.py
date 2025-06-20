#!/usr/bin/env python3
"""
Phase Confidence Tracker Module
Tracks and visualizes the evolution of phase confidence levels over time.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path


class PhaseConfidenceTracker:
    """Tracks confidence level evolution for each menstrual phase."""
    
    def __init__(self):
        self.phase_data = None
        self.confidence_log = None
        self.today = date.today().strftime('%Y-%m-%d')
        self.confidence_changes = []
        self.log_file_path = 'output/phase_confidence_log.csv'
        
    def load_phase_data(self):
        """Load current phase performance data."""
        try:
            self.phase_data = pd.read_csv('output/backtest_by_phase.csv')
            print(f"✓ Loaded phase performance data: {len(self.phase_data)} phases")
            
            # Ensure phase names are lowercase
            self.phase_data['phase'] = self.phase_data['phase'].str.lower()
            
        except FileNotFoundError as e:
            print(f"❌ Error loading backtest_by_phase.csv: {e}")
            raise
            
    def load_confidence_log(self):
        """Load existing confidence log or create new one."""
        try:
            self.confidence_log = pd.read_csv(self.log_file_path)
            print(f"✓ Loaded confidence log: {len(self.confidence_log)} historical entries")
        except FileNotFoundError:
            # Create new log file
            self.confidence_log = pd.DataFrame(columns=[
                'date', 'phase', 'total_bets', 'total_wins', 'win_rate', 'confidence_status'
            ])
            print("📝 Creating new confidence log file")
            
    def determine_confidence_status(self, total_bets, win_rate):
        """Determine confidence status based on bets and win rate."""
        # Ensure win_rate is in decimal format
        if win_rate > 1:
            win_rate = win_rate / 100
            
        if total_bets < 20 or win_rate < 0.6:
            return 'LOW'
        elif total_bets >= 20 and 0.6 <= win_rate < 0.7:
            return 'MEDIUM'
        elif total_bets >= 20 and win_rate >= 0.7:
            return 'HIGH'
        else:
            return 'LOW'
            
    def update_confidence_log(self):
        """Add today's confidence status for each phase."""
        new_entries = []
        
        for _, row in self.phase_data.iterrows():
            phase = row['phase']
            total_bets = int(row['total_bets'])
            total_wins = int(row['total_wins'])
            win_rate = row['win_rate']
            
            # Ensure win_rate is in decimal format
            if win_rate > 1:
                win_rate = win_rate / 100
                
            # Determine confidence status
            confidence_status = self.determine_confidence_status(total_bets, win_rate)
            
            # Check if entry already exists for today
            existing_entry = self.confidence_log[
                (self.confidence_log['date'] == self.today) & 
                (self.confidence_log['phase'] == phase)
            ]
            
            if existing_entry.empty:
                # Add new entry
                new_entry = {
                    'date': self.today,
                    'phase': phase,
                    'total_bets': total_bets,
                    'total_wins': total_wins,
                    'win_rate': win_rate,
                    'confidence_status': confidence_status
                }
                new_entries.append(new_entry)
                
                # Check for confidence level changes
                self.check_confidence_change(phase, confidence_status)
            else:
                print(f"  ℹ️  Entry already exists for {phase} on {self.today}")
                
        # Append new entries
        if new_entries:
            new_df = pd.DataFrame(new_entries)
            self.confidence_log = pd.concat([self.confidence_log, new_df], ignore_index=True)
            print(f"✓ Added {len(new_entries)} new confidence entries for {self.today}")
            
    def check_confidence_change(self, phase, new_status):
        """Check if confidence level changed from previous entry."""
        # Get previous entries for this phase
        phase_history = self.confidence_log[self.confidence_log['phase'] == phase]
        
        if not phase_history.empty:
            # Get most recent entry
            last_entry = phase_history.iloc[-1]
            last_status = last_entry['confidence_status']
            
            if last_status != new_status:
                # Determine if upgrade or downgrade
                status_order = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
                
                if status_order[new_status] > status_order[last_status]:
                    change_type = '⬆️ UPGRADE'
                    emoji = '🎉'
                else:
                    change_type = '⬇️ DOWNGRADE'
                    emoji = '⚠️'
                    
                self.confidence_changes.append({
                    'phase': phase,
                    'change': f"{last_status} → {new_status}",
                    'type': change_type,
                    'emoji': emoji,
                    'date': self.today
                })
                
    def save_confidence_log(self):
        """Save updated confidence log to CSV."""
        # Sort by date and phase for better readability
        self.confidence_log = self.confidence_log.sort_values(['date', 'phase'])
        self.confidence_log.to_csv(self.log_file_path, index=False)
        print(f"✓ Saved confidence log to: {self.log_file_path}")
        
    def print_summary_report(self):
        """Print comprehensive summary of confidence evolution."""
        print("\n" + "="*80)
        print("PHASE CONFIDENCE TRACKER REPORT")
        print("="*80)
        print(f"Report Date: {self.today}")
        
        # Level changes
        if self.confidence_changes:
            print("\n🚨 CONFIDENCE LEVEL CHANGES TODAY:")
            print("-"*80)
            for change in self.confidence_changes:
                print(f"{change['emoji']} {change['phase'].upper()}: {change['change']} ({change['type']})")
        else:
            print("\n✓ No confidence level changes today")
            
        # Current status summary
        print("\n\n📊 CURRENT CONFIDENCE STATUS:")
        print("-"*80)
        print(f"{'Phase':<15} {'Status':<12} {'Total Bets':<12} {'Win Rate':<12} {'Progress to Next':<20}")
        print("-"*80)
        
        for _, row in self.phase_data.iterrows():
            phase = row['phase']
            total_bets = int(row['total_bets'])
            total_wins = int(row['total_wins'])
            win_rate = row['win_rate']
            
            # Ensure win_rate is in decimal format for display
            if win_rate > 1:
                win_rate = win_rate / 100
                
            status = self.determine_confidence_status(total_bets, win_rate)
            
            # Calculate progress to next level
            progress = self.calculate_progress_to_next(total_bets, win_rate, status)
            
            # Status emoji
            status_emoji = {'LOW': '🔴', 'MEDIUM': '🟨', 'HIGH': '✅'}
            
            print(f"{phase:<15} {status_emoji[status]} {status:<10} {total_bets:<12} "
                  f"{win_rate*100:<12.1f} {progress:<20}")
            
        # Recent history for each phase
        print("\n\n📈 RECENT CONFIDENCE HISTORY (Last 5 Entries Per Phase):")
        print("-"*80)
        
        phases = self.phase_data['phase'].unique()
        for phase in sorted(phases):
            phase_history = self.confidence_log[self.confidence_log['phase'] == phase].tail(5)
            
            if not phase_history.empty:
                print(f"\n{phase.upper()}:")
                print(f"{'Date':<12} {'Bets':<8} {'Wins':<8} {'Win%':<10} {'Status':<12}")
                print("-"*50)
                
                for _, entry in phase_history.iterrows():
                    win_pct = entry['win_rate'] * 100 if entry['win_rate'] <= 1 else entry['win_rate']
                    status_emoji = {'LOW': '🔴', 'MEDIUM': '🟨', 'HIGH': '✅'}
                    
                    print(f"{entry['date']:<12} {int(entry['total_bets']):<8} "
                          f"{int(entry['total_wins']):<8} {win_pct:<10.1f} "
                          f"{status_emoji[entry['confidence_status']]} {entry['confidence_status']:<10}")
                          
        # Statistical summary
        print("\n\n📊 STATISTICAL SUMMARY:")
        print("-"*80)
        
        # Overall stats
        total_bets_all = self.phase_data['total_bets'].sum()
        total_wins_all = self.phase_data['total_wins'].sum()
        overall_win_rate = (total_wins_all / total_bets_all * 100) if total_bets_all > 0 else 0
        
        print(f"Total Bets Across All Phases: {total_bets_all}")
        print(f"Total Wins Across All Phases: {total_wins_all}")
        print(f"Overall System Win Rate: {overall_win_rate:.1f}%")
        
        # Confidence distribution
        current_statuses = []
        for _, row in self.phase_data.iterrows():
            status = self.determine_confidence_status(row['total_bets'], row['win_rate'])
            current_statuses.append(status)
            
        print(f"\nConfidence Distribution:")
        for status in ['HIGH', 'MEDIUM', 'LOW']:
            count = current_statuses.count(status)
            pct = (count / len(current_statuses) * 100) if len(current_statuses) > 0 else 0
            print(f"  {status}: {count} phases ({pct:.0f}%)")
            
        print("\n" + "="*80)
        
    def calculate_progress_to_next(self, total_bets, win_rate, current_status):
        """Calculate progress towards next confidence level."""
        # Ensure win_rate is in decimal format
        if win_rate > 1:
            win_rate = win_rate / 100
            
        if current_status == 'LOW':
            if total_bets < 20:
                return f"Need {20 - total_bets} more bets"
            elif win_rate < 0.6:
                return f"Need {60 - win_rate*100:.1f}% more wins"
        elif current_status == 'MEDIUM':
            return f"Need {70 - win_rate*100:.1f}% win rate"
        elif current_status == 'HIGH':
            return "Max level! 🏆"
            
        return "—"
        
    def run(self):
        """Execute the confidence tracking pipeline."""
        print("🔍 Starting Phase Confidence Tracker...")
        
        # Load current phase data
        self.load_phase_data()
        
        # Load or create confidence log
        self.load_confidence_log()
        
        # Update log with today's data
        self.update_confidence_log()
        
        # Save updated log
        self.save_confidence_log()
        
        # Print summary report
        self.print_summary_report()
        
        print("\n✅ Phase Confidence Tracking Complete!")


def main():
    """Main execution function."""
    tracker = PhaseConfidenceTracker()
    tracker.run()


if __name__ == "__main__":
    main()