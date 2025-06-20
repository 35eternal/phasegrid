"""
WNBA Daily Betting Dashboard
Complete system for daily betting management and tracking
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

class WNBABettingDashboard:
    def __init__(self):
        self.phase_win_rates = {
            'luteal': 0.80,
            'follicular': 0.67,
            'menstrual': 0.20,
            'ovulatory': 0.50
        }
        
        self.results_file = 'output/phase_results_tracker.csv'
        self.optimal_slate_file = 'output/optimal_betting_slate.csv'
        self.enhanced_card_file = 'output/daily_betting_card_adjusted.csv'
        
    def display_header(self):
        """Display dashboard header"""
        print("="*70)
        print("🏀 WNBA DAILY BETTING DASHBOARD 🏀".center(70))
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n".center(70))
        print("="*70)
    
    def load_optimal_slate(self):
        """Load and display today's optimal betting slate"""
        if not os.path.exists(self.optimal_slate_file):
            print("❌ No optimal slate found. Run enhancement pipeline first.")
            return None
            
        df = pd.read_csv(self.optimal_slate_file)
        
        print("\n📋 TODAY'S OPTIMAL BETTING SLATE")
        print("-"*70)
        
        # Add expected value calculation
        df['expected_win_rate'] = df['adv_phase'].map(self.phase_win_rates)
        df['expected_value'] = (
            df['kelly_used'] * df['actual_odds'] * df['expected_win_rate'] - 
            df['kelly_used'] * (1 - df['expected_win_rate'])
        ) * 100
        
        # Display bets
        display_cols = ['player_name', 'stat_type', 'line', 'kelly_used', 
                       'bet_percentage', 'adv_phase', 'expected_value']
        
        for idx, row in df.iterrows():
            print(f"\n{idx+1}. {row['player_name']} - {row['stat_type']}")
            print(f"   Line: {row['line']} | Kelly: {row['kelly_used']:.3f} ({row['bet_percentage']:.2f}%)")
            print(f"   Phase: {row['adv_phase']} | Expected Win Rate: {row['expected_win_rate']*100:.0f}%")
            print(f"   Expected Value: {row['expected_value']:+.3f}% of bankroll")
            if 'actual_odds' in row and row['actual_odds'] != 0.9:
                print(f"   Odds: {row['actual_odds']:.3f} ({int(-100/row['actual_odds']) if row['actual_odds'] < 1 else f'+{int((row['actual_odds']-1)*100)}'})")
        
        # Summary statistics
        print("\n" + "-"*70)
        print("SLATE SUMMARY:")
        print(f"Total Bets: {len(df)}")
        print(f"Total Exposure: {df['bet_percentage'].sum():.2f}% of bankroll")
        print(f"Expected Value: {df['expected_value'].sum():+.3f}% of bankroll")
        
        # Phase breakdown
        phase_counts = df['adv_phase'].value_counts()
        print("\nPhase Distribution:")
        for phase, count in phase_counts.items():
            win_rate = self.phase_win_rates.get(phase, 0.5)
            print(f"  {phase}: {count} bets ({count/len(df)*100:.0f}%) - {win_rate*100:.0f}% win rate")
        
        return df
    
    def analyze_historical_performance(self):
        """Analyze historical betting performance by phase"""
        if not os.path.exists(self.results_file):
            print("\n📊 No historical data yet. Start tracking results!")
            return
        
        df = pd.read_csv(self.results_file)
        
        print("\n📈 HISTORICAL PERFORMANCE ANALYSIS")
        print("-"*70)
        
        # Overall performance
        total_bets = len(df)
        wins = len(df[df['Result'] == 'W'])
        win_rate = wins / total_bets if total_bets > 0 else 0
        
        print(f"Total Bets: {total_bets}")
        print(f"Overall Win Rate: {win_rate*100:.1f}% ({wins}W-{total_bets-wins}L)")
        
        # Performance by phase
        print("\nPerformance by Phase:")
        for phase in ['luteal', 'follicular', 'ovulatory', 'menstrual']:
            phase_df = df[df['Phase'] == phase]
            if len(phase_df) > 0:
                phase_wins = len(phase_df[phase_df['Result'] == 'W'])
                phase_win_rate = phase_wins / len(phase_df)
                expected_rate = self.phase_win_rates[phase]
                
                print(f"\n{phase.upper()}:")
                print(f"  Actual: {phase_win_rate*100:.1f}% ({phase_wins}W-{len(phase_df)-phase_wins}L)")
                print(f"  Expected: {expected_rate*100:.0f}%")
                print(f"  Difference: {(phase_win_rate - expected_rate)*100:+.1f}%")
                
                # Calculate ROI
                phase_roi = phase_df['Payout'].str.replace('+', '').astype(float).sum()
                print(f"  ROI: {phase_roi:+.3f} units")
    
    def add_result(self, player, stat, phase, kelly, result, payout):
        """Add a new betting result"""
        new_result = {
            'Date': datetime.now().strftime('%Y-%m-%d'),
            'Player': player,
            'Stat': stat,
            'Phase': phase,
            'Kelly': kelly,
            'Result': result,
            'Payout': payout
        }
        
        if os.path.exists(self.results_file):
            df = pd.read_csv(self.results_file)
        else:
            df = pd.DataFrame(columns=['Date', 'Player', 'Stat', 'Phase', 'Kelly', 'Result', 'Payout'])
        
        df = pd.concat([df, pd.DataFrame([new_result])], ignore_index=True)
        df.to_csv(self.results_file, index=False)
        
        print(f"✅ Result added: {player} - {stat} ({phase}) - {result}")
    
    def quick_add_results(self):
        """Interactive result entry"""
        print("\n📝 QUICK RESULT ENTRY")
        print("-"*70)
        print("Enter betting results (or 'done' to finish):")
        
        while True:
            entry = input("\nFormat: Player,Stat,Phase,Kelly,W/L,Payout (or 'done'): ")
            if entry.lower() == 'done':
                break
            
            try:
                parts = entry.split(',')
                if len(parts) == 6:
                    self.add_result(*[p.strip() for p in parts])
                else:
                    print("❌ Invalid format. Use: Player,Stat,Phase,Kelly,W/L,Payout")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def calculate_kelly_adjustments(self):
        """Suggest Kelly divisor adjustments based on actual performance"""
        if not os.path.exists(self.results_file):
            return
        
        df = pd.read_csv(self.results_file)
        
        print("\n🔧 SUGGESTED KELLY ADJUSTMENTS")
        print("-"*70)
        
        current_divisors = {
            'luteal': 3,
            'follicular': 5,
            'menstrual': 10,
            'ovulatory': 5
        }
        
        for phase in current_divisors:
            phase_df = df[df['Phase'] == phase]
            if len(phase_df) >= 10:  # Need sufficient sample
                actual_win_rate = len(phase_df[phase_df['Result'] == 'W']) / len(phase_df)
                expected_win_rate = self.phase_win_rates[phase]
                
                # Adjust divisor based on performance
                if actual_win_rate > expected_win_rate * 1.1:
                    new_divisor = max(2, current_divisors[phase] - 1)
                    print(f"{phase}: Consider reducing divisor {current_divisors[phase]} → {new_divisor} (outperforming)")
                elif actual_win_rate < expected_win_rate * 0.9:
                    new_divisor = min(15, current_divisors[phase] + 2)
                    print(f"{phase}: Consider increasing divisor {current_divisors[phase]} → {new_divisor} (underperforming)")
                else:
                    print(f"{phase}: Keep current divisor of {current_divisors[phase]} (performing as expected)")
    
    def generate_betting_slip(self):
        """Generate a betting slip for easy entry"""
        if not os.path.exists(self.optimal_slate_file):
            return
        
        df = pd.read_csv(self.optimal_slate_file)
        
        slip_content = f"WNBA BETTING SLIP - {datetime.now().strftime('%Y-%m-%d')}\n"
        slip_content += "="*50 + "\n\n"
        
        for idx, row in df.iterrows():
            slip_content += f"{idx+1}. {row['player_name']} {row['stat_type']} "
            slip_content += f"{'Over' if row.get('pred_outcome', 'over') == 'over' else 'Under'} {row['line']}\n"
            slip_content += f"   Bet: {row['bet_percentage']:.2f}% of bankroll\n\n"
        
        slip_content += f"\nTotal Exposure: {df['bet_percentage'].sum():.2f}%\n"
        
        with open('output/betting_slip_today.txt', 'w') as f:
            f.write(slip_content)
        
        print("\n✅ Betting slip saved to: output/betting_slip_today.txt")
        
    def run_dashboard(self):
        """Run the complete dashboard"""
        self.display_header()
        
        # Load and display optimal slate
        slate = self.load_optimal_slate()
        
        # Show historical performance
        self.analyze_historical_performance()
        
        # Show Kelly adjustments
        self.calculate_kelly_adjustments()
        
        # Generate betting slip
        if slate is not None:
            self.generate_betting_slip()
        
        # Options menu
        print("\n" + "="*70)
        print("OPTIONS:")
        print("1. Add betting results")
        print("2. Regenerate optimal slate")
        print("3. View full enhanced card")
        print("4. Export reports")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ")
        
        if choice == '1':
            self.quick_add_results()
        elif choice == '2':
            os.system('python scripts/phase_risk_analyzer.py')
        elif choice == '3':
            df = pd.read_csv(self.enhanced_card_file)
            print(df[['player_name', 'stat_type', 'kelly_used', 'adv_phase', 'actual_odds']].head(20))
        elif choice == '4':
            self.export_reports()
    
    def export_reports(self):
        """Export comprehensive reports"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create report content
        report = {
            'timestamp': timestamp,
            'optimal_slate': pd.read_csv(self.optimal_slate_file).to_dict('records') if os.path.exists(self.optimal_slate_file) else [],
            'historical_results': pd.read_csv(self.results_file).to_dict('records') if os.path.exists(self.results_file) else [],
            'phase_performance': {}
        }
        
        # Calculate phase performance
        if os.path.exists(self.results_file):
            df = pd.read_csv(self.results_file)
            for phase in self.phase_win_rates:
                phase_df = df[df['Phase'] == phase]
                if len(phase_df) > 0:
                    wins = len(phase_df[phase_df['Result'] == 'W'])
                    report['phase_performance'][phase] = {
                        'bets': len(phase_df),
                        'wins': wins,
                        'win_rate': wins / len(phase_df),
                        'expected_rate': self.phase_win_rates[phase]
                    }
        
        # Save report
        with open(f'output/betting_report_{timestamp}.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Report exported to: output/betting_report_{timestamp}.json")


def main():
    dashboard = WNBABettingDashboard()
    dashboard.run_dashboard()


if __name__ == "__main__":
    main()