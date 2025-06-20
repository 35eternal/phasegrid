#!/usr/bin/env python3
"""
Phase Multiplier Engine - Dynamically calculates Kelly divisors based on phase performance.
Loads phase results, applies formulas from config, and outputs optimized divisors.
"""

import pandas as pd
import json
import os
import numpy as np
from datetime import datetime

class PhaseMultiplierEngine:
    def __init__(self, config_path='config/phase_kelly_divisors.json'):
        self.config_path = config_path
        self.config = self.load_config()
        self.phase_results = None
        self.kelly_divisors = {}
    
    def load_config(self):
        """Load phase Kelly divisor configuration."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                print(f"✅ Loaded config from: {self.config_path}")
                return config
        else:
            print(f"❌ Config file not found: {self.config_path}")
            return {}
    
    def load_phase_results(self, filepath='phase_results_tracker.csv'):
        """Load phase results tracking data."""
        if os.path.exists(filepath):
            self.phase_results = pd.read_csv(filepath)
            print(f"✅ Loaded phase results: {len(self.phase_results)} records")
            return True
        else:
            print(f"❌ Phase results file not found: {filepath}")
            return False
    
    def calculate_phase_stats(self):
        """Calculate win rate and bet count for each phase."""
        if self.phase_results is None or self.phase_results.empty:
            return {}
        
        stats = {}
        
        for phase in ['luteal', 'menstrual', 'follicular', 'ovulatory']:
            phase_data = self.phase_results[self.phase_results['phase'] == phase]
            
            if len(phase_data) > 0:
                # Calculate win rate
                if 'actual_result' in phase_data.columns:
                    wins = phase_data[phase_data['actual_result'] == 'win']
                    win_rate = len(wins) / len(phase_data)
                else:
                    # Fallback if actual_result not available
                    win_rate = 0.5
                
                stats[phase] = {
                    'bet_count': len(phase_data),
                    'win_rate': win_rate,
                    'wins': len(wins) if 'actual_result' in phase_data.columns else 0,
                    'losses': len(phase_data) - len(wins) if 'actual_result' in phase_data.columns else 0
                }
            else:
                stats[phase] = {
                    'bet_count': 0,
                    'win_rate': 0.5,  # Default
                    'wins': 0,
                    'losses': 0
                }
        
        return stats
    
    def apply_formula(self, formula_str, win_rate):
        """Safely evaluate formula string with win_rate variable."""
        try:
            # Create safe namespace for evaluation
            namespace = {
                'win_rate': win_rate,
                'max': max,
                'min': min,
                'round': round,
                'abs': abs,
                'sqrt': np.sqrt
            }
            
            # Evaluate formula
            result = eval(formula_str, {"__builtins__": {}}, namespace)
            return float(result)
        except Exception as e:
            print(f"❌ Error evaluating formula '{formula_str}': {e}")
            return 5.0  # Safe default
    
    def calculate_kelly_divisors(self, stats):
        """Calculate Kelly divisors for each phase based on config formulas."""
        divisors = {}
        
        for phase, config in self.config.items():
            phase_stats = stats.get(phase, {})
            win_rate = phase_stats.get('win_rate', 0.5)
            bet_count = phase_stats.get('bet_count', 0)
            
            # Check minimum bets requirement
            min_bets = config.get('minimum_bets', 20)
            
            if bet_count >= min_bets:
                # Apply formula
                formula = config.get('formula', 'max(5, round(1 / win_rate, 2))')
                divisor = self.apply_formula(formula, win_rate)
                confidence_level = 'PRODUCTION'
            else:
                # Not enough data - use conservative default
                divisor = 10.0
                confidence_level = 'INSUFFICIENT_DATA'
            
            divisors[phase] = {
                'kelly_divisor': divisor,
                'win_rate': round(win_rate, 4),
                'bet_count': bet_count,
                'confidence_level': confidence_level,
                'formula_used': config.get('formula', 'default'),
                'minimum_bets_met': bet_count >= min_bets
            }
        
        return divisors
    
    def generate_output(self, divisors):
        """Generate output CSV with dynamic Kelly divisors."""
        # Convert to DataFrame
        rows = []
        for phase, data in divisors.items():
            row = {
                'phase': phase,
                'kelly_divisor': data['kelly_divisor'],
                'win_rate': data['win_rate'],
                'bet_count': data['bet_count'],
                'confidence_level': data['confidence_level'],
                'formula_used': data['formula_used'],
                'minimum_bets_met': data['minimum_bets_met'],
                'timestamp': datetime.now().isoformat()
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # Save to output
        output_path = 'output/dynamic_kelly_divisors.csv'
        df.to_csv(output_path, index=False)
        print(f"\n✅ Saved dynamic Kelly divisors to: {output_path}")
        
        return df
    
    def generate_report(self, stats, divisors):
        """Generate detailed report of calculations."""
        print("\n" + "="*60)
        print("📊 PHASE MULTIPLIER ENGINE REPORT")
        print("="*60)
        
        for phase in ['luteal', 'menstrual', 'follicular', 'ovulatory']:
            print(f"\n🌙 {phase.upper()} PHASE:")
            
            # Stats
            phase_stats = stats.get(phase, {})
            print(f"  Bets: {phase_stats.get('bet_count', 0)}")
            print(f"  Win Rate: {phase_stats.get('win_rate', 0):.2%}")
            print(f"  Record: {phase_stats.get('wins', 0)}W - {phase_stats.get('losses', 0)}L")
            
            # Divisor
            phase_divisor = divisors.get(phase, {})
            print(f"  Kelly Divisor: {phase_divisor.get('kelly_divisor', 'N/A')}")
            print(f"  Confidence: {phase_divisor.get('confidence_level', 'N/A')}")
            
            # Formula
            if phase in self.config:
                print(f"  Formula: {self.config[phase].get('formula', 'N/A')}")
        
        print("\n" + "="*60)
    
    def run(self):
        """Execute the phase multiplier calculation pipeline."""
        print("🚀 Starting Phase Multiplier Engine...")
        
        # Load phase results
        if not self.load_phase_results():
            print("❌ Cannot proceed without phase results data")
            return None
        
        # Calculate stats
        stats = self.calculate_phase_stats()
        print(f"\n📈 Calculated stats for {len(stats)} phases")
        
        # Calculate divisors
        divisors = self.calculate_kelly_divisors(stats)
        self.kelly_divisors = divisors
        
        # Generate output
        output_df = self.generate_output(divisors)
        
        # Generate report
        self.generate_report(stats, divisors)
        
        return output_df

def main():
    """Run the phase multiplier engine."""
    engine = PhaseMultiplierEngine()
    result = engine.run()
    
    if result is not None:
        print("\n✅ Phase Multiplier Engine completed successfully!")
        print(f"   Output saved to: output/dynamic_kelly_divisors.csv")

if __name__ == "__main__":
    main()