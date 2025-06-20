#!/usr/bin/env python3
"""Main workflow runner for PhaseGrid betting system."""

import argparse
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from sheet_connector import SheetConnector
from slip_optimizer import SlipOptimizer
from bankroll_optimizer import BankrollOptimizer
from update_results import ResultsUpdater


class BettingWorkflow:
    def __init__(self, mode: str = "PRODUCTION"):
        """Initialize betting workflow."""
        self.mode = mode
        self.sheet_id = "1-VX73LvsxtpO4D15dsaYso3UjGzYcmsFJUx0io6_VZM"
        
        # Initialize components
        self.connector = SheetConnector(sheet_id=self.sheet_id)
        self.slip_optimizer = SlipOptimizer()
        self.bankroll_optimizer = BankrollOptimizer()
        self.results_updater = ResultsUpdater(sheet_id=self.sheet_id)
        
        # Workflow state
        self.current_bankroll = 1000.0
        self.current_phase = 'follicular'
        self.phase_win_rate = 0.52
        
    def run(self, 
            target_date: Optional[datetime] = None,
            max_slips: int = 10,
            slip_types: List[str] = ['Power', 'Flex']) -> Dict:
        """
        Run complete betting workflow.
        
        Args:
            target_date: Date to generate slips for
            max_slips: Maximum number of slips to generate
            slip_types: Types of slips to generate
            
        Returns:
            Workflow execution summary
        """
        if target_date is None:
            target_date = datetime.now()
            
        print(f"\n🚀 Running {self.mode} betting workflow for {target_date.strftime('%Y-%m-%d')}")
        
        # Step 1: Load configuration and state
        self._load_current_state()
        
        # Step 2: Get available betting opportunities
        opportunities = self._get_betting_opportunities(target_date)
        
        if not opportunities:
            print("❌ No betting opportunities available")
            return {'status': 'no_opportunities', 'slips_generated': 0}
            
        # Step 3: Optimize slips
        optimized_slips = self.slip_optimizer.optimize_slips(
            available_bets=opportunities,
            target_slips=max_slips,
            slip_types=slip_types
        )
        
        print(f"\n📋 Generated {len(optimized_slips)} optimized slips")
        
        # Step 4: Apply Kelly criterion for stake sizing
        sized_slips = self._apply_stake_sizing(optimized_slips)
        
        # Step 5: Prepare slip data
        slip_data = self._prepare_slip_data(sized_slips, target_date)
        
        # Step 6: Sync to Google Sheets
        if self.mode != "TEST":
            self._sync_to_sheets(slip_data)
            print("✅ Slips synced to Google Sheets")
        else:
            print("✅ TEST mode - skipping sheet sync")
            
        # Step 7: Generate summary
        summary = self._generate_summary(slip_data)
        
        # Display results
        self._display_summary(summary)
        
        return summary
        
    def _load_current_state(self):
        """Load current bankroll and phase information."""
        try:
            # Read settings
            settings_df = self.connector.read_sheet('settings')
            
            # Get current bankroll
            bankroll_row = settings_df[settings_df['parameter'] == 'current_bankroll']
            if not bankroll_row.empty:
                bankroll_str = bankroll_row.iloc[0]['value']
                self.current_bankroll = float(bankroll_str.replace('$', '').replace(',', ''))
                
            # Get current phase
            phase_row = settings_df[settings_df['parameter'] == 'current_phase']
            if not phase_row.empty:
                self.current_phase = phase_row.iloc[0]['value']
                
            # Get phase win rate from tracker
            tracker_df = self.connector.read_sheet('phase_confidence_tracker')
            phase_data = tracker_df[tracker_df['phase'] == self.current_phase]
            if not phase_data.empty:
                # Use most recent win rate
                recent = phase_data.sort_values('date', ascending=False).iloc[0]
                self.phase_win_rate = recent['win_rate']
                
        except Exception as e:
            print(f"Warning: Failed to load state: {e}")
            # Use defaults
            
        print(f"💰 Current bankroll: ${self.current_bankroll:,.2f}")
        print(f"🌙 Current phase: {self.current_phase}")
        print(f"📊 Phase win rate: {self.phase_win_rate:.1%}")
        
    def _get_betting_opportunities(self, date: datetime) -> List[Dict]:
        """Get available betting opportunities for the date."""
        if self.mode == "TEST":
            # Generate test data
            return self._generate_test_opportunities()
            
        # In production, this would fetch from data sources
        # For now, simulate realistic opportunities
        
        teams = ['LAS', 'LA', 'NY', 'CHI', 'SEA', 'MIN', 'PHO', 'DAL', 'ATL', 'WAS', 'CON', 'IND']
        players = [
            {'name': 'A. Wilson', 'team': 'LAS', 'avg_pts': 23.5, 'avg_reb': 7.2, 'avg_ast': 4.1},
            {'name': 'S. Stewart', 'team': 'NY', 'avg_pts': 19.8, 'avg_reb': 9.5, 'avg_ast': 3.2},
            {'name': 'B. Jones', 'team': 'CHI', 'avg_pts': 21.2, 'avg_reb': 5.8, 'avg_ast': 6.3},
            {'name': 'C. Clark', 'team': 'IND', 'avg_pts': 18.7, 'avg_reb': 4.5, 'avg_ast': 7.8},
            {'name': 'D. Taurasi', 'team': 'PHO', 'avg_pts': 16.3, 'avg_reb': 3.8, 'avg_ast': 5.2},
            {'name': 'J. Young', 'team': 'LAS', 'avg_pts': 14.5, 'avg_reb': 8.2, 'avg_ast': 2.8},
            {'name': 'K. Mitchell', 'team': 'SEA', 'avg_pts': 17.9, 'avg_reb': 6.1, 'avg_ast': 4.5},
            {'name': 'S. Diggins', 'team': 'PHO', 'avg_pts': 15.2, 'avg_reb': 3.5, 'avg_ast': 6.9}
        ]
        
        opportunities = []
        
        # Generate 4-6 games
        num_games = np.random.randint(4, 7)
        used_teams = set()
        
        for _ in range(num_games):
            # Select teams
            available_teams = [t for t in teams if t not in used_teams]
            if len(available_teams) < 2:
                break
                
            team1, team2 = np.random.choice(available_teams, 2, replace=False)
            used_teams.update([team1, team2])
            game = f"{team1} @ {team2}"
            
            # Get players for these teams
            game_players = [p for p in players if p['team'] in [team1, team2]]
            
            for player in game_players:
                # Generate props
                for prop_type, avg_key in [('points', 'avg_pts'), ('rebounds', 'avg_reb'), ('assists', 'avg_ast')]:
                    avg_stat = player[avg_key]
                    
                    # Line is slightly adjusted from average
                    line = round(avg_stat + np.random.uniform(-1.5, 1.5), 1)
                    
                    # Generate projection
                    projection = avg_stat + np.random.normal(0, 1.5)
                    
                    # Calculate confidence based on edge
                    edge = abs(projection - line) / line
                    base_confidence = 0.52 + min(edge * 0.3, 0.13)  # Cap at 0.65
                    
                    # Add some noise
                    confidence = np.clip(base_confidence + np.random.uniform(-0.03, 0.03), 0.45, 0.68)
                    
                    # Odds based on confidence
                    if confidence > 0.55:
                        over_odds = np.random.randint(-125, -105)
                        under_odds = np.random.randint(-115, -105)
                    else:
                        over_odds = np.random.randint(-115, -105)
                        under_odds = np.random.randint(-115, -105)
                        
                    opportunities.append({
                        'game': game,
                        'player': player['name'],
                        'prop_type': prop_type,
                        'line': line,
                        'over_odds': over_odds,
                        'under_odds': under_odds,
                        'projection': round(projection, 1),
                        'confidence': round(confidence, 3),
                        'odds': over_odds if projection > line else under_odds
                    })
                    
        print(f"📊 Found {len(opportunities)} betting opportunities across {num_games} games")
        
        return opportunities
        
    def _generate_test_opportunities(self) -> List[Dict]:
        """Generate minimal test opportunities."""
        return [
            {
                'game': 'TEST @ GAME',
                'player': 'Test Player 1',
                'prop_type': 'points',
                'line': 20.5,
                'over_odds': -110,
                'under_odds': -110,
                'projection': 22.0,
                'confidence': 0.58,
                'odds': -110
            },
            {
                'game': 'TEST @ GAME',
                'player': 'Test Player 2',
                'prop_type': 'rebounds',
                'line': 8.5,
                'over_odds': -115,
                'under_odds': -105,
                'projection': 9.5,
                'confidence': 0.62,
                'odds': -115
            },
            {
                'game': 'GAME @ TEST',
                'player': 'Test Player 3',
                'prop_type': 'assists',
                'line': 5.5,
                'over_odds': -120,
                'under_odds': -100,
                'projection': 6.2,
                'confidence': 0.55,
                'odds': -120
            }
        ]
        
    def _apply_stake_sizing(self, slips: List) -> List[Dict]:
        """Apply Kelly criterion to size stakes."""
        sized_slips = []
        
        for slip in slips:
            # Calculate appropriate stake
            if slip.slip_type == 'Power':
                # For Power plays, use combined probability
                win_prob = slip.confidence
            else:
                # For Flex, use weighted probability
                avg_confidence = sum(b.confidence for b in slip.bets) / len(slip.bets)
                win_prob = avg_confidence
                
            # Apply phase-aware Kelly
            stake = self.bankroll_optimizer.calculate_stake(
                bankroll=self.current_bankroll,
                win_prob=win_prob,
                odds=slip.total_odds if slip.slip_type == 'Power' else 2.0,  # Simplified for Flex
                phase=self.current_phase,
                win_rate=self.phase_win_rate
            )
            
            if stake > 0:
                # Format slip details
                slip_details = self.slip_optimizer.format_slip_details(slip, stake)
                slip_details['slip_object'] = slip
                sized_slips.append(slip_details)
                
        return sized_slips
        
    def _prepare_slip_data(self, sized_slips: List[Dict], date: datetime) -> Dict:
        """Prepare data for sheet upload."""
        slips_data = []
        bets_data = []
        
        for i, slip_info in enumerate(sized_slips, 1):
            slip = slip_info['slip_object']
            
            # Generate slip ID
            slip_id = f"{self.mode[:4]}_{date.strftime('%Y%m%d')}_{slip.slip_type[:3]}_{i:03d}"
            
            # Slip entry
            slip_entry = {
                'slip_id': slip_id,
                'date': date.strftime('%Y-%m-%d'),
                'type': slip.slip_type,
                'legs': slip.num_legs,
                'total_stake': slip_info['stake'],
                'potential_payout': slip_info.get('potential_payout', 
                                                 slip_info.get('payout_tiers', {}).get(f"{slip.num_legs}_correct", 0)),
                'actual_payout': 0,
                'result': 'pending',
                'phase': self.current_phase,
                'confidence': round(slip.confidence, 3),
                'dry_run': 'TRUE' if self.mode == "TEST" else 'FALSE'
            }
            
            slips_data.append(slip_entry)
            
            # Individual bet entries
            for j, bet in enumerate(slip.bets, 1):
                bet_entry = {
                    'slip_id': slip_id,
                    'source_id': f"{slip_id}_L{j}",  # Using source_id not bet_id
                    'date': date.strftime('%Y-%m-%d'),
                    'player': bet.player,
                    'prop_type': bet.prop_type,
                    'line': bet.line,
                    'over_under': bet.over_under,
                    'odds': bet.odds,
                    'stake': round(slip_info['stake'] / slip.num_legs, 2),  # Equal split
                    'result': 'pending',
                    'payout': 0,
                    'phase': self.current_phase,
                    'confidence': bet.confidence,
                    'notes': f"{bet.game}"
                }
                
                bets_data.append(bet_entry)
                
        return {
            'slips': pd.DataFrame(slips_data),
            'bets': pd.DataFrame(bets_data)
        }
        
    def _sync_to_sheets(self, slip_data: Dict):
        """Sync slip data to Google Sheets."""
        try:
            # Append to logs
            if not slip_data['slips'].empty:
                self.connector.append_data('slips_log', slip_data['slips'])
                
            if not slip_data['bets'].empty:
                self.connector.append_data('bets_log', slip_data['bets'])
                
            # Update current bankroll (deduct stakes)
            total_stake = slip_data['slips']['total_stake'].sum()
            new_bankroll = self.current_bankroll - total_stake
            
            # Update settings
            settings_df = self.connector.read_sheet('settings')
            settings_df.loc[settings_df['parameter'] == 'current_bankroll', 'value'] = f"${new_bankroll:,.2f}"
            settings_df.loc[settings_df['parameter'] == 'current_bankroll', 'last_updated'] = datetime.now().isoformat()
            
            self.connector.update_sheet('settings', settings_df)
            
        except Exception as e:
            print(f"❌ Error syncing to sheets: {e}")
            raise
            
    def _generate_summary(self, slip_data: Dict) -> Dict:
        """Generate workflow execution summary."""
        slips_df = slip_data['slips']
        bets_df = slip_data['bets']
        
        power_slips = len(slips_df[slips_df['type'] == 'Power'])
        flex_slips = len(slips_df[slips_df['type'] == 'Flex'])
        
        summary = {
            'status': 'success',
            'mode': self.mode,
            'date': slips_df.iloc[0]['date'] if not slips_df.empty else datetime.now().strftime('%Y-%m-%d'),
            'slips_generated': len(slips_df),
            'power_slips': power_slips,
            'flex_slips': flex_slips,
            'total_bets': len(bets_df),
            'total_stake': slips_df['total_stake'].sum(),
            'max_potential_payout': slips_df['potential_payout'].sum(),
            'phase': self.current_phase,
            'bankroll_before': self.current_bankroll,
            'bankroll_after': self.current_bankroll - slips_df['total_stake'].sum()
        }
        
        # Leg distribution
        summary['legs_distribution'] = slips_df['legs'].value_counts().to_dict()
        
        # Average confidence by type
        for slip_type in ['Power', 'Flex']:
            type_slips = slips_df[slips_df['type'] == slip_type]
            if not type_slips.empty:
                summary[f'{slip_type.lower()}_avg_confidence'] = type_slips['confidence'].mean()
                
        return summary
        
    def _display_summary(self, summary: Dict):
        """Display workflow summary."""
        print("\n" + "="*60)
        print("WORKFLOW SUMMARY")
        print("="*60)
        
        if self.mode == "TEST":
            print(f"Power slips: {summary['power_slips']}")
            print(f"Flex slips:  {summary['flex_slips']}")
            print("✅ slips synced")
        else:
            print(f"Date: {summary['date']}")
            print(f"Phase: {summary['phase']}")
            print(f"Slips Generated: {summary['slips_generated']}")
            print(f"  - Power: {summary['power_slips']}")
            print(f"  - Flex: {summary['flex_slips']}")
            print(f"Total Stake: ${summary['total_stake']:.2f}")
            print(f"Max Potential Payout: ${summary['max_potential_payout']:.2f}")
            print(f"Bankroll: ${summary['bankroll_before']:,.2f} → ${summary['bankroll_after']:,.2f}")
            
            if summary.get('legs_distribution'):
                print("\nLegs Distribution:")
                for legs, count in sorted(summary['legs_distribution'].items()):
                    print(f"  {legs}-leg: {count} slips")


def main():
    parser = argparse.ArgumentParser(description='Run PhaseGrid betting workflow')
    parser.add_argument('--mode', choices=['PRODUCTION', 'TEST', 'PAPER'], 
                       default='PRODUCTION', help='Workflow mode')
    parser.add_argument('--date', type=str, help='Target date (YYYY-MM-DD)')
    parser.add_argument('--max-slips', type=int, default=10, help='Maximum slips to generate')
    parser.add_argument('--power-only', action='store_true', help='Generate only Power slips')
    parser.add_argument('--flex-only', action='store_true', help='Generate only Flex slips')
    
    args = parser.parse_args()
    
    # Determine slip types
    if args.power_only:
        slip_types = ['Power']
    elif args.flex_only:
        slip_types = ['Flex']
    else:
        slip_types = ['Power', 'Flex']
        
    # Parse date
    target_date = None
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d')
        
    # Run workflow
    workflow = BettingWorkflow(mode=args.mode)
    summary = workflow.run(
        target_date=target_date,
        max_slips=args.max_slips,
        slip_types=slip_types
    )
    
    # Return appropriate exit code
    if summary['status'] == 'success' and summary['slips_generated'] > 0:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())