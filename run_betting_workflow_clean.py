"""
Main betting workflow orchestrator v2 - Clean version.
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
        """Initialize workflow components."""
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
                        value_str = str(settings[key])
                        value_clean = value_str.replace('$', '').replace(',', '')
                        settings[key] = float(value_clean)
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
                'flex_target': 5
            }
    
    def load_props_data(self) -> pd.DataFrame:
        """Load today's props with phase information."""
        # For TEST mode, generate sample data
        if self.mode == "TEST":
            return self._generate_test_props()
        
        # For PROD mode, load from actual data source
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
    
    def push_slips_to_sheet(self, portfolio: Dict[str, List[Dict]]) -> int:
        """Push generated slips to Google Sheets."""
        # Push to bets_log in the format it expects
        return self._push_to_bets_log(portfolio)
    
    def _push_to_bets_log(self, portfolio: Dict[str, List[Dict]]) -> int:
        """Push individual bets from slips to bets_log worksheet."""
        all_bets_data = []
        
        for ticket_type in ['power', 'flex']:
            for slip in portfolio[ticket_type]:
                # For PrizePicks, we'll track the slip as a single entry
                bet_row = {
                    'source_id': slip.get('slip_id', ''),  # Use slip_id as source_id
                    'timestamp': datetime.now().isoformat(),
                    'player_name': f"{ticket_type.upper()} {slip.get('n_props', 0)}-pick",
                    'market': 'parlay',
                    'line': float(slip.get('n_props', 0)),
                    'phase': slip.get('phase', 'unknown'),
                    'adjusted_prediction': float(slip.get('ev', 0)),
                    'wager_amount': float(slip.get('stake', 0)),
                    'odds': float(self._calculate_odds(slip)),
                    'status': 'pending',
                    'actual_result': '',
                    'result_confirmed': False,
                    'profit_loss': 0.0,
                    'notes': json.dumps(slip.get('props', []))  # Store full props in notes
                }
                all_bets_data.append(bet_row)
        
        if all_bets_data:
            try:
                bets_df = pd.DataFrame(all_bets_data)
                print(f"DataFrame created with columns: {list(bets_df.columns)}")
                success = self.sheet_connector.push_slips(bets_df)
                if success:
                    print(f"✅ Pushed {len(all_bets_data)} slips to bets_log")
                return len(all_bets_data) if success else 0
            except Exception as e:
                print(f"Failed to push to bets_log: {e}")
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
            return 5.0  # Placeholder - adjust based on PrizePicks structure
    
    def run(self):
        """Execute the complete betting workflow."""
        print(f"Starting betting workflow in {self.mode} mode...")
        
        # Load props
        props_df = self.load_props_data()
        print(f"Loaded {len(props_df)} props")
        
        # Generate slips
        portfolio = self.generate_slips(props_df)
        
        # Filter out zero-stake slips
        portfolio['power'] = [s for s in portfolio['power'] if s['stake'] > 0]
        portfolio['flex'] = [s for s in portfolio['flex'] if s['stake'] > 0]
        
        # Push to sheet
        n_pushed = 0
        if self.mode == "PROD" or (self.mode == "TEST" and hasattr(self.sheet_connector, 'spreadsheet')):
            n_pushed = self.push_slips_to_sheet(portfolio)
        
        # Print required summary
        print(f"\nPower slips: {len(portfolio['power'])}")
        print(f"Flex slips: {len(portfolio['flex'])}")
        
        if self.mode == "TEST" and n_pushed == 0:
            print("✓ slips generated (test mode - sheet sync skipped)")
        elif n_pushed > 0:
            print("✅ slips synced to Google Sheets")
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