#!/usr/bin/env python3
"""
Phase Risk Adapter - Adjusts betting risk thresholds based on cycle phase.
Now with production/testing toggle for different threshold requirements.
"""

import pandas as pd
import numpy as np
from datetime import datetime

# CRITICAL TOGGLE: Set to True for production (20+ bets, strict WR)
# Set to False for testing (3-4 bets, relaxed WR)
USE_PRODUCTION_THRESHOLDS = False

class PhaseRiskAdapter:
    def __init__(self):
        self.production_mode = USE_PRODUCTION_THRESHOLDS
        self.thresholds = self._get_thresholds()
        self.phase_data = None
        
    def _get_thresholds(self):
        """Get appropriate thresholds based on mode."""
        if self.production_mode:
            # Production thresholds (30+ bets, 70%+ WR for HIGH)
            return {
                'HIGH': {
                    'min_bets': 30,
                    'min_win_rate': 0.70,
                    'kelly_multiplier': 1.2,
                    'max_exposure': 0.05  # 5% of bankroll
                },
                'MEDIUM': {
                    'min_bets': 20,
                    'min_win_rate': 0.60,
                    'kelly_multiplier': 1.0,
                    'max_exposure': 0.03  # 3% of bankroll
                },
                'LOW': {
                    'min_bets': 20,
                    'min_win_rate': 0.50,
                    'kelly_multiplier': 0.8,
                    'max_exposure': 0.02  # 2% of bankroll
                },
                'INSUFFICIENT': {
                    'min_bets': 0,
                    'min_win_rate': 0,
                    'kelly_multiplier': 0.5,
                    'max_exposure': 0.01  # 1% of bankroll
                }
            }
        else:
            # Test thresholds (3-4 bets, relaxed WR)
            return {
                'HIGH': {
                    'min_bets': 4,
                    'min_win_rate': 0.60,
                    'kelly_multiplier': 1.0,
                    'max_exposure': 0.03
                },
                'MEDIUM': {
                    'min_bets': 3,
                    'min_win_rate': 0.50,
                    'kelly_multiplier': 0.8,
                    'max_exposure': 0.02
                },
                'LOW': {
                    'min_bets': 2,
                    'min_win_rate': 0.40,
                    'kelly_multiplier': 0.6,
                    'max_exposure': 0.015
                },
                'INSUFFICIENT': {
                    'min_bets': 0,
                    'min_win_rate': 0,
                    'kelly_multiplier': 0.4,
                    'max_exposure': 0.01
                }
            }
    
    def load_phase_data(self, filepath='phase_results_tracker.csv'):
        """Load phase performance data."""
        try:
            self.phase_data = pd.read_csv(filepath)
            print(f"✅ Loaded phase data: {len(self.phase_data)} records")
            print(f"📊 Mode: {'PRODUCTION' if self.production_mode else 'TESTING'}")
            return True
        except Exception as e:
            print(f"❌ Error loading phase data: {e}")
            return False
    
    def calculate_phase_metrics(self, phase):
        """Calculate metrics for a specific phase."""
        if self.phase_data is None:
            return None
        
        phase_records = self.phase_data[self.phase_data['phase'] == phase]
        
        if len(phase_records) == 0:
            return {
                'phase': phase,
                'bet_count': 0,
                'win_rate': 0,
                'wins': 0,
                'losses': 0,
                'risk_level': 'INSUFFICIENT'
            }
        
        # Calculate win rate
        wins = len(phase_records[phase_records['actual_result'] == 'win'])
        losses = len(phase_records[phase_records['actual_result'] == 'loss'])
        total_resolved = wins + losses
        
        win_rate = wins / total_resolved if total_resolved > 0 else 0
        
        # Determine risk level
        risk_level = self._determine_risk_level(len(phase_records), win_rate)
        
        return {
            'phase': phase,
            'bet_count': len(phase_records),
            'win_rate': win_rate,
            'wins': wins,
            'losses': losses,
            'risk_level': risk_level
        }
    
    def _determine_risk_level(self, bet_count, win_rate):
        """Determine risk level based on thresholds."""
        for level in ['HIGH', 'MEDIUM', 'LOW']:
            threshold = self.thresholds[level]
            if (bet_count >= threshold['min_bets'] and 
                win_rate >= threshold['min_win_rate']):
                return level
        
        return 'INSUFFICIENT'
    
    def get_phase_adjustments(self, phase):
        """Get risk adjustments for a specific phase."""
        metrics = self.calculate_phase_metrics(phase)
        
        if metrics is None:
            return None
        
        risk_level = metrics['risk_level']
        threshold = self.thresholds[risk_level]
        
        adjustments = {
            'phase': phase,
            'risk_level': risk_level,
            'kelly_multiplier': threshold['kelly_multiplier'],
            'max_exposure': threshold['max_exposure'],
            'bet_count': metrics['bet_count'],
            'win_rate': metrics['win_rate'],
            'confidence_score': self._calculate_confidence_score(metrics)
        }
        
        return adjustments
    
    def _calculate_confidence_score(self, metrics):
        """Calculate confidence score (0-100) based on metrics."""
        # Base score from win rate (0-50 points)
        win_rate_score = min(metrics['win_rate'] * 50, 50)
        
        # Bet count score (0-50 points)
        if self.production_mode:
            bet_count_score = min(metrics['bet_count'] / 60 * 50, 50)
        else:
            bet_count_score = min(metrics['bet_count'] / 8 * 50, 50)
        
        return round(win_rate_score + bet_count_score, 1)
    
    def generate_risk_report(self):
        """Generate comprehensive risk report for all phases."""
        phases = ['luteal', 'menstrual', 'follicular', 'ovulatory']
        
        print("\n" + "="*60)
        print(f"🎯 PHASE RISK ADAPTER REPORT - {['TESTING', 'PRODUCTION'][self.production_mode]} MODE")
        print("="*60)
        
        report_data = []
        
        for phase in phases:
            adjustments = self.get_phase_adjustments(phase)
            
            if adjustments:
                report_data.append(adjustments)
                
                print(f"\n🌙 {phase.upper()} PHASE:")
                print(f"  Risk Level: {adjustments['risk_level']}")
                print(f"  Confidence: {adjustments['confidence_score']}/100")
                print(f"  Bet Count: {adjustments['bet_count']}")
                print(f"  Win Rate: {adjustments['win_rate']:.2%}")
                print(f"  Kelly Multiplier: {adjustments['kelly_multiplier']}x")
                print(f"  Max Exposure: {adjustments['max_exposure']:.1%}")
        
        # Summary
        print("\n" + "-"*60)
        print("📊 THRESHOLD REQUIREMENTS:")
        print(f"  Mode: {'PRODUCTION' if self.production_mode else 'TESTING'}")
        
        for level in ['HIGH', 'MEDIUM', 'LOW']:
            t = self.thresholds[level]
            print(f"  {level}: {t['min_bets']}+ bets, {t['min_win_rate']:.0%}+ WR")
        
        print("\n" + "="*60)
        
        # Save report
        df = pd.DataFrame(report_data)
        output_path = 'output/phase_risk_adjustments.csv'
        df.to_csv(output_path, index=False)
        print(f"\n📄 Risk adjustments saved to: {output_path}")
        
        return df
    
    def apply_risk_adjustment(self, bet_size, phase):
        """Apply risk adjustment to a proposed bet size."""
        adjustments = self.get_phase_adjustments(phase)
        
        if adjustments is None:
            return bet_size * 0.5  # Safety fallback
        
        # Apply Kelly multiplier
        adjusted_size = bet_size * adjustments['kelly_multiplier']
        
        # Apply max exposure cap
        max_allowed = adjustments['max_exposure']
        
        # Return minimum of adjusted size and max exposure
        return min(adjusted_size, max_allowed)

def main():
    """Run risk adapter analysis."""
    print("🚀 Starting Phase Risk Adapter...")
    
    adapter = PhaseRiskAdapter()
    
    # Load data
    if adapter.load_phase_data():
        # Generate report
        report = adapter.generate_risk_report()
        
        # Example usage
        print("\n💡 Example Risk Adjustments:")
        base_bet = 0.025  # 2.5% base Kelly
        
        for phase in ['luteal', 'menstrual', 'follicular', 'ovulatory']:
            adjusted = adapter.apply_risk_adjustment(base_bet, phase)
            print(f"  {phase}: {base_bet:.3f} → {adjusted:.3f} ({adjusted/base_bet:.1f}x)")
        
        print(f"\n✅ Risk adapter ready! Mode: {'PRODUCTION' if USE_PRODUCTION_THRESHOLDS else 'TESTING'}")

if __name__ == "__main__":
    main()