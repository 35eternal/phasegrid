"""
WNBA Cycle-Based Betting System - Production Ready
Integrates cycle detection with live betting opportunities
"""

import pandas as pd
from datetime import datetime, timedelta
import json

class WNBACycleBettingSystem:
    def __init__(self):
        # Load cycle patterns
        self.patterns = pd.read_csv('cycle_betting_guide.csv')
        self.high_value_patterns = self.patterns[self.patterns['Pattern_Strength'] > 0.8]
        
    def calculate_cycle_dates(self, season_start_date, player, stat, cycle_days):
        """Generate all cycle dates for a season"""
        dates = []
        current = pd.to_datetime(season_start_date)
        season_end = current + timedelta(days=140)  # ~5 month season
        
        while current < season_end:
            current += timedelta(days=cycle_days)
            dates.append({
                'date': current,
                'window_start': current - timedelta(days=3),
                'window_end': current + timedelta(days=3),
                'recovery_start': current + timedelta(days=4),
                'recovery_end': current + timedelta(days=7)
            })
        return dates
    
    def generate_season_calendar(self, season_start='2025-05-16'):
        """Create betting calendar for entire season"""
        calendar = []
        
        for _, pattern in self.high_value_patterns.iterrows():
            player = pattern['Player']
            stat = pattern['Stat']
            cycle_days = pattern['Cycle_Days']
            
            cycle_dates = self.calculate_cycle_dates(season_start, player, stat, cycle_days)
            
            for cycle in cycle_dates:
                # Dip window bets
                calendar.append({
                    'date': cycle['window_start'].strftime('%Y-%m-%d'),
                    'player': player,
                    'stat': stat,
                    'bet_type': 'UNDER',
                    'confidence': pattern['Pattern_Strength'],
                    'expected_drop': pattern['Avg_Drop_%'],
                    'phase': 'PRE_DIP'
                })
                
                # Recovery window bets
                calendar.append({
                    'date': cycle['recovery_start'].strftime('%Y-%m-%d'),
                    'player': player,
                    'stat': stat,
                    'bet_type': 'OVER',
                    'confidence': pattern['Pattern_Strength'] * 0.8,  # Slightly lower confidence
                    'expected_bounce': pattern['Avg_Drop_%'] * 0.7,  # Conservative estimate
                    'phase': 'RECOVERY'
                })
        
        calendar_df = pd.DataFrame(calendar)
        calendar_df = calendar_df.sort_values('date')
        return calendar_df
    
    def get_upcoming_bets(self, days_ahead=7):
        """Get betting opportunities for next N days"""
        calendar = self.generate_season_calendar()
        today = pd.to_datetime('2025-06-16')  # Current date
        end_date = today + timedelta(days=days_ahead)
        
        upcoming = calendar[
            (pd.to_datetime(calendar['date']) >= today) & 
            (pd.to_datetime(calendar['date']) <= end_date)
        ]
        
        return upcoming
    
    def create_betting_sheet(self):
        """Create comprehensive betting guide"""
        print("="*60)
        print("WNBA CYCLE BETTING SYSTEM - MASTER GUIDE")
        print("="*60)
        
        # Top patterns summary
        print("\n🎯 HIGHEST VALUE PATTERNS (80%+ Reliability):")
        print("-"*60)
        
        for _, p in self.high_value_patterns.iterrows():
            print(f"\n{p['Player']} - {p['Stat']}")
            print(f"  Cycle: Every {p['Cycle_Days']} days")
            print(f"  Reliability: {p['Pattern_Strength']:.1%}")
            print(f"  Average Drop: {p['Avg_Drop_%']:.1f}%")
            print(f"  Betting Value: {p['Bet_Value']}")
        
        # Chennedy Carter special section
        print("\n" + "="*60)
        print("⭐ SPECIAL FOCUS: CHENNEDY CARTER")
        print("="*60)
        carter_patterns = self.patterns[self.patterns['Player'] == 'Chennedy Carter']
        
        print("\nTRIPLE PATTERN ADVANTAGE:")
        for _, p in carter_patterns.iterrows():
            print(f"  {p['Stat']}: {p['Cycle_Days']}-day cycle ({p['Avg_Drop_%']:.1f}% drop)")
        
        print("\nBETTING STRATEGY:")
        print("  • When PTS dip is due, bet UNDER on all three stats")
        print("  • Highest confidence window: Days 28-32 from last dip")
        print("  • Recovery plays: OVER bets 5-7 days after dip")
        
        # Export upcoming bets
        upcoming = self.get_upcoming_bets(30)
        if not upcoming.empty:
            upcoming.to_csv('upcoming_cycle_bets.csv', index=False)
            print(f"\n✅ Exported {len(upcoming)} upcoming bets to 'upcoming_cycle_bets.csv'")
        
        # Create JSON for easy integration
        patterns_json = []
        for _, p in self.patterns.iterrows():
            patterns_json.append({
                'player': p['Player'],
                'stat': p['Stat'],
                'cycle_days': float(p['Cycle_Days']),
                'reliability': float(p['Pattern_Strength']),
                'avg_drop_pct': float(p['Avg_Drop_%']),
                'bet_value': p['Bet_Value']
            })
        
        with open('cycle_patterns.json', 'w') as f:
            json.dump(patterns_json, f, indent=2)
        
        print("\n✅ Exported patterns to 'cycle_patterns.json' for app integration")
        
        return upcoming

# Run the system
system = WNBACycleBettingSystem()
upcoming_bets = system.create_betting_sheet()

# Show next week's opportunities
print("\n" + "="*60)
print("NEXT 7 DAYS - BETTING OPPORTUNITIES")
print("="*60)

next_week = system.get_upcoming_bets(7)
if not next_week.empty:
    for _, bet in next_week.iterrows():
        print(f"\n{bet['date']} - {bet['player']}")
        print(f"  Bet: {bet['stat']} {bet['bet_type']}")
        print(f"  Confidence: {bet['confidence']:.1%}")
        if bet['phase'] == 'PRE_DIP':
            print(f"  Expected drop: {bet['expected_drop']:.1f}%")
else:
    print("\nNo bets in next 7 days - season may not have started yet")

print("\n🎲 System ready for production betting!")
