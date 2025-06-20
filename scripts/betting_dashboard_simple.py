import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

class WNBABettingDashboard:
    def __init__(self):
        self.phase_win_rates = {
            "luteal": 0.80,
            "follicular": 0.67,
            "menstrual": 0.20,
            "ovulatory": 0.50
        }
        
        self.results_file = "output/phase_results_tracker.csv"
        self.optimal_slate_file = "output/optimal_betting_slate.csv"
        self.enhanced_card_file = "output/daily_betting_card_adjusted.csv"
        
    def display_header(self):
        """Display dashboard header"""
        print("="*70)
        print("WNBA DAILY BETTING DASHBOARD".center(70))
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}".center(70))
        print("="*70)
    
    def load_optimal_slate(self):
        """Load and display today's optimal betting slate"""
        if not os.path.exists(self.optimal_slate_file):
            print("No optimal slate found. Run enhancement pipeline first.")
            return None
            
        df = pd.read_csv(self.optimal_slate_file)
        
        print("\nTODAY'S OPTIMAL BETTING SLATE")
        print("-"*70)
        
        # Add expected value calculation
        df["expected_win_rate"] = df["adv_phase"].map(self.phase_win_rates)
        df["expected_value"] = (
            df["kelly_used"] * df["actual_odds"] * df["expected_win_rate"] - 
            df["kelly_used"] * (1 - df["expected_win_rate"])
        ) * 100
        
        # Display bets
        for idx, row in df.iterrows():
            print(f"\n{idx+1}. {row['player_name']} - {row['stat_type']}")
            print(f"   Line: {row['line']} | Kelly: {row['kelly_used']:.3f} ({row['bet_percentage']:.2f}%)")
            print(f"   Phase: {row['adv_phase']} | Expected Win Rate: {row['expected_win_rate']*100:.0f}%")
            print(f"   Expected Value: {row['expected_value']:+.3f}% of bankroll")
        
        # Summary statistics
        print("\n" + "-"*70)
        print("SLATE SUMMARY:")
        print(f"Total Bets: {len(df)}")
        print(f"Total Exposure: {df['bet_percentage'].sum():.2f}% of bankroll")
        print(f"Expected Value: {df['expected_value'].sum():+.3f}% of bankroll")
        
        # Phase breakdown
        phase_counts = df["adv_phase"].value_counts()
        print("\nPhase Distribution:")
        for phase, count in phase_counts.items():
            win_rate = self.phase_win_rates.get(phase, 0.5)
            print(f"  {phase}: {count} bets ({count/len(df)*100:.0f}%) - {win_rate*100:.0f}% win rate")
        
        return df
    
    def analyze_historical_performance(self):
        """Analyze historical betting performance by phase"""
        if not os.path.exists(self.results_file):
            print("\nNo historical data yet. Start tracking results!")
            return
        
        df = pd.read_csv(self.results_file)
        
        print("\nHISTORICAL PERFORMANCE ANALYSIS")
        print("-"*70)
        
        # Overall performance
        total_bets = len(df)
        wins = len(df[df["Result"] == "W"])
        win_rate = wins / total_bets if total_bets > 0 else 0
        
        print(f"Total Bets: {total_bets}")
        print(f"Overall Win Rate: {win_rate*100:.1f}% ({wins}W-{total_bets-wins}L)")
        
        # Performance by phase
        print("\nPerformance by Phase:")
        for phase in ["luteal", "follicular", "ovulatory", "menstrual"]:
            phase_df = df[df["Phase"] == phase]
            if len(phase_df) > 0:
                phase_wins = len(phase_df[phase_df["Result"] == "W"])
                phase_win_rate = phase_wins / len(phase_df)
                expected_rate = self.phase_win_rates[phase]
                
                print(f"\n{phase.upper()}:")
                print(f"  Actual: {phase_win_rate*100:.1f}% ({phase_wins}W-{len(phase_df)-phase_wins}L)")
                print(f"  Expected: {expected_rate*100:.0f}%")
                print(f"  Difference: {(phase_win_rate - expected_rate)*100:+.1f}%")
                
                # Calculate ROI - FIXED VERSION
                try:
                    phase_roi = phase_df["Payout"].astype(float).sum()
                except:
                    phase_roi = 0.0
                print(f"  ROI: {phase_roi:+.3f} units")
    
    def generate_betting_slip(self):
        """Generate a betting slip for easy entry"""
        if not os.path.exists(self.optimal_slate_file):
            return
        
        df = pd.read_csv(self.optimal_slate_file)
        
        slip_content = f"WNBA BETTING SLIP - {datetime.now().strftime('%Y-%m-%d')}\n"
        slip_content += "="*50 + "\n\n"
        
        for idx, row in df.iterrows():
            slip_content += f"{idx+1}. {row['player_name']} {row['stat_type']} "
            slip_content += f"Over {row['line']}\n"
            slip_content += f"   Bet: {row['bet_percentage']:.2f}% of bankroll\n\n"
        
        slip_content += f"\nTotal Exposure: {df['bet_percentage'].sum():.2f}%\n"
        
        with open("output/betting_slip_today.txt", "w") as f:
            f.write(slip_content)
        
        print("\nBetting slip saved to: output/betting_slip_today.txt")
        
    def run_dashboard(self):
        """Run the complete dashboard"""
        self.display_header()
        
        # Load and display optimal slate
        slate = self.load_optimal_slate()
        
        # Show historical performance
        self.analyze_historical_performance()
        
        # Generate betting slip
        if slate is not None:
            self.generate_betting_slip()
        
        print("\n" + "="*70)

if __name__ == "__main__":
    dashboard = WNBABettingDashboard()
    dashboard.run_dashboard()
