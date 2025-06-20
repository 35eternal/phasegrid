#!/usr/bin/env python3
"""Update betting results from game outcomes."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
import json

from sheet_connector import SheetConnector


class ResultsUpdater:
    def __init__(self, sheet_id: str = "1-VX73LvsxtpO4D15dsaYso3UjGzYcmsFJUx0io6_VZM"):
        """Initialize results updater."""
        self.sheet_id = sheet_id
        self.connector = SheetConnector(sheet_id=sheet_id)
        
        # Results cache
        self.game_results = {}
        self.player_stats = {}
        
    def update_results(self, 
                      date: Optional[datetime] = None,
                      source: str = "api",
                      dry_run: bool = False) -> Dict:
        """
        Update betting results for completed games.
        
        Args:
            date: Date to update results for (default: yesterday)
            source: Data source ('api', 'manual', 'simulated')
            dry_run: If True, simulate results without API calls
            
        Returns:
            Summary of updates made
        """
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        print(f"\n📊 Updating results for {date.strftime('%Y-%m-%d')}...")
        
        # Read pending bets
        bets_df = self.connector.read_sheet('bets_log')
        slips_df = self.connector.read_sheet('slips_log')
        
        # Filter pending bets for the date
        pending_bets = bets_df[
            (bets_df['result'] == 'pending') & 
            (pd.to_datetime(bets_df['date']).dt.date == date.date())
        ]
        
        if pending_bets.empty:
            print("No pending bets to update.")
            return {'updated_bets': 0, 'updated_slips': 0}
            
        # Get game results
        if source == "api" and not dry_run:
            self._fetch_game_results(date)
        elif source == "simulated" or dry_run:
            self._simulate_results(pending_bets)
            
        # Update individual bet results
        updated_bets = self._update_bet_results(bets_df, pending_bets)
        
        # Update slip results
        updated_slips = self._update_slip_results(slips_df, bets_df, date)
        
        # Update phase confidence tracker
        self._update_phase_tracker(bets_df, slips_df)
        
        # Write updates back to sheets
        if not dry_run:
            print("Writing updates to sheets...")
            self.connector.update_sheet('bets_log', bets_df)
            self.connector.update_sheet('slips_log', slips_df)
            
        # Generate summary
        summary = {
            'date': date.strftime('%Y-%m-%d'),
            'updated_bets': updated_bets,
            'updated_slips': updated_slips,
            'winning_bets': len(bets_df[bets_df['result'] == 'won']),
            'total_payout': bets_df[bets_df['result'] == 'won']['payout'].sum()
        }
        
        print(f"\n✅ Updated {updated_bets} bets and {updated_slips} slips")
        
        return summary
        
    def _fetch_game_results(self, date: datetime):
        """Fetch actual game results from API."""
        # In production, this would call a real sports data API
        # For now, placeholder for API integration
        
        print(f"Fetching game results for {date.strftime('%Y-%m-%d')}...")
        
        # Example API structure (would be replaced with actual API)
        try:
            # Simulated API response
            self.game_results = {
                'LAS @ LA': {
                    'final_score': {'LAS': 78, 'LA': 82},
                    'player_stats': {
                        'A. Wilson': {'points': 24, 'rebounds': 7, 'assists': 4},
                        'S. Stewart': {'points': 18, 'rebounds': 10, 'assists': 3}
                    }
                },
                'NY @ CHI': {
                    'final_score': {'NY': 85, 'CHI': 79},
                    'player_stats': {
                        'B. Jones': {'points': 22, 'rebounds': 5, 'assists': 6}
                    }
                }
            }
            
        except Exception as e:
            print(f"Error fetching results: {e}")
            self._simulate_results(None)
            
    def _simulate_results(self, pending_bets: Optional[pd.DataFrame]):
        """Simulate game results for testing."""
        print("Simulating game results...")
        
        if pending_bets is not None:
            # Generate realistic results based on lines
            for _, bet in pending_bets.iterrows():
                player = bet['player']
                prop_type = bet['prop_type']
                line = bet['line']
                
                # Simulate with slight variance around line
                if prop_type == 'points':
                    actual = np.random.normal(line, 3.5)
                elif prop_type == 'rebounds':
                    actual = np.random.normal(line, 1.5)
                elif prop_type == 'assists':
                    actual = np.random.normal(line, 1.2)
                else:
                    actual = line + np.random.normal(0, 1)
                    
                # Store result
                if player not in self.player_stats:
                    self.player_stats[player] = {}
                self.player_stats[player][prop_type] = max(0, round(actual, 1))
                
    def _update_bet_results(self, bets_df: pd.DataFrame, pending_bets: pd.DataFrame) -> int:
        """Update individual bet results."""
        updated_count = 0
        
        for idx, bet in pending_bets.iterrows():
            player = bet['player']
            prop_type = bet['prop_type']
            line = bet['line']
            over_under = bet['over_under']
            odds = bet['odds']
            stake = bet['stake']
            
            # Get actual result
            actual = self._get_player_stat(player, prop_type)
            
            if actual is not None:
                # Determine win/loss
                if over_under == 'over':
                    won = actual > line
                else:
                    won = actual < line
                    
                # Calculate payout
                if won:
                    # Convert odds to decimal
                    if odds < 0:
                        decimal_odds = (-100 / odds) + 1
                    else:
                        decimal_odds = (odds / 100) + 1
                        
                    payout = round(stake * decimal_odds, 2)
                    result = 'won'
                else:
                    payout = 0
                    result = 'lost'
                    
                # Handle push (exact line)
                if actual == line:
                    payout = stake  # Return stake
                    result = 'push'
                    
                # Update DataFrame
                bets_df.loc[idx, 'result'] = result
                bets_df.loc[idx, 'payout'] = payout
                bets_df.loc[idx, 'actual'] = actual
                
                updated_count += 1
                
        return updated_count
        
    def _get_player_stat(self, player: str, prop_type: str) -> Optional[float]:
        """Get actual player statistic."""
        # Check game results first
        for game, data in self.game_results.items():
            if 'player_stats' in data and player in data['player_stats']:
                stats = data['player_stats'][player]
                if prop_type in stats:
                    return stats[prop_type]
                    
        # Check simulated stats
        if player in self.player_stats and prop_type in self.player_stats[player]:
            return self.player_stats[player][prop_type]
            
        return None
        
    def _update_slip_results(self, slips_df: pd.DataFrame, bets_df: pd.DataFrame, date: datetime) -> int:
        """Update slip results based on individual bet outcomes."""
        updated_count = 0
        
        # Get pending slips for date
        pending_slips = slips_df[
            (slips_df['result'] == 'pending') &
            (pd.to_datetime(slips_df['date']).dt.date == date.date())
        ]
        
        for idx, slip in pending_slips.iterrows():
            slip_id = slip['slip_id']
            slip_type = slip['type']
            total_stake = slip['total_stake']
            
            # Get all bets for this slip
            slip_bets = bets_df[bets_df['slip_id'] == slip_id]
            
            if slip_bets.empty:
                continue
                
            # Count wins
            wins = len(slip_bets[slip_bets['result'] == 'won'])
            losses = len(slip_bets[slip_bets['result'] == 'lost'])
            pushes = len(slip_bets[slip_bets['result'] == 'push'])
            total_legs = len(slip_bets)
            
            # Calculate payout based on slip type
            if slip_type == 'Power':
                # Power play: all must win (pushes reduce legs)
                effective_legs = wins + pushes
                
                if losses == 0 and effective_legs == total_legs:
                    # All won or pushed - calculate payout
                    if wins == 0:
                        # All pushes
                        actual_payout = total_stake
                        result = 'push'
                    else:
                        # Calculate combined odds from winning bets
                        combined_odds = 1.0
                        for _, bet in slip_bets[slip_bets['result'] == 'won'].iterrows():
                            odds = bet['odds']
                            if odds < 0:
                                decimal_odds = (-100 / odds) + 1
                            else:
                                decimal_odds = (odds / 100) + 1
                            combined_odds *= decimal_odds
                            
                        actual_payout = round(total_stake * combined_odds, 2)
                        result = 'won'
                else:
                    actual_payout = 0
                    result = 'lost'
                    
            else:  # Flex
                # Get payout table
                payout_table = self._get_flex_payouts(total_legs)
                
                # Adjust for pushes (reduce total legs)
                effective_legs = total_legs - pushes
                effective_wins = wins
                
                if str(effective_wins) in payout_table:
                    multiplier = payout_table[str(effective_wins)]
                    actual_payout = round(total_stake * multiplier, 2)
                    
                    if actual_payout > total_stake:
                        result = 'won'
                    elif actual_payout == total_stake:
                        result = 'push'
                    else:
                        result = 'partial'
                else:
                    actual_payout = 0
                    result = 'lost'
                    
            # Update slip
            slips_df.loc[idx, 'actual_payout'] = actual_payout
            slips_df.loc[idx, 'result'] = result
            slips_df.loc[idx, 'winning_legs'] = wins
            slips_df.loc[idx, 'updated_at'] = datetime.now().isoformat()
            
            updated_count += 1
            
        return updated_count
        
    def _get_flex_payouts(self, num_legs: int) -> Dict[str, float]:
        """Get Flex payout table."""
        try:
            config_path = Path(__file__).parent / "config" / "payout_tables.json"
            with open(config_path, 'r') as f:
                payouts = json.load(f)
                return payouts['flex'].get(str(num_legs), {})
        except:
            # Fallback payouts
            default = {
                2: {2: 2.3},
                3: {2: 1.2, 3: 5.0},
                4: {2: 0.4, 3: 2.0, 4: 10.0},
                5: {3: 1.5, 4: 5.0, 5: 20.0},
                6: {4: 4.0, 5: 12.0, 6: 35.0}
            }
            return default.get(num_legs, {})
            
    def _update_phase_tracker(self, bets_df: pd.DataFrame, slips_df: pd.DataFrame):
        """Update phase confidence tracking metrics."""
        try:
            tracker_df = self.connector.read_sheet('phase_confidence_tracker')
            
            # Calculate metrics by phase
            phases = ['menstrual', 'follicular', 'ovulatory', 'luteal']
            
            for phase in phases:
                # Get phase bets
                phase_bets = bets_df[
                    (bets_df['phase'] == phase) & 
                    (bets_df['result'].isin(['won', 'lost']))
                ]
                
                if not phase_bets.empty:
                    wins = len(phase_bets[phase_bets['result'] == 'won'])
                    total = len(phase_bets)
                    win_rate = wins / total
                    
                    total_stake = phase_bets['stake'].sum()
                    total_payout = phase_bets['payout'].sum()
                    roi = (total_payout - total_stake) / total_stake if total_stake > 0 else 0
                    
                    # Update or append
                    new_row = {
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'phase': phase,
                        'confidence': 'medium',  # Would be calculated from model
                        'win_rate': round(win_rate, 3),
                        'roi': round(roi, 3),
                        'total_bets': total,
                        'total_stake': round(total_stake, 2),
                        'total_payout': round(total_payout, 2)
                    }
                    
                    tracker_df = pd.concat([tracker_df, pd.DataFrame([new_row])], ignore_index=True)
                    
            # Keep only last 30 days per phase
            tracker_df['date'] = pd.to_datetime(tracker_df['date'])
            cutoff = datetime.now() - timedelta(days=30)
            tracker_df = tracker_df[tracker_df['date'] >= cutoff]
            
            # Write back
            self.connector.update_sheet('phase_confidence_tracker', tracker_df)
            
        except Exception as e:
            print(f"Error updating phase tracker: {e}")
            
    def generate_performance_report(self, 
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> Dict:
        """Generate performance report for date range."""
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
            
        print(f"\n📈 Generating performance report ({start_date.date()} to {end_date.date()})...")
        
        # Read data
        bets_df = self.connector.read_sheet('bets_log')
        slips_df = self.connector.read_sheet('slips_log')
        
        # Filter date range
        bets_df['date'] = pd.to_datetime(bets_df['date'])
        slips_df['date'] = pd.to_datetime(slips_df['date'])
        
        period_bets = bets_df[
            (bets_df['date'] >= start_date) & 
            (bets_df['date'] <= end_date) &
            (bets_df['result'].isin(['won', 'lost']))
        ]
        
        period_slips = slips_df[
            (slips_df['date'] >= start_date) & 
            (slips_df['date'] <= end_date) &
            (slips_df['result'].isin(['won', 'lost', 'partial']))
        ]
        
        # Calculate metrics
        report = {
            'period': f"{start_date.date()} to {end_date.date()}",
            'total_bets': len(period_bets),
            'winning_bets': len(period_bets[period_bets['result'] == 'won']),
            'bet_win_rate': len(period_bets[period_bets['result'] == 'won']) / len(period_bets) if len(period_bets) > 0 else 0,
            'total_slips': len(period_slips),
            'winning_slips': len(period_slips[period_slips['result'] == 'won']),
            'slip_win_rate': len(period_slips[period_slips['result'] == 'won']) / len(period_slips) if len(period_slips) > 0 else 0,
            'total_stake': period_slips['total_stake'].sum(),
            'total_payout': period_slips['actual_payout'].sum(),
            'net_profit': period_slips['actual_payout'].sum() - period_slips['total_stake'].sum(),
            'roi': ((period_slips['actual_payout'].sum() - period_slips['total_stake'].sum()) / 
                    period_slips['total_stake'].sum() * 100) if period_slips['total_stake'].sum() > 0 else 0
        }
        
        # Performance by slip type
        report['by_type'] = {}
        for slip_type in ['Power', 'Flex']:
            type_slips = period_slips[period_slips['type'] == slip_type]
            if not type_slips.empty:
                report['by_type'][slip_type] = {
                    'count': len(type_slips),
                    'win_rate': len(type_slips[type_slips['result'] == 'won']) / len(type_slips),
                    'roi': ((type_slips['actual_payout'].sum() - type_slips['total_stake'].sum()) / 
                            type_slips['total_stake'].sum() * 100) if type_slips['total_stake'].sum() > 0 else 0
                }
                
        # Performance by phase
        report['by_phase'] = {}
        for phase in ['menstrual', 'follicular', 'ovulatory', 'luteal']:
            phase_slips = period_slips[period_slips['phase'] == phase]
            if not phase_slips.empty:
                report['by_phase'][phase] = {
                    'count': len(phase_slips),
                    'win_rate': len(phase_slips[phase_slips['result'] == 'won']) / len(phase_slips),
                    'roi': ((phase_slips['actual_payout'].sum() - phase_slips['total_stake'].sum()) / 
                            phase_slips['total_stake'].sum() * 100) if phase_slips['total_stake'].sum() > 0 else 0
                }
                
        # Display report
        print("\n" + "="*60)
        print("PERFORMANCE REPORT")
        print("="*60)
        print(f"Period: {report['period']}")
        print(f"Total Slips: {report['total_slips']}")
        print(f"Win Rate: {report['slip_win_rate']:.1%}")
        print(f"ROI: {report['roi']:+.1f}%")
        print(f"Net Profit: ${report['net_profit']:+,.2f}")
        
        print("\nBy Type:")
        for slip_type, metrics in report['by_type'].items():
            print(f"  {slip_type}: {metrics['win_rate']:.1%} win rate, {metrics['roi']:+.1f}% ROI")
            
        print("\nBy Phase:")
        for phase, metrics in report['by_phase'].items():
            print(f"  {phase}: {metrics['win_rate']:.1%} win rate, {metrics['roi']:+.1f}% ROI")
            
        return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Update betting results')
    parser.add_argument('--date', type=str, help='Date to update (YYYY-MM-DD)')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without writing')
    parser.add_argument('--report', action='store_true', help='Generate performance report')
    parser.add_argument('--days', type=int, default=30, help='Days to include in report')
    
    args = parser.parse_args()
    
    updater = ResultsUpdater()
    
    if args.report:
        # Generate report
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        updater.generate_performance_report(start_date, end_date)
    else:
        # Update results
        date = None
        if args.date:
            date = datetime.strptime(args.date, '%Y-%m-%d')
            
        updater.update_results(
            date=date,
            source='simulated' if args.dry_run else 'api',
            dry_run=args.dry_run
        )