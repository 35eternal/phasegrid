#!/usr/bin/env python3
"""
Phase Risk Adapter Module
Dynamically adjusts betting risk based on historical phase performance data.
"""

import pandas as pd
import numpy as np
from pathlib import Path


class PhaseRiskAdapter:
    """Adapts betting risk based on historical phase performance."""
    
    def __init__(self):
        self.phase_stats = None
        self.risk_stats = None
        self.current_bets = None
        self.phase_divisor_map = {}
        self.adjustment_summary = {}
        
    def load_data(self):
        """Load required CSV files."""
        try:
            # Load phase performance data
            self.phase_stats = pd.read_csv('output/backtest_by_phase.csv')
            print(f"✓ Loaded phase stats: {len(self.phase_stats)} phases")
            
            # Load risk performance data (for potential future use)
            self.risk_stats = pd.read_csv('output/backtest_by_risk.csv')
            print(f"✓ Loaded risk stats: {len(self.risk_stats)} risk levels")
            
            # Load current betting card
            self.current_bets = pd.read_csv('output/daily_betting_card_adjusted.csv')
            print(f"✓ Loaded current bets: {len(self.current_bets)} bets")
            
        except FileNotFoundError as e:
            print(f"❌ Error loading files: {e}")
            raise
            
    def calculate_phase_divisors(self):
        """Calculate divisors for each phase based on win rate and sample size."""
        
        # Ensure phase column exists and is lowercase
        if 'phase' in self.phase_stats.columns:
            self.phase_stats['phase'] = self.phase_stats['phase'].str.lower()
        elif 'Phase' in self.phase_stats.columns:
            self.phase_stats.rename(columns={'Phase': 'phase'}, inplace=True)
            self.phase_stats['phase'] = self.phase_stats['phase'].str.lower()
            
        # Process each phase
        for _, row in self.phase_stats.iterrows():
            phase = row['phase']
            
            # Extract win rate and sample size
            win_rate = row.get('win_rate', row.get('Win Rate', 0))
            sample_size = row.get('total_bets', row.get('Total Bets', 0))
            
            # Convert win rate to percentage if needed
            if win_rate <= 1:
                win_rate *= 100
                
            # Apply divisor rules (adjusted for small samples)
            if win_rate >= 70 and sample_size >= 4:
                divisor = 3
                confidence = "HIGH"
            elif win_rate >= 60 and sample_size >= 3:
                divisor = 5
                confidence = "MEDIUM"
            else:
                divisor = 10
                confidence = "LOW"
                
            self.phase_divisor_map[phase] = {
                'divisor': divisor,
                'win_rate': win_rate,
                'sample_size': sample_size,
                'confidence': confidence
            }
            
        # Add default for missing phases
        self.phase_divisor_map['default'] = {
            'divisor': 10,
            'win_rate': 0,
            'sample_size': 0,
            'confidence': 'FALLBACK'
        }
        
    def adjust_betting_card(self):
        """Adjust kelly_used and bet_percentage based on phase divisors."""
        
        # Ensure phase column exists and is lowercase
        if 'phase' in self.current_bets.columns:
            self.current_bets['phase'] = self.current_bets['phase'].str.lower()
        elif 'Phase' in self.current_bets.columns:
            self.current_bets.rename(columns={'Phase': 'phase'}, inplace=True)
            self.current_bets['phase'] = self.current_bets['phase'].str.lower()
        elif 'adv_phase' in self.current_bets.columns:
            self.current_bets['phase'] = self.current_bets['adv_phase'].str.lower()
        else:
            print("⚠️  Warning: No phase column found, using 'unknown' for all bets")
            self.current_bets['phase'] = 'unknown'
            
        # Debug: print unique phases found
        print(f"\nUnique phases in betting card: {self.current_bets['phase'].unique()}")
            
        # Debug: print unique phases found
        print(f"\nUnique phases in betting card: {self.current_bets['phase'].unique()}")
            
        # Initialize tracking
        adjustments_by_phase = {}
        
        # Process each bet
        for idx, row in self.current_bets.iterrows():
            phase = row.get('phase', 'unknown')
            
            # Get divisor for this phase
            phase_info = self.phase_divisor_map.get(phase, self.phase_divisor_map['default'])
            divisor = phase_info['divisor']
            
            # Track original values
            original_kelly = row.get('kelly_used', row.get('Kelly Used', 0.25))
            
            # Calculate new kelly_used based on divisor
            # If divisor = 3, use more Kelly (divide by smaller number)
            # If divisor = 10, use less Kelly (divide by larger number)
            new_kelly = 1.0 / divisor
            
            # Update values
            self.current_bets.at[idx, 'kelly_used'] = new_kelly
            
            # Recalculate bet percentage if needed
            if 'bet_percentage' in self.current_bets.columns:
                # Assuming bet_percentage = kelly_used * edge * bankroll_fraction
                # We'll scale it proportionally
                original_bet_pct = row.get('bet_percentage', 0)
                if original_kelly > 0:
                    scaling_factor = new_kelly / original_kelly
                    new_bet_pct = original_bet_pct * scaling_factor
                else:
                    new_bet_pct = new_kelly * 0.01  # Default 1% of Kelly
                    
                self.current_bets.at[idx, 'bet_percentage'] = new_bet_pct
            
            # Track adjustments
            if phase not in adjustments_by_phase:
                adjustments_by_phase[phase] = {
                    'count': 0,
                    'divisor': divisor,
                    'confidence': phase_info['confidence'],
                    'win_rate': phase_info['win_rate'],
                    'sample_size': phase_info['sample_size']
                }
            adjustments_by_phase[phase]['count'] += 1
            
        self.adjustment_summary = adjustments_by_phase
        
    def save_results(self):
        """Save the adjusted betting card."""
        output_path = 'output/final_betting_card.csv'
        self.current_bets.to_csv(output_path, index=False)
        print(f"\n✓ Saved final betting card to: {output_path}")
        
    def print_summary(self):
        """Print summary of adjustments made."""
        print("\n" + "="*60)
        print("PHASE RISK ADAPTATION SUMMARY")
        print("="*60)
        
        # Print phase divisor map
        print("\nPHASE DIVISOR MAPPING:")
        print("-"*60)
        print(f"{'Phase':<15} {'Divisor':<10} {'Win Rate':<12} {'Samples':<10} {'Confidence':<12}")
        print("-"*60)
        
        for phase, info in sorted(self.phase_divisor_map.items()):
            if phase != 'default':
                print(f"{phase:<15} {info['divisor']:<10} "
                      f"{info['win_rate']:<12.1f} {info['sample_size']:<10} "
                      f"{info['confidence']:<12}")
        
        # Print adjustment summary
        print("\n\nADJUSTMENTS BY PHASE:")
        print("-"*60)
        print(f"{'Phase':<15} {'Bets Adjusted':<15} {'Kelly Divisor':<15}")
        print("-"*60)
        
        total_adjusted = 0
        for phase, stats in sorted(self.adjustment_summary.items()):
            print(f"{phase:<15} {stats['count']:<15} {stats['divisor']:<15}")
            total_adjusted += stats['count']
            
        print("-"*60)
        print(f"{'TOTAL':<15} {total_adjusted:<15}")
        
        # Print risk level distribution
        print("\n\nRISK LEVEL DISTRIBUTION:")
        print("-"*60)
        
        risk_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'FALLBACK': 0}
        for phase, stats in self.adjustment_summary.items():
            risk_counts[stats['confidence']] += stats['count']
            
        for risk, count in risk_counts.items():
            if count > 0:
                pct = (count / total_adjusted) * 100
                print(f"{risk:<15} {count:<10} ({pct:.1f}%)")
                
        print("="*60)
        
    def run(self):
        """Execute the full phase risk adaptation pipeline."""
        print("Starting Phase Risk Adaptation...")
        
        # Load data
        self.load_data()
        
        # Calculate phase divisors
        self.calculate_phase_divisors()
        
        # Adjust betting card
        self.adjust_betting_card()
        
        # Save results
        self.save_results()
        
        # Print summary
        self.print_summary()
        
        print("\n✅ Phase Risk Adaptation Complete!")


def main():
    """Main execution function."""
    adapter = PhaseRiskAdapter()
    adapter.run()


if __name__ == "__main__":
    main()