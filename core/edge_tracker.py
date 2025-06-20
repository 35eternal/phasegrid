import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

class EdgeTracker:
    """
    Tracks betting results and system performance over time.
    Provides insights on actual ROI vs predicted EV.
    """
    
    def __init__(self, tracking_file='data/betting_history.json'):
        self.tracking_file = tracking_file
        self.history = self.load_history()
        
    def load_history(self):
        """Load betting history from file."""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r') as f:
                    return json.load(f)
            except:
                return {'bets': [], 'sessions': []}
        return {'bets': [], 'sessions': []}
    
    def save_history(self):
        """Save betting history to file."""
        with open(self.tracking_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def add_bet(self, player, stat, line, recommendation, predicted_ev, 
                hit_probability, confidence, stake=1.0, odds=-110):
        """Add a new bet to tracking."""
        bet = {
            'id': len(self.history['bets']) + 1,
            'date': datetime.now().isoformat(),
            'player': player,
            'stat': stat,
            'line': line,
            'recommendation': recommendation,
            'predicted_ev': predicted_ev,
            'hit_probability': hit_probability,
            'confidence': confidence,
            'stake': stake,
            'odds': odds,
            'result': 'pending',
            'actual_value': None,
            'payout': None
        }
        
        self.history['bets'].append(bet)
        self.save_history()
        return bet['id']
    
    def update_bet_result(self, source_id, actual_value, hit=None):
        """Update a bet with its result."""
        for bet in self.history['bets']:
            if bet['id'] == source_id:
                bet['actual_value'] = actual_value
                
                # Determine if bet hit
                if hit is None:
                    if bet['recommendation'] == 'OVER' or bet['recommendation'] == 'STRONG OVER':
                        hit = actual_value > bet['line']
                    else:  # UNDER
                        hit = actual_value < bet['line']
                
                bet['result'] = 'win' if hit else 'loss'
                
                # Calculate payout
                if hit:
                    # Convert American odds to decimal
                    if bet['odds'] < 0:
                        decimal_odds = 1 + (100 / abs(bet['odds']))
                    else:
                        decimal_odds = 1 + (bet['odds'] / 100)
                    bet['payout'] = bet['stake'] * decimal_odds
                else:
                    bet['payout'] = 0
                
                self.save_history()
                return True
        return False
    
    def add_session_summary(self, date=None):
        """Add a betting session summary."""
        if date is None:
            date = datetime.now().date()
        
        # Get bets from this date
        session_bets = [
            bet for bet in self.history['bets'] 
            if bet['date'].startswith(str(date))
        ]
        
        if not session_bets:
            return None
        
        # Calculate session metrics
        total_stake = sum(bet['stake'] for bet in session_bets)
        total_payout = sum(bet.get('payout', 0) for bet in session_bets)
        completed_bets = [bet for bet in session_bets if bet['result'] != 'pending']
        
        if completed_bets:
            wins = len([bet for bet in completed_bets if bet['result'] == 'win'])
            win_rate = wins / len(completed_bets)
            roi = ((total_payout - total_stake) / total_stake) * 100 if total_stake > 0 else 0
        else:
            win_rate = 0
            roi = 0
        
        session = {
            'date': str(date),
            'total_bets': len(session_bets),
            'completed_bets': len(completed_bets),
            'wins': wins if completed_bets else 0,
            'win_rate': win_rate,
            'total_stake': total_stake,
            'total_payout': total_payout,
            'profit': total_payout - total_stake,
            'roi': roi
        }
        
        # Update or add session
        existing = False
        for i, s in enumerate(self.history['sessions']):
            if s['date'] == session['date']:
                self.history['sessions'][i] = session
                existing = True
                break
        
        if not existing:
            self.history['sessions'].append(session)
        
        self.save_history()
        return session
    
    def analyze_performance(self, days=30):
        """Analyze betting performance over specified period."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_bets = [
            bet for bet in self.history['bets']
            if datetime.fromisoformat(bet['date']) > cutoff_date
            and bet['result'] != 'pending'
        ]
        
        if not recent_bets:
            return None
        
        # Overall metrics
        total_bets = len(recent_bets)
        wins = len([bet for bet in recent_bets if bet['result'] == 'win'])
        win_rate = wins / total_bets
        
        total_stake = sum(bet['stake'] for bet in recent_bets)
        total_payout = sum(bet['payout'] for bet in recent_bets)
        profit = total_payout - total_stake
        roi = (profit / total_stake) * 100 if total_stake > 0 else 0
        
        # Expected vs Actual
        avg_predicted_ev = np.mean([bet['predicted_ev'] for bet in recent_bets])
        
        # Performance by confidence level
        confidence_buckets = {
            'high': [bet for bet in recent_bets if bet['confidence'] >= 70],
            'medium': [bet for bet in recent_bets if 50 <= bet['confidence'] < 70],
            'low': [bet for bet in recent_bets if bet['confidence'] < 50]
        }
        
        confidence_performance = {}
        for level, bets in confidence_buckets.items():
            if bets:
                level_wins = len([bet for bet in bets if bet['result'] == 'win'])
                level_win_rate = level_wins / len(bets)
                level_roi = self._calculate_roi(bets)
                confidence_performance[level] = {
                    'count': len(bets),
                    'win_rate': level_win_rate,
                    'roi': level_roi
                }
        
        # Performance by stat type
        stat_performance = {}
        for stat in set(bet['stat'] for bet in recent_bets):
            stat_bets = [bet for bet in recent_bets if bet['stat'] == stat]
            stat_wins = len([bet for bet in stat_bets if bet['result'] == 'win'])
            stat_performance[stat] = {
                'count': len(stat_bets),
                'win_rate': stat_wins / len(stat_bets),
                'roi': self._calculate_roi(stat_bets)
            }
        
        return {
            'period_days': days,
            'total_bets': total_bets,
            'wins': wins,
            'losses': total_bets - wins,
            'win_rate': win_rate,
            'total_stake': total_stake,
            'total_payout': total_payout,
            'profit': profit,
            'roi': roi,
            'avg_predicted_ev': avg_predicted_ev,
            'confidence_performance': confidence_performance,
            'stat_performance': stat_performance
        }
    
    def _calculate_roi(self, bets):
        """Calculate ROI for a list of bets."""
        if not bets:
            return 0
        total_stake = sum(bet['stake'] for bet in bets)
        total_payout = sum(bet['payout'] for bet in bets)
        return ((total_payout - total_stake) / total_stake) * 100 if total_stake > 0 else 0
    
    def generate_performance_report(self):
        """Generate a comprehensive performance report."""
        print("📊 WNBA Betting Performance Report")
        print("=" * 60)
        
        # Last 7 days
        week_stats = self.analyze_performance(7)
        if week_stats:
            print("\n📅 Last 7 Days:")
            print(f"  Bets: {week_stats['total_bets']} (W: {week_stats['wins']}, L: {week_stats['losses']})")
            print(f"  Win Rate: {week_stats['win_rate']:.1%}")
            print(f"  ROI: {week_stats['roi']:.1f}%")
            print(f"  Profit: ${week_stats['profit']:.2f}")
        
        # Last 30 days
        month_stats = self.analyze_performance(30)
        if month_stats:
            print("\n📅 Last 30 Days:")
            print(f"  Bets: {month_stats['total_bets']} (W: {month_stats['wins']}, L: {month_stats['losses']})")
            print(f"  Win Rate: {month_stats['win_rate']:.1%}")
            print(f"  ROI: {month_stats['roi']:.1f}%")
            print(f"  Profit: ${month_stats['profit']:.2f}")
            
            # Confidence breakdown
            print("\n🎯 Performance by Confidence:")
            for level, stats in month_stats['confidence_performance'].items():
                print(f"  {level.title()}: {stats['win_rate']:.1%} win rate, {stats['roi']:.1f}% ROI ({stats['count']} bets)")
            
            # Stat breakdown
            print("\n📊 Performance by Stat Type:")
            sorted_stats = sorted(month_stats['stat_performance'].items(), 
                                key=lambda x: x[1]['roi'], reverse=True)
            for stat, perf in sorted_stats[:5]:
                print(f"  {stat}: {perf['win_rate']:.1%} win rate, {perf['roi']:.1f}% ROI ({perf['count']} bets)")
        
        # All-time stats
        all_completed = [bet for bet in self.history['bets'] if bet['result'] != 'pending']
        if all_completed:
            all_wins = len([bet for bet in all_completed if bet['result'] == 'win'])
            all_roi = self._calculate_roi(all_completed)
            
            print(f"\n📈 All-Time Record:")
            print(f"  Total Bets: {len(all_completed)}")
            print(f"  Win Rate: {all_wins/len(all_completed):.1%}")
            print(f"  ROI: {all_roi:.1f}%")

def main():
    """Demo/utility functions for edge tracker."""
    tracker = EdgeTracker()
    
    print("🎯 WNBA Betting Edge Tracker")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. View performance report")
        print("2. Add bet result")
        print("3. Import today's bets from betting slip")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ")
        
        if choice == '1':
            tracker.generate_performance_report()
            
        elif choice == '2':
            try:
                source_id = int(input("Enter bet ID: "))
                actual_value = float(input("Enter actual value: "))
                tracker.update_bet_result(source_id, actual_value)
                print("✅ Bet result updated")
            except ValueError:
                print("❌ Invalid input")
                
        elif choice == '3':
            # Import from today's betting slip
            import glob
            today = datetime.now().strftime('%Y%m%d')
            slips = glob.glob(f'output/betting_slip_{today}*.csv')
            
            if slips:
                latest_slip = max(slips)
                try:
                    slip_df = pd.read_csv(latest_slip)
                    print(f"\n📋 Found {len(slip_df)} bets in {latest_slip}")
                    
                    for _, bet in slip_df.iterrows():
                        # Parse bet string
                        parts = bet['Bet'].split()
                        player = ' '.join(parts[:-3])
                        recommendation = parts[-3]
                        line = float(parts[-2])
                        stat = parts[-1]
                        
                        source_id = tracker.add_bet(
                            player=player,
                            stat=stat,
                            line=line,
                            recommendation=recommendation,
                            predicted_ev=bet['EV'],
                            hit_probability=bet['Hit_Probability'],
                            confidence=70  # Default, could be enhanced
                        )
                        print(f"  Added bet #{source_id}: {bet['Bet']}")
                        
                    print("✅ All bets imported")
                except Exception as e:
                    print(f"❌ Error importing: {e}")
            else:
                print("❌ No betting slip found for today")
                
        elif choice == '4':
            break
            
        else:
            print("Invalid option")
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
