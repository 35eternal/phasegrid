#!/usr/bin/env python3
"""
Log Integrity Check - Validates betting data consistency across all tracking files.
Ensures all bets are properly tracked and resolved.
"""

import pandas as pd
import os
from collections import defaultdict

class LogIntegrityChecker:
    def __init__(self):
        self.issues = defaultdict(list)
        self.stats = {
            'total_bets': 0,
            'resolved_bets': 0,
            'unresolved_bets': 0,
            'duplicates': 0,
            'missing_in_phase_tracker': 0,
            'missing_in_backtest': 0
        }
    
    def load_data(self):
        """Load all relevant data files."""
        files = {
            'betting_card': 'daily_betting_card_adjusted.csv',
            'phase_tracker': 'phase_results_tracker.csv',
            'backtest': 'backtest_detailed.csv'
        }
        
        data = {}
        for key, filepath in files.items():
            if os.path.exists(filepath):
                try:
                    data[key] = pd.read_csv(filepath)
                    print(f"✅ Loaded: {filepath} ({len(data[key])} rows)")
                except Exception as e:
                    print(f"❌ Error loading {filepath}: {e}")
                    data[key] = pd.DataFrame()
            else:
                print(f"⚠️  File not found: {filepath}")
                data[key] = pd.DataFrame()
        
        return data
    
    def validate_betting_card(self, df):
        """Check betting card for required columns and duplicates."""
        required_columns = ['source_id', 'date', 'player', 'market', 'actual_result']
        
        # Check columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            self.issues['missing_columns'].append(f"Missing columns: {missing_cols}")
            return False
        
        # Check for duplicates
        duplicates = df[df.duplicated(subset=['source_id'], keep=False)]
        if not duplicates.empty:
            self.stats['duplicates'] = len(duplicates)
            dup_ids = duplicates['source_id'].tolist()
            self.issues['duplicates'].extend(dup_ids)
        
        # Count resolved vs unresolved
        self.stats['total_bets'] = len(df)
        resolved = df[df['actual_result'].notna()]
        unresolved = df[df['actual_result'].isna()]
        
        self.stats['resolved_bets'] = len(resolved)
        self.stats['unresolved_bets'] = len(unresolved)
        
        # Track unresolved bet IDs
        if not unresolved.empty:
            unresolved_ids = unresolved['source_id'].tolist()
            self.issues['unresolved_bets'].extend(unresolved_ids)
        
        return True
    
    def cross_check_phase_tracker(self, betting_df, phase_df):
        """Verify resolved bets exist in phase tracker."""
        if betting_df.empty or phase_df.empty:
            return
        
        resolved_bets = betting_df[betting_df['actual_result'].notna()]
        
        # Check if phase tracker has source_id column
        if 'source_id' in phase_df.columns:
            phase_source_ids = set(phase_df['source_id'].unique())
            
            for _, bet in resolved_bets.iterrows():
                if bet['source_id'] not in phase_source_ids:
                    self.stats['missing_in_phase_tracker'] += 1
                    self.issues['missing_phase_tracker'].append(bet['source_id'])
    
    def cross_check_backtest(self, betting_df, backtest_df):
        """Verify resolved bets exist in backtest results."""
        if betting_df.empty or backtest_df.empty:
            return
        
        resolved_bets = betting_df[betting_df['actual_result'].notna()]
        
        # Check if backtest has source_id column
        if 'source_id' in backtest_df.columns:
            backtest_source_ids = set(backtest_df['source_id'].unique())
            
            for _, bet in resolved_bets.iterrows():
                if bet['source_id'] not in backtest_source_ids:
                    self.stats['missing_in_backtest'] += 1
                    self.issues['missing_backtest'].append(bet['source_id'])
    
    def generate_report(self):
        """Generate integrity check summary."""
        print("\n" + "="*60)
        print("📊 LOG INTEGRITY CHECK SUMMARY")
        print("="*60)
        
        # Stats
        print("\n📈 STATISTICS:")
        print(f"  Total Bets: {self.stats['total_bets']}")
        print(f"  Resolved: {self.stats['resolved_bets']}")
        print(f"  Unresolved: {self.stats['unresolved_bets']}")
        print(f"  Duplicates: {self.stats['duplicates']}")
        
        # Cross-check results
        print("\n🔍 CROSS-CHECK RESULTS:")
        print(f"  Missing in Phase Tracker: {self.stats['missing_in_phase_tracker']}")
        print(f"  Missing in Backtest: {self.stats['missing_in_backtest']}")
        
        # Issues detail
        if any(self.issues.values()):
            print("\n⚠️  ISSUES FOUND:")
            
            if self.issues['duplicates']:
                print(f"\n  Duplicate Bet IDs ({len(self.issues['duplicates'])}):")
                for source_id in self.issues['duplicates'][:5]:  # Show first 5
                    print(f"    - {source_id}")
                if len(self.issues['duplicates']) > 5:
                    print(f"    ... and {len(self.issues['duplicates']) - 5} more")
            
            if self.issues['unresolved_bets']:
                print(f"\n  Unresolved Bets ({len(self.issues['unresolved_bets'])}):")
                for source_id in self.issues['unresolved_bets'][:5]:
                    print(f"    - {source_id}")
                if len(self.issues['unresolved_bets']) > 5:
                    print(f"    ... and {len(self.issues['unresolved_bets']) - 5} more")
            
            if self.issues['missing_phase_tracker']:
                print(f"\n  Missing from Phase Tracker ({len(self.issues['missing_phase_tracker'])}):")
                for source_id in self.issues['missing_phase_tracker'][:5]:
                    print(f"    - {source_id}")
            
            if self.issues['missing_backtest']:
                print(f"\n  Missing from Backtest ({len(self.issues['missing_backtest'])}):")
                for source_id in self.issues['missing_backtest'][:5]:
                    print(f"    - {source_id}")
        else:
            print("\n✅ No integrity issues found! All systems aligned.")
        
        print("\n" + "="*60)
        
        # Save detailed report
        self.save_detailed_report()
    
    def save_detailed_report(self):
        """Save detailed issues to file for review."""
        report_path = 'phase_logs/integrity_check_report.txt'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("LOG INTEGRITY CHECK DETAILED REPORT\n")
            f.write(f"Generated: {pd.Timestamp.now()}\n")
            f.write("="*60 + "\n\n")
            
            f.write("STATISTICS:\n")
            for key, value in self.stats.items():
                f.write(f"  {key}: {value}\n")
            
            f.write("\nDETAILED ISSUES:\n")
            for issue_type, source_ids in self.issues.items():
                if source_ids:
                    f.write(f"\n{issue_type.upper()}:\n")
                    for source_id in source_ids:
                        f.write(f"  - {source_id}\n")
        
        print(f"\n📄 Detailed report saved to: {report_path}")

def main():
    """Run integrity check."""
    print("🧪 Starting Log Integrity Check...")
    
    checker = LogIntegrityChecker()
    
    # Load data
    data = checker.load_data()
    
    # Validate betting card
    if 'betting_card' in data and not data['betting_card'].empty:
        if checker.validate_betting_card(data['betting_card']):
            # Cross-check with other files
            checker.cross_check_phase_tracker(
                data['betting_card'], 
                data.get('phase_tracker', pd.DataFrame())
            )
            checker.cross_check_backtest(
                data['betting_card'],
                data.get('backtest', pd.DataFrame())
            )
    
    # Generate report
    checker.generate_report()

if __name__ == "__main__":
    main()
