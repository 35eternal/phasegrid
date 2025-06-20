"""
Main betting workflow orchestrator v2.
Generates both POWER and FLEX slips with phase-aware bankroll sizing.
"""

import sys
import json
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add modules to path
sys.path.append(str(Path(__file__).parent))

from modules.sheet_connector import SheetConnector
from modules.slip_optimizer import SlipOptimizer
from modules.bankroll_optimizer import BankrollOptimizer


class BettingWorkflow:
    """Orchestrates the complete betting workflow."""
    
    def __init__(self, mode: str = "PROD"):
        """
        Initialize workflow components.
        
        Args:
            mode: "TEST" or "PROD" - affects slip generation parameters
        """
        self.mode = mode
        self.sheet_connector = SheetConnector()
        self.slip_optimizer = SlipOptimizer()
        self.bankroll_optimizer = BankrollOptimizer()
        
        # Connect to Google Sheets if in PROD mode
        if self.mode == "PROD":
            try:
                self.sheet_connector.connect()
                print("Connected to Google Sheets")
            except Exception as e:
                print(f"Warning: Could not connect to Google Sheets: {e}")
        
        # Load settings
        self.settings = self._load_settings()
        
        # Configure bankroll optimizer with settings
        self.bankroll_optimizer.set_constraints(
            min_bet=self.settings.get('min_bet', 5.0),
            max_bet_pct=self.settings.get('max_bet_pct', 0.10)
        )
    
    def _load_settings(self) -> Dict:
        """Load settings from Google Sheets or use defaults."""
        try:
            # Use the read_settings method from sheet connector
            settings_data = self.sheet_connector.read_settings()
            
            # Handle both DataFrame and dict returns
            if isinstance(settings_data, pd.DataFrame):
                if not settings_data.empty:
                    # Convert DataFrame to dict
                    settings = {}
                    for _, row in settings_data.iterrows():
                        settings[row['parameter']] = row['value']
                else:
                    raise Exception("Settings sheet is empty")
            elif isinstance(settings_data, dict):
                # Already a dict, use directly
                settings = settings_data
            else:
                raise Exception("Unexpected settings format")
            
            # Convert numeric settings - handle string values
            for key in ['min_bet', 'max_bet_pct', 'bankroll', 'power_target', 'flex_target']:
                if key in settings:
                    try:
                        # Remove any currency symbols or commas
                        value = str(settings[key]).replace(', '').replace(',', '')
    
    def load_props_data(self) -> pd.DataFrame:
        """Load today's props with phase information."""
        # For TEST mode, generate sample data
        if self.mode == "TEST":
            return self._generate_test_props()
        
        # For PROD mode, would load from actual data source
        # This is a stub - replace with actual data loading
        props_path = Path("data/todays_props.csv")
        if props_path.exists():
            return pd.read_csv(props_path)
        else:
            print("Warning: No props data found, using test data")
            return self._generate_test_props()
    
    def _generate_test_props(self) -> pd.DataFrame:
        """Generate sample props for testing."""
        import numpy as np
        
        np.random.seed(42)  # For reproducibility
        n_props = 30
        
        props = pd.DataFrame({
            'prop_id': [f'TEST_{datetime.now().strftime("%Y%m%d")}_{i:03d}' for i in range(n_props)],
            'player': [f'TestPlayer_{i%10}' for i in range(n_props)],
            'type': ['points'] * 15 + ['rebounds'] * 10 + ['assists'] * 5,
            'line': np.random.uniform(10, 35, n_props),
            'implied_prob': np.random.uniform(0.35, 0.55, n_props),  # More realistic probabilities
            'phase': np.random.choice(['follicular', 'ovulatory', 'luteal', 'menstrual'], n_props),
            'game_time': '7:00 PM ET',
            'opponent': [f'Team_{i%5}' for i in range(n_props)]
        })
        
        return props
    
    def generate_portfolio(self, props_df: pd.DataFrame) -> Dict:
        """Generate complete betting portfolio with slips AND individual bets."""
        # Generate slips (parlays)
        slips_portfolio = self.generate_slips(props_df)
        
        # Generate individual bets if enabled in settings
        individual_bets = []
        if self.settings.get('enable_singles', True):
            individual_bets = self.generate_individual_bets(props_df)
        
        return {
            'slips': slips_portfolio,
            'individual_bets': individual_bets
        }
    
    def generate_individual_bets(self, props_df: pd.DataFrame) -> List[Dict]:
        """Generate individual prop bets with phase-aware sizing."""
        bets = []
        bankroll = self.settings.get('bankroll', 1000.0)
        singles_allocation = self.settings.get('singles_allocation', 0.3)  # 30% for singles
        
        # Allocate portion of bankroll to singles
        singles_bankroll = bankroll * singles_allocation
        
        # Sort props by EV (implied edge)
        props_df['edge'] = (1 / props_df['implied_prob']) - 2.0  # Assuming -110 standard odds
        top_props = props_df.nlargest(10, 'edge')  # Top 10 props by edge
        
        for _, prop in top_props.iterrows():
            if prop['edge'] > 0:  # Positive EV only
                # Calculate stake using Kelly
                stake = self.bankroll_optimizer.size_bet(
                    bankroll=singles_bankroll,
                    ev=prop['edge'],
                    phase=prop['phase']
                )
                
                if stake > 0:
                    bet = {
                        'source_id': f"SINGLE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{prop['prop_id']}",
                        'timestamp': datetime.now().isoformat(),
                        'player_name': prop['player'],
                        'market': prop['type'],
                        'line': prop['line'],
                        'phase': prop['phase'],
                        'adjusted_prediction': prop['implied_prob'],
                        'wager_amount': stake,
                        'odds': round(1 / prop['implied_prob'], 2),
                        'status': 'pending',
                        'actual_result': '',
                        'result_confirmed': False,
                        'profit_loss': 0.0,
                        'notes': 'Individual prop bet'
                    }
                    bets.append(bet)
        
        return bets
    
    def push_slips_to_sheet(self, portfolio: Dict[str, List[Dict]]) -> int:
        """Push generated slips to Google Sheets."""
        # First, push slips to slips_log (for parlays)
        slips_pushed = self._push_to_slips_log(portfolio)
        
        # Then, also push individual bets to bets_log
        bets_pushed = self._push_to_bets_log(portfolio)
        
        return slips_pushed
    
    def _push_to_slips_log(self, portfolio: Dict[str, List[Dict]]) -> int:
        """Push parlay slips to slips_log worksheet."""
        all_slips_data = []
        
        for ticket_type in ['power', 'flex']:
            for slip in portfolio[ticket_type]:
                slip_row = {
                    'slip_id': slip['slip_id'],
                    'created': datetime.now().isoformat(),
                    'timestamp': datetime.now().isoformat(),
                    'ticket_type': slip['ticket_type'],
                    'props': json.dumps(slip['props']),
                    'n_props': slip['n_props'],
                    'ev': slip['ev'],
                    'stake': slip['stake'],
                    'odds': self._calculate_odds(slip),
                    'status': 'pending',
                    'payout': 0.0,
                    'settled_at': ''
                }
                all_slips_data.append(slip_row)
        
        if all_slips_data:
            try:
                # Check if we have access to spreadsheet
                if hasattr(self.sheet_connector, 'spreadsheet') and self.sheet_connector.spreadsheet:
                    # Try to access slips_log worksheet
                    try:
                        slips_ws = self.sheet_connector.spreadsheet.worksheet('slips_log')
                        slips_df = pd.DataFrame(all_slips_data)
                        
                        # Get existing data
                        existing = slips_ws.get_all_values()
                        
                        # If empty, add headers
                        if not existing:
                            headers = list(slips_df.columns)
                            slips_ws.append_row(headers)
                        
                        # Append each slip
                        for _, row in slips_df.iterrows():
                            values = [str(row[col]) for col in slips_df.columns]
                            slips_ws.append_row(values)
                        
                        print(f"✅ Pushed {len(all_slips_data)} slips to slips_log")
                        return len(all_slips_data)
                    except:
                        print("Note: slips_log worksheet not found")
                        print("To track parlays separately, create a 'slips_log' tab in your Google Sheet")
                        return 0
                else:
                    return 0
                
            except Exception as e:
                print(f"Error accessing slips_log: {e}")
                return 0
        
        return 0
    
    def _push_to_bets_log(self, portfolio: Dict[str, List[Dict]]) -> int:
        """Push individual bets from slips to bets_log worksheet."""
        all_bets_data = []
        
        for ticket_type in ['power', 'flex']:
            for slip in portfolio[ticket_type]:
                # Extract individual props as separate bets
                for prop in slip['props']:
                    bet_row = {
                        'source_id': f"{slip['slip_id']}_{prop['prop_id']}",
                        'timestamp': datetime.now().isoformat(),
                        'player_name': prop.get('player', ''),
                        'market': prop.get('type', ''),
                        'line': prop.get('line', 0),
                        'phase': prop.get('phase', 'unknown'),
                        'adjusted_prediction': prop.get('implied_prob', 0),
                        'wager_amount': slip['stake'] / slip['n_props'],  # Allocate stake evenly
                        'odds': self._calculate_individual_odds(prop),
                        'status': 'pending',
                        'actual_result': '',
                        'result_confirmed': False,
                        'profit_loss': 0.0,
                        'notes': f"Part of {ticket_type.upper()} slip: {slip['slip_id']}"
                    }
                    all_bets_data.append(bet_row)
        
        if all_bets_data:
            try:
                bets_df = pd.DataFrame(all_bets_data)
                success = self.sheet_connector.push_slips(bets_df)
                if success:
                    print(f"✅ Pushed {len(all_bets_data)} individual bets to bets_log")
                return len(all_bets_data) if success else 0
            except Exception as e:
                print(f"Failed to push to bets_log: {e}")
                return 0
        
        return 0
    
    def _calculate_individual_odds(self, prop: Dict) -> float:
        """Calculate decimal odds for an individual prop."""
        # Convert implied probability to decimal odds
        prob = prop.get('implied_prob', 0.5)
        if prob > 0:
            return round(1 / prob, 2)
        return 2.0  # Default
    
    def _calculate_odds(self, slip: Dict) -> float:
        """Calculate decimal odds for a slip."""
        if slip['ticket_type'] == 'POWER':
            # Simple multiplier from payout table
            n_props = slip['n_props']
            power_payouts = self.slip_optimizer.payout_tables['power']
            return power_payouts.get(str(n_props), 0.0)
        else:
            # For FLEX, use approximate weighted average
            # In production, would calculate exact odds
            return 5.0  # Placeholder
    
    def run(self):
        """Execute the complete betting workflow."""
        print(f"Starting betting workflow in {self.mode} mode...")
        
        # Load props
        props_df = self.load_props_data()
        print(f"Loaded {len(props_df)} props")
        
        # Generate slips (parlays)
        portfolio = self.generate_slips(props_df)
        
        # Generate individual bets if enabled
        individual_bets = []
        if self.settings.get('enable_singles', False):
            individual_bets = self.generate_individual_bets(props_df)
            print(f"Generated {len(individual_bets)} individual bets")
        
        # Filter out zero-stake slips
        portfolio['power'] = [s for s in portfolio['power'] if s['stake'] > 0]
        portfolio['flex'] = [s for s in portfolio['flex'] if s['stake'] > 0]
        
        # Push to sheets
        n_slips_pushed = 0
        n_bets_pushed = 0
        
        if self.mode == "PROD" or (self.mode == "TEST" and hasattr(self.sheet_connector, 'spreadsheet')):
            # Push slips
            n_slips_pushed = self.push_slips_to_sheet(portfolio)
            
            # Push individual bets if any
            if individual_bets:
                try:
                    bets_df = pd.DataFrame(individual_bets)
                    if self.sheet_connector.push_slips(bets_df):
                        n_bets_pushed = len(individual_bets)
                        print(f"✅ Pushed {n_bets_pushed} individual bets")
                except Exception as e:
                    print(f"Failed to push individual bets: {e}")
        
        # Print required summary
        print(f"\nPower slips: {len(portfolio['power'])}")
        print(f"Flex slips: {len(portfolio['flex'])}")
        if individual_bets:
            print(f"Individual bets: {len(individual_bets)}")
        
        if self.mode == "TEST" and n_slips_pushed == 0:
            print("✓ bets generated (test mode - sheet sync skipped)")
        elif n_slips_pushed > 0 or n_bets_pushed > 0:
            print("✅ bets synced")
        else:
            print("❌ sync failed")
        
        return {
            'portfolio': portfolio,
            'individual_bets': individual_bets
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run WNBA betting workflow")
    parser.add_argument('--mode', choices=['TEST', 'PROD'], default='PROD',
                        help='Run mode (TEST uses sample data)')
    parser.add_argument('--singles', action='store_true',
                        help='Also generate individual prop bets')
    
    args = parser.parse_args()
    
    # Run workflow
    workflow = BettingWorkflow(mode=args.mode)
    
    # Enable singles if requested
    if args.singles:
        workflow.settings['enable_singles'] = True
    
    result = workflow.run()
    
    # In TEST mode, show sample details
    if args.mode == 'TEST':
        portfolio = result['portfolio']
        if portfolio['power']:
            print("\nSample POWER slip:")
            slip = portfolio['power'][0]
            print(f"  ID: {slip['slip_id']}")
            print(f"  EV: {slip['ev']:.2%}")
            print(f"  Stake: ${slip['stake']}")
            print(f"  Props: {slip['n_props']}")
        
        if args.singles and result['individual_bets']:
            print("\nSample individual bet:")
            bet = result['individual_bets'][0]
            print(f"  Player: {bet['player_name']}")
            print(f"  Market: {bet['market']} {bet['line']}")
            print(f"  Phase: {bet['phase']}")
            print(f"  Stake: ${bet['wager_amount']:.2f}")


if __name__ == "__main__":
    main()
, '').replace(',', '')
                        settings[key] = float(value)
                    except:
                        # Use defaults if conversion fails
                        defaults = {
                            'min_bet': 5.0,
                            'max_bet_pct': 0.10,
                            'bankroll': 1000.0,
                            'power_target': 5,
                            'flex_target': 5
                        }
                        settings[key] = defaults.get(key, 0)
            
            print(f"Loaded settings from Google Sheets")
            return settings
            
        except Exception as e:
            print(f"Warning: Could not load settings from sheet: {e}")
            # Return defaults
            return {
                'min_bet': 5.0,
                'max_bet_pct': 0.10,
                'bankroll': 1000.0,
                'power_target': 5,
                'flex_target': 5,
                'enable_singles': False,
                'singles_allocation': 0.3  # 30% of bankroll for singles
            }
    
    def load_props_data(self) -> pd.DataFrame:
        """Load today's props with phase information."""
        # For TEST mode, generate sample data
        if self.mode == "TEST":
            return self._generate_test_props()
        
        # For PROD mode, would load from actual data source
        # This is a stub - replace with actual data loading
        props_path = Path("data/todays_props.csv")
        if props_path.exists():
            return pd.read_csv(props_path)
        else:
            print("Warning: No props data found, using test data")
            return self._generate_test_props()
    
    def _generate_test_props(self) -> pd.DataFrame:
        """Generate sample props for testing."""
        import numpy as np
        
        np.random.seed(42)  # For reproducibility
        n_props = 30
        
        props = pd.DataFrame({
            'prop_id': [f'TEST_{datetime.now().strftime("%Y%m%d")}_{i:03d}' for i in range(n_props)],
            'player': [f'TestPlayer_{i%10}' for i in range(n_props)],
            'type': ['points'] * 15 + ['rebounds'] * 10 + ['assists'] * 5,
            'line': np.random.uniform(10, 35, n_props),
            'implied_prob': np.random.uniform(0.35, 0.55, n_props),  # More realistic probabilities
            'phase': np.random.choice(['follicular', 'ovulatory', 'luteal', 'menstrual'], n_props),
            'game_time': '7:00 PM ET',
            'opponent': [f'Team_{i%5}' for i in range(n_props)]
        })
        
        return props
    
    def generate_slips(self, props_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Generate optimized portfolio of POWER and FLEX slips."""
        # Get targets from settings or use defaults
        power_target = int(self.settings.get('power_target', 5))
        flex_target = int(self.settings.get('flex_target', 5))
        
        # Generate portfolio
        portfolio = self.slip_optimizer.optimize_portfolio(
            props_df, 
            power_target=power_target,
            flex_target=flex_target
        )
        
        # Add bankroll sizing to each slip
        bankroll = self.settings.get('bankroll', 1000.0)
        
        for ticket_type in ['power', 'flex']:
            for slip in portfolio[ticket_type]:
                # Get phase from first prop (or could aggregate)
                phase = slip['props'][0]['phase']
                
                # Calculate optimal stake
                stake = self.bankroll_optimizer.size_bet(
                    bankroll=bankroll,
                    ev=slip['ev'],
                    phase=phase
                )
                
                slip['stake'] = stake
                slip['phase'] = phase
        
        return portfolio
    
    def generate_individual_bets(self, props_df: pd.DataFrame) -> List[Dict]:
        """Generate individual prop bets with phase-aware sizing."""
        bets = []
        bankroll = self.settings.get('bankroll', 1000.0)
        singles_allocation = self.settings.get('singles_allocation', 0.3)  # 30% for singles
        
        # Allocate portion of bankroll to singles
        singles_bankroll = bankroll * singles_allocation
        
        # Calculate edge for each prop
        # Edge = (Fair odds * Implied prob) - 1
        # For -110 odds, decimal odds = 1.909
        props_df = props_df.copy()
        standard_odds = 1.909  # -110 in decimal
        props_df['edge'] = (standard_odds * props_df['implied_prob']) - 1.0
        
        # Filter positive EV props and sort by edge
        positive_ev = props_df[props_df['edge'] > 0].nlargest(10, 'edge')
        
        bet_counter = 0
        for _, prop in positive_ev.iterrows():
            # Calculate stake using Kelly
            stake = self.bankroll_optimizer.size_bet(
                bankroll=singles_bankroll,
                ev=prop['edge'],
                phase=prop['phase']
            )
            
            if stake > 0:
                bet_counter += 1
                bet = {
                    'source_id': f"SINGLE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{bet_counter:03d}",
                    'timestamp': datetime.now().isoformat(),
                    'player_name': prop['player'],
                    'market': prop['type'],
                    'line': prop['line'],
                    'phase': prop['phase'],
                    'adjusted_prediction': prop['implied_prob'],
                    'wager_amount': stake,
                    'odds': round(1 / prop['implied_prob'], 2),
                    'status': 'pending',
                    'actual_result': '',
                    'result_confirmed': False,
                    'profit_loss': 0.0,
                    'notes': 'Individual prop bet (phase-aware Kelly)'
                }
                bets.append(bet)
        
        return bets
    
    def push_slips_to_sheet(self, portfolio: Dict[str, List[Dict]]) -> int:
        """Push generated slips to Google Sheets."""
        all_slips_data = []
        
        # Combine all slips into DataFrame-ready format
        for ticket_type in ['power', 'flex']:
            for slip in portfolio[ticket_type]:
                # Create dictionary for DataFrame row
                slip_row = {
                    'slip_id': slip['slip_id'],
                    'created': datetime.now().isoformat(),  # Add created timestamp
                    'timestamp': datetime.now().isoformat(),
                    'ticket_type': slip['ticket_type'],
                    'props': json.dumps(slip['props']),  # JSON string
                    'n_props': slip['n_props'],
                    'ev': slip['ev'],
                    'stake': slip['stake'],
                    'odds': self._calculate_odds(slip),
                    'status': 'pending',
                    'payout': 0.0,
                    'settled_at': ''
                }
                all_slips_data.append(slip_row)
        
        # Push to sheet
        if all_slips_data:
            try:
                # Convert to DataFrame
                slips_df = pd.DataFrame(all_slips_data)
                
                # Use the push_slips method which expects a DataFrame
                success = self.sheet_connector.push_slips(slips_df)
                return len(all_slips_data) if success else 0
            except Exception as e:
                print(f"Failed to push slips: {e}")
                # Print more details about the error
                import traceback
                traceback.print_exc()
                return 0
        
        return 0
    
    def _calculate_odds(self, slip: Dict) -> float:
        """Calculate decimal odds for a slip."""
        if slip['ticket_type'] == 'POWER':
            # Simple multiplier from payout table
            n_props = slip['n_props']
            power_payouts = self.slip_optimizer.payout_tables['power']
            return power_payouts.get(str(n_props), 0.0)
        else:
            # For FLEX, use approximate weighted average
            # In production, would calculate exact odds
            return 5.0  # Placeholder
    
    def run(self):
        """Execute the complete betting workflow."""
        print(f"Starting betting workflow in {self.mode} mode...")
        
        # Load props
        props_df = self.load_props_data()
        print(f"Loaded {len(props_df)} props")
        
        # Generate slips
        portfolio = self.generate_slips(props_df)
        
        # Count slips
        n_power = len(portfolio['power'])
        n_flex = len(portfolio['flex'])
        
        # Filter out zero-stake slips
        portfolio['power'] = [s for s in portfolio['power'] if s['stake'] > 0]
        portfolio['flex'] = [s for s in portfolio['flex'] if s['stake'] > 0]
        
        # Push to sheet (skip in TEST mode if connection fails)
        n_pushed = 0
        if self.mode == "PROD" or (self.mode == "TEST" and hasattr(self.sheet_connector, 'worksheet')):
            n_pushed = self.push_slips_to_sheet(portfolio)
        
        # Print required summary
        print(f"\nPower slips: {len(portfolio['power'])}")
        print(f"Flex slips: {len(portfolio['flex'])}")
        if self.mode == "TEST" and n_pushed == 0:
            print("✓ slips generated (test mode - sheet sync skipped)")
        elif n_pushed > 0:
            print("✅ slips synced")
        else:
            print("❌ sync failed")
        
        return portfolio


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run WNBA betting workflow")
    parser.add_argument('--mode', choices=['TEST', 'PROD'], default='PROD',
                        help='Run mode (TEST uses sample data)')
    
    args = parser.parse_args()
    
    # Run workflow
    workflow = BettingWorkflow(mode=args.mode)
    portfolio = workflow.run()
    
    # In TEST mode, show sample slip details
    if args.mode == 'TEST' and portfolio['power']:
        print("\nSample POWER slip:")
        slip = portfolio['power'][0]
        print(f"  ID: {slip['slip_id']}")
        print(f"  EV: {slip['ev']:.2%}")
        print(f"  Stake: ${slip['stake']}")
        print(f"  Props: {slip['n_props']}")


if __name__ == "__main__":
    main()
