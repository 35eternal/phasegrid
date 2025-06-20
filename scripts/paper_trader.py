#!/usr/bin/env python3
"""Paper trading harness for PhaseGrid betting system."""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sheet_connector import SheetConnector
from slip_optimizer import SlipOptimizer
from bankroll_optimizer import BankrollOptimizer


class PaperTrader:
    def __init__(self, mode: str = "DRY_RUN"):
        self.mode = mode
        self.sheet_id = "1-VX73LvsxtpO4D15dsaYso3UjGzYcmsFJUx0io6_VZM"
        self.connector = SheetConnector(sheet_id=self.sheet_id)
        
        # Initialize optimizers
        self.slip_optimizer = SlipOptimizer()
        self.bankroll_optimizer = BankrollOptimizer()
        
        # Output paths
        self.output_dir = Path(__file__).parent.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Paper trading state
        self.paper_slips = []
        self.metrics = {
            'total_slips': 0,
            'winning_slips': 0,
            'total_stake': 0.0,
            'total_payout': 0.0,
            'power_slips': 0,
            'flex_slips': 0,
            'hit_rates_by_legs': {},
            'roi_by_phase': {}
        }
        
    def run_daily_paper_trades(self, target_date: Optional[datetime] = None):
        """Generate paper trading slips for a given date."""
        if target_date is None:
            target_date = datetime.now()
            
        print(f"\n🎲 Running paper trades for {target_date.strftime('%Y-%m-%d')}...")
        
        # Load today's games and projections
        games_data = self._load_games_data(target_date)
        if not games_data:
            print("No games available for paper trading today.")
            return
            
        # Get current phase and confidence
        phase_info = self._get_current_phase()
        
        # Generate Power slips (2-3 legs)
        power_slips = self._generate_power_slips(games_data, phase_info)
        
        # Generate Flex slips (2-6 legs)
        flex_slips = self._generate_flex_slips(games_data, phase_info)
        
        # Combine all slips
        all_slips = power_slips + flex_slips
        
        # Apply Kelly criterion for stake sizing
        sized_slips = self._apply_kelly_sizing(all_slips, phase_info)
        
        # Tag as dry run
        for slip in sized_slips:
            slip['dry_run'] = True
            slip['date'] = target_date.strftime('%Y-%m-%d')
            
        # Save to sheets and local CSV
        self._save_paper_slips(sized_slips, target_date)
        
        # Update metrics
        self.paper_slips.extend(sized_slips)
        self.metrics['total_slips'] += len(sized_slips)
        self.metrics['power_slips'] += len(power_slips)
        self.metrics['flex_slips'] += len(flex_slips)
        self.metrics['total_stake'] += sum(slip['total_stake'] for slip in sized_slips)
        
        print(f"✅ Generated {len(sized_slips)} paper slips ({len(power_slips)} Power, {len(flex_slips)} Flex)")
        
    def _load_games_data(self, date: datetime) -> List[Dict]:
        """Load games and player projections for given date."""
        # In production, this would connect to data sources
        # For paper trading, generate synthetic data
        
        teams = ['LAS', 'LA', 'NY', 'CHI', 'SEA', 'MIN', 'PHO', 'DAL', 'ATL', 'WAS']
        players = [
            'A. Wilson', 'S. Stewart', 'B. Jones', 'A. Thomas', 'C. Clark',
            'J. Young', 'D. Taurasi', 'S. Diggins', 'K. Mitchell', 'A. Gray'
        ]
        
        games_data = []
        
        # Generate 3-5 games
        num_games = np.random.randint(3, 6)
        
        for i in range(num_games):
            team1, team2 = np.random.choice(teams, 2, replace=False)
            
            # Generate player props for each game
            for _ in range(4):  # 4 players per game
                player = np.random.choice(players)
                
                for prop_type in ['points', 'rebounds', 'assists']:
                    line = {
                        'points': np.random.uniform(12, 28),
                        'rebounds': np.random.uniform(4, 12),
                        'assists': np.random.uniform(2, 8)
                    }[prop_type]
                    
                    games_data.append({
                        'game': f"{team1} @ {team2}",
                        'player': player,
                        'prop_type': prop_type,
                        'line': round(line, 1),
                        'over_odds': np.random.uniform(-130, -105),
                        'under_odds': np.random.uniform(-130, -105),
                        'projection': line + np.random.uniform(-2, 2),
                        'confidence': np.random.uniform(0.45, 0.65)
                    })
                    
        return games_data
        
    def _get_current_phase(self) -> Dict:
        """Get current menstrual phase and confidence level."""
        # In production, this would read from phase_confidence_tracker
        # For demo, cycle through phases
        
        day_of_month = datetime.now().day
        phases = ['menstrual', 'follicular', 'ovulatory', 'luteal']
        phase = phases[(day_of_month - 1) % 4]
        
        # Phase-based confidence adjustments
        confidence_multipliers = {
            'menstrual': 0.85,
            'follicular': 0.95,
            'ovulatory': 1.10,
            'luteal': 1.05
        }
        
        return {
            'phase': phase,
            'confidence_multiplier': confidence_multipliers[phase],
            'win_rate_estimate': 0.52 * confidence_multipliers[phase]
        }
        
    def _generate_power_slips(self, games_data: List[Dict], phase_info: Dict) -> List[Dict]:
        """Generate Power Play slips (2-3 legs, all correct required)."""
        slips = []
        
        # Filter high-confidence picks
        high_conf_picks = [g for g in games_data if g['confidence'] * phase_info['confidence_multiplier'] > 0.58]
        
        if len(high_conf_picks) < 2:
            return slips
            
        # Generate 2-3 Power slips
        num_slips = min(3, len(high_conf_picks) // 2)
        
        for i in range(num_slips):
            # Select 2-3 legs
            num_legs = np.random.randint(2, 4)
            legs = np.random.choice(high_conf_picks, num_legs, replace=False)
            
            # Calculate combined odds and payout
            combined_odds = 1.0
            for leg in legs:
                # Use over/under based on projection vs line
                if leg['projection'] > leg['line']:
                    odds = leg['over_odds']
                    pick = 'over'
                else:
                    odds = leg['under_odds']
                    pick = 'under'
                    
                # Convert American to decimal odds
                decimal_odds = (-100 / odds) + 1 if odds < 0 else (odds / 100) + 1
                combined_odds *= decimal_odds
                
                leg['pick'] = pick
                leg['decimal_odds'] = decimal_odds
                
            slip_id = f"PAPER_PWR_{datetime.now().strftime('%Y%m%d')}_{i+1:03d}"
            
            slips.append({
                'slip_id': slip_id,
                'type': 'Power',
                'legs': num_legs,
                'picks': legs,
                'combined_odds': combined_odds,
                'potential_multiplier': combined_odds
            })
            
        return slips
        
    def _generate_flex_slips(self, games_data: List[Dict], phase_info: Dict) -> List[Dict]:
        """Generate Flex Play slips (2-6 legs, partial wins allowed)."""
        slips = []
        
        # Use broader selection for Flex
        viable_picks = [g for g in games_data if g['confidence'] * phase_info['confidence_multiplier'] > 0.52]
        
        if len(viable_picks) < 2:
            return slips
            
        # Generate 3-5 Flex slips with varying leg counts
        num_slips = min(5, len(viable_picks) // 2)
        
        for i in range(num_slips):
            # Vary leg count: 2-6 legs
            if i < 2:
                num_legs = np.random.randint(2, 4)  # Focus on 2-3 legs
            else:
                num_legs = np.random.randint(4, 7)  # Include 4-6 legs
                
            num_legs = min(num_legs, len(viable_picks))
            legs = np.random.choice(viable_picks, num_legs, replace=False)
            
            # Process legs
            for leg in legs:
                if leg['projection'] > leg['line']:
                    odds = leg['over_odds']
                    pick = 'over'
                else:
                    odds = leg['under_odds']
                    pick = 'under'
                    
                decimal_odds = (-100 / odds) + 1 if odds < 0 else (odds / 100) + 1
                leg['pick'] = pick
                leg['decimal_odds'] = decimal_odds
                
            slip_id = f"PAPER_FLX_{datetime.now().strftime('%Y%m%d')}_{i+1:03d}"
            
            slips.append({
                'slip_id': slip_id,
                'type': 'Flex',
                'legs': num_legs,
                'picks': legs,
                'flex_payouts': self._get_flex_payouts(num_legs)
            })
            
        return slips
        
    def _get_flex_payouts(self, num_legs: int) -> Dict[int, float]:
        """Get Flex payout multipliers by correct picks."""
        # Load from config if available
        try:
            config_path = Path(__file__).parent.parent / "config" / "payout_tables.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    payout_tables = json.load(f)
                    return payout_tables.get('flex', {}).get(str(num_legs), {})
        except:
            pass
            
        # Default payout structure
        default_payouts = {
            2: {2: 2.5},
            3: {2: 1.2, 3: 5.0},
            4: {2: 0.4, 3: 2.0, 4: 10.0},
            5: {3: 1.5, 4: 5.0, 5: 20.0},
            6: {4: 4.0, 5: 12.0, 6: 35.0}
        }
        
        return default_payouts.get(num_legs, {})
        
    def _apply_kelly_sizing(self, slips: List[Dict], phase_info: Dict) -> List[Dict]:
        """Apply Kelly criterion for stake sizing."""
        # Get current bankroll from settings
        try:
            settings_df = self.connector.read_sheet('settings')
            bankroll_row = settings_df[settings_df['parameter'] == 'current_bankroll']
            if not bankroll_row.empty:
                bankroll_str = bankroll_row.iloc[0]['value']
                bankroll = float(bankroll_str.replace('$', '').replace(',', ''))
            else:
                bankroll = 1000.0  # Default
        except:
            bankroll = 1000.0
            
        # Calculate stakes
        for slip in slips:
            if slip['type'] == 'Power':
                # Power play sizing
                win_prob = phase_info['win_rate_estimate'] ** slip['legs']
                kelly_fraction = self.bankroll_optimizer.calculate_kelly_fraction(
                    win_prob=win_prob,
                    odds=slip['combined_odds'],
                    phase=phase_info['phase']
                )
                
            else:  # Flex
                # Flex play sizing (use expected value approach)
                expected_multiplier = 0
                for correct, payout in slip['flex_payouts'].items():
                    prob = phase_info['win_rate_estimate'] ** int(correct) * (1 - phase_info['win_rate_estimate']) ** (slip['legs'] - int(correct))
                    expected_multiplier += prob * payout
                    
                win_prob = phase_info['win_rate_estimate'] ** (slip['legs'] // 2 + 1)  # Simplified
                kelly_fraction = self.bankroll_optimizer.calculate_kelly_fraction(
                    win_prob=win_prob,
                    odds=expected_multiplier,
                    phase=phase_info['phase']
                )
                
            # Apply constraints
            stake = bankroll * kelly_fraction
            stake = max(5.0, min(stake, bankroll * 0.05))  # $5 min, 5% max
            stake = round(stake, 2)  # Round to 2 decimal places
            
            slip['total_stake'] = stake
            slip['phase'] = phase_info['phase']
            slip['confidence'] = phase_info['win_rate_estimate']
            
            # Calculate potential payout
            if slip['type'] == 'Power':
                slip['potential_payout'] = round(stake * slip['combined_odds'], 2)
            else:
                # Use max payout for Flex
                max_payout = max(slip['flex_payouts'].values())
                slip['potential_payout'] = round(stake * max_payout, 2)
                
        return slips
        
    def _save_paper_slips(self, slips: List[Dict], date: datetime):
        """Save paper slips to Google Sheets and local CSV."""
        if not slips:
            return
            
        # Prepare data for sheets
        slips_data = []
        bets_data = []
        
        for slip in slips:
            # Slips log entry
            slips_data.append({
                'slip_id': slip['slip_id'],
                'date': date.strftime('%Y-%m-%d'),
                'type': slip['type'],
                'legs': slip['legs'],
                'total_stake': slip['total_stake'],
                'potential_payout': slip['potential_payout'],
                'actual_payout': 0,  # Will be updated after results
                'result': 'pending',
                'phase': slip['phase'],
                'confidence': slip['confidence'],
                'dry_run': 'TRUE'
            })
            
            # Individual bets
            for i, pick in enumerate(slip['picks']):
                bets_data.append({
                    'slip_id': slip['slip_id'],
                    'source_id': f"{slip['slip_id']}_L{i+1}",
                    'date': date.strftime('%Y-%m-%d'),
                    'player': pick['player'],
                    'prop_type': pick['prop_type'],
                    'line': pick['line'],
                    'over_under': pick['pick'],
                    'odds': pick.get('over_odds' if pick['pick'] == 'over' else 'under_odds'),
                    'stake': slip['total_stake'] / slip['legs'],  # Equal split
                    'result': 'pending',
                    'payout': 0,
                    'phase': slip['phase'],
                    'confidence': pick['confidence'],
                    'notes': f"Paper trade - {pick['game']}"
                })
                
        # Write to paper_slips tab
        try:
            # Check if paper_slips tab exists
            existing_tabs = self.connector.sheet.worksheets()
            tab_names = [ws.title for ws in existing_tabs]
            
            if 'paper_slips' not in tab_names:
                # Create new tab
                self.connector.sheet.add_worksheet(title='paper_slips', rows=1000, cols=20)
                
                # Add headers
                headers = list(slips_data[0].keys())
                paper_ws = self.connector.sheet.worksheet('paper_slips')
                paper_ws.update('A1', [headers])
                
            # Append data
            paper_ws = self.connector.sheet.worksheet('paper_slips')
            values = [[row[col] for col in slips_data[0].keys()] for row in slips_data]
            paper_ws.append_rows(values)
            
            # Also append to regular slips_log and bets_log
            self.connector.append_data('slips_log', pd.DataFrame(slips_data))
            self.connector.append_data('bets_log', pd.DataFrame(bets_data))
            
        except Exception as e:
            print(f"⚠️  Failed to write to sheets: {e}")
            
        # Save local CSV
        csv_path = self.output_dir / f"paper_slips_{date.strftime('%Y%m%d')}.csv"
        
        # Combine slips and bets data for CSV
        full_data = []
        for slip in slips:
            slip_info = {k: v for k, v in slip.items() if k != 'picks'}
            for pick in slip['picks']:
                row = {**slip_info, **pick}
                full_data.append(row)
                
        df = pd.DataFrame(full_data)
        df.to_csv(csv_path, index=False)
        
        print(f"💾 Saved {len(slips)} paper slips to {csv_path}")
        
    def update_results(self, date: Optional[datetime] = None):
        """Update paper trading results after games complete."""
        if date is None:
            date = datetime.now() - timedelta(days=1)  # Yesterday's games
            
        print(f"\n📊 Updating paper trading results for {date.strftime('%Y-%m-%d')}...")
        
        # In production, this would fetch actual game results
        # For paper trading, simulate results
        
        # Read pending paper slips
        try:
            slips_df = self.connector.read_sheet('slips_log')
            bets_df = self.connector.read_sheet('bets_log')
            
            # Filter paper trades
            paper_slips = slips_df[
                (slips_df['dry_run'] == 'TRUE') & 
                (slips_df['result'] == 'pending') &
                (pd.to_datetime(slips_df['date']).dt.date == date.date())
            ]
            
            if paper_slips.empty:
                print("No pending paper slips to update.")
                return
                
            # Simulate results for each bet
            for _, slip in paper_slips.iterrows():
                slip_bets = bets_df[bets_df['slip_id'] == slip['slip_id']]
                
                # Simulate individual bet outcomes
                wins = 0
                for _, bet in slip_bets.iterrows():
                    # Use phase-adjusted win probability
                    win_prob = 0.52  # Base
                    if slip['phase'] == 'ovulatory':
                        win_prob = 0.57
                    elif slip['phase'] == 'luteal':
                        win_prob = 0.55
                    elif slip['phase'] == 'menstrual':
                        win_prob = 0.48
                        
                    # Simulate outcome
                    won = np.random.random() < win_prob
                    if won:
                        wins += 1
                        
                    # Update bet result
                    bets_df.loc[bets_df['slip_id'] == bet['slip_id'], 'result'] = 'won' if won else 'lost'
                    
                # Calculate slip payout
                if slip['type'] == 'Power':
                    # Power requires all correct
                    if wins == slip['legs']:
                        actual_payout = slip['potential_payout']
                        result = 'won'
                    else:
                        actual_payout = 0
                        result = 'lost'
                else:  # Flex
                    # Get payout based on wins
                    flex_payouts = self._get_flex_payouts(slip['legs'])
                    
                    if wins in flex_payouts:
                        multiplier = flex_payouts[wins]
                        actual_payout = round(slip['total_stake'] * multiplier, 2)
                        result = 'won' if actual_payout > slip['total_stake'] else 'push'
                    else:
                        actual_payout = 0
                        result = 'lost'
                        
                # Update slip result
                slips_df.loc[slips_df['slip_id'] == slip['slip_id'], 'actual_payout'] = actual_payout
                slips_df.loc[slips_df['slip_id'] == slip['slip_id'], 'result'] = result
                
                # Update metrics
                self.metrics['total_payout'] += actual_payout
                if result == 'won':
                    self.metrics['winning_slips'] += 1
                    
                # Track by legs
                leg_key = f"{slip['legs']}_legs"
                if leg_key not in self.metrics['hit_rates_by_legs']:
                    self.metrics['hit_rates_by_legs'][leg_key] = {'total': 0, 'wins': 0}
                self.metrics['hit_rates_by_legs'][leg_key]['total'] += 1
                if result == 'won':
                    self.metrics['hit_rates_by_legs'][leg_key]['wins'] += 1
                    
            # Write updates back to sheets
            self.connector.update_sheet('slips_log', slips_df)
            self.connector.update_sheet('bets_log', bets_df)
            
            # Calculate and display metrics
            self._calculate_metrics()
            
        except Exception as e:
            print(f"❌ Error updating results: {e}")
            
    def _calculate_metrics(self):
        """Calculate and save paper trading metrics."""
        if self.metrics['total_slips'] == 0:
            return
            
        # Overall metrics
        roi = (self.metrics['total_payout'] - self.metrics['total_stake']) / self.metrics['total_stake'] * 100
        hit_rate = self.metrics['winning_slips'] / self.metrics['total_slips'] * 100
        
        print("\n📈 Paper Trading Metrics:")
        print(f"  Total Slips: {self.metrics['total_slips']}")
        print(f"  Win Rate: {hit_rate:.1f}%")
        print(f"  ROI: {roi:+.1f}%")
        print(f"  Total Stake: ${self.metrics['total_stake']:.2f}")
        print(f"  Total Payout: ${self.metrics['total_payout']:.2f}")
        print(f"  Net P/L: ${self.metrics['total_payout'] - self.metrics['total_stake']:+.2f}")
        
        # Hit rates by legs
        print("\n  Hit Rates by Leg Count:")
        for leg_key, stats in sorted(self.metrics['hit_rates_by_legs'].items()):
            if stats['total'] > 0:
                rate = stats['wins'] / stats['total'] * 100
                print(f"    {leg_key}: {rate:.1f}% ({stats['wins']}/{stats['total']})")
                
        # Save metrics to CSV
        metrics_path = self.output_dir / "paper_metrics.csv"
        
        metrics_data = {
            'timestamp': datetime.now().isoformat(),
            'total_slips': self.metrics['total_slips'],
            'winning_slips': self.metrics['winning_slips'],
            'hit_rate': hit_rate,
            'total_stake': self.metrics['total_stake'],
            'total_payout': self.metrics['total_payout'],
            'roi': roi,
            'power_slips': self.metrics['power_slips'],
            'flex_slips': self.metrics['flex_slips']
        }
        
        # Append to existing or create new
        if metrics_path.exists():
            df = pd.read_csv(metrics_path)
            df = pd.concat([df, pd.DataFrame([metrics_data])], ignore_index=True)
        else:
            df = pd.DataFrame([metrics_data])
            
        df.to_csv(metrics_path, index=False)
        print(f"\n💾 Metrics saved to {metrics_path}")
        
    def run_7_day_simulation(self):
        """Run paper trading for 7 consecutive days."""
        print("\n🚀 Starting 7-day paper trading simulation...")
        
        start_date = datetime.now()
        
        for day in range(7):
            current_date = start_date + timedelta(days=day)
            print(f"\n{'='*60}")
            print(f"Day {day+1}/7: {current_date.strftime('%Y-%m-%d')}")
            
            # Generate slips
            self.run_daily_paper_trades(current_date)
            
            # If not first day, update previous day's results
            if day > 0:
                prev_date = current_date - timedelta(days=1)
                self.update_results(prev_date)
                
        # Update final day's results
        final_date = start_date + timedelta(days=6)
        self.update_results(final_date)
        
        print("\n🏁 7-day simulation complete!")
        self._calculate_metrics()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Paper trading harness for PhaseGrid')
    parser.add_argument('--days', type=int, default=1, help='Number of days to simulate')
    parser.add_argument('--update', action='store_true', help='Update results only')
    
    args = parser.parse_args()
    
    trader = PaperTrader()
    
    if args.update:
        trader.update_results()
    elif args.days == 7:
        trader.run_7_day_simulation()
    else:
        for _ in range(args.days):
            trader.run_daily_paper_trades()
