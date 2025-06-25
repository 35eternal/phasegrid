#!/usr/bin/env python3
"""
PaperTrader - Integrated with Operations Modules (Fixed Version)
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our operations modules
from src.prediction_engine import PredictionEngine
from src.sheet_repair import SheetRepair
from src.result_ingester import ResultIngester
from src.slip_optimizer import SlipOptimizer
from src.metrics_database import MetricsDatabase
from src.alert_system import AlertSystem, AlertType

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PaperTrader:
    """Enhanced Paper Trader with integrated operations modules."""
    
    def __init__(self, initial_bankroll: float = 1000.0):
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        
        # Initialize all modules
        self.prediction_engine = PredictionEngine()
        self.sheet_repair = SheetRepair()
        self.result_ingester = ResultIngester()
        self.slip_optimizer = SlipOptimizer()
        self.metrics_db = MetricsDatabase()
        self.alert_system = AlertSystem()
        
        # Configuration from environment
        self.high_roi_threshold = float(os.getenv('HIGH_ROI_THRESHOLD', '0.20'))  # 20%
        self.low_roi_threshold = float(os.getenv('LOW_ROI_THRESHOLD', '-0.20'))  # -20%
        
        # Store metrics in a CSV file as backup
        self.metrics_file = "data/paper_metrics.csv"
        
        logger.info(f"PaperTrader initialized with bankroll: ${initial_bankroll}")
        logger.info(f"ROI thresholds - High: {self.high_roi_threshold*100}%, Low: {self.low_roi_threshold*100}%")
    
    def load_prizepicks_lines(self, date: datetime) -> pd.DataFrame:
        """Load PrizePicks lines for a specific date."""
        date_str = date.strftime('%Y%m%d')
        lines_file = f"data/prizepicks_lines_{date_str}.csv"
        
        try:
            if os.path.exists(lines_file):
                lines_df = pd.read_csv(lines_file)
                logger.info(f"Loaded {len(lines_df)} lines from {lines_file}")
                
                # For now, just return the dataframe without repair
                # TODO: Update when SheetRepair method is available
                return lines_df
            else:
                logger.warning(f"Lines file not found: {lines_file}")
                # Fallback to most recent available lines
                return self._load_fallback_lines()
        except Exception as e:
            logger.error(f"Error loading lines: {e}")
            self.alert_system.send_alert(
                AlertType.ERROR,
                f"Failed to load PrizePicks lines for {date_str}",
                {"error": str(e), "file": lines_file}
            )
            return pd.DataFrame()
    
    def _load_fallback_lines(self) -> pd.DataFrame:
        """Load the most recent available lines as fallback."""
        data_dir = "data"
        line_files = [f for f in os.listdir(data_dir) if f.startswith("prizepicks_lines_") and f.endswith(".csv")]
        
        if not line_files:
            logger.error("No line files found in data directory")
            return pd.DataFrame()
        
        # Sort by date and get the most recent
        line_files.sort(reverse=True)
        latest_file = os.path.join(data_dir, line_files[0])
        
        try:
            df = pd.read_csv(latest_file)
            logger.info(f"Using fallback lines from {latest_file}")
            return df
        except Exception as e:
            logger.error(f"Failed to load fallback lines: {e}")
            return pd.DataFrame()
    
    def generate_predictions(self, lines_df: pd.DataFrame) -> List[Dict]:
        """Generate predictions using the PredictionEngine."""
        try:
            predictions = []
            
            # For now, create simple predictions for testing
            for _, line in lines_df.iterrows():
                # Simple prediction logic for testing
                prediction = {
                    'player_name': line.get('player_name'),
                    'prop_type': line.get('prop_type'),
                    'line': line.get('line'),
                    'prediction': 'over',  # Simple prediction
                    'confidence': 0.65,    # Fixed confidence for testing
                    'expected_value': 0.05  # Fixed EV for testing
                }
                predictions.append(prediction)
            
            logger.info(f"Generated {len(predictions)} predictions")
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            self.alert_system.send_alert(
                AlertType.ERROR,
                "Prediction generation failed",
                {"error": str(e)}
            )
            return []
    
    def optimize_slip(self, predictions: List[Dict], max_legs: int = 5) -> List[Dict]:
        """Optimize the betting slip using SlipOptimizer."""
        try:
            # For now, just take the top predictions
            optimized = predictions[:max_legs]
            
            # Add stake to each prediction
            for pred in optimized:
                pred['stake'] = 10.0  # Fixed stake for testing
            
            total_stake = sum(p['stake'] for p in optimized)
            logger.info(f"Optimized slip with {len(optimized)} legs, total stake: ${total_stake:.2f}")
            return optimized
            
        except Exception as e:
            logger.error(f"Error optimizing slip: {e}")
            return predictions[:max_legs]
    
    def simulate_betting_day(self, date: datetime) -> Dict:
        """Simulate a full day of paper trading."""
        logger.info(f"Starting paper trading simulation for {date.strftime('%Y-%m-%d')}")
        
        try:
            # Load lines for the day
            lines_df = self.load_prizepicks_lines(date)
            if lines_df.empty:
                logger.warning("No lines available for trading")
                return {'date': date, 'trades': 0, 'pnl': 0, 'roi': 0}
            
            # Generate predictions
            predictions = self.generate_predictions(lines_df)
            if not predictions:
                logger.warning("No predictions generated")
                return {'date': date, 'trades': 0, 'pnl': 0, 'roi': 0}
            
            # Optimize slip
            optimized_slip = self.optimize_slip(predictions)
            
            # Simulate trades (simplified for testing)
            total_stake = sum(p.get('stake', 10) for p in optimized_slip)
            
            # Simulate some wins and losses
            import random
            random.seed(42)  # For reproducible testing
            
            trades = []
            total_pnl = 0
            
            for pred in optimized_slip:
                win = random.random() < pred['confidence']
                pnl = pred['stake'] * 0.9 if win else -pred['stake']
                total_pnl += pnl
                
                trade = {
                    'player': pred['player_name'],
                    'prop': pred['prop_type'],
                    'stake': pred['stake'],
                    'status': 'won' if win else 'lost',
                    'pnl': pnl
                }
                trades.append(trade)
            
            # Update bankroll
            self.current_bankroll += total_pnl
            roi = total_pnl / total_stake if total_stake > 0 else 0
            
            # Create metrics
            metrics = {
                'date': date.strftime('%Y-%m-%d'),
                'trades': len(trades),
                'total_stake': total_stake,
                'total_pnl': total_pnl,
                'roi': roi,
                'bankroll': self.current_bankroll,
                'win_rate': sum(1 for t in trades if t['status'] == 'won') / len(trades) if trades else 0
            }
            
            # Store metrics in CSV
            self._store_metrics_csv(metrics)
            
            # Check for alerts
            self._check_alerts(metrics)
            
            logger.info(f"Day complete - Trades: {len(trades)}, P&L: ${total_pnl:.2f}, ROI: {roi*100:.1f}%")
            
            # Show trade details
            for trade in trades:
                logger.info(f"  {trade['player']} {trade['prop']}: {trade['status']} (${trade['pnl']:.2f})")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error in betting simulation: {e}")
            self.alert_system.send_alert(
                AlertType.ERROR,
                "Paper trading simulation failed",
                {"date": str(date), "error": str(e)}
            )
            raise
    
    def _store_metrics_csv(self, metrics: Dict):
        """Store metrics in CSV file."""
        import csv
        
        file_exists = os.path.exists(self.metrics_file)
        
        with open(self.metrics_file, 'a', newline='') as f:
            fieldnames = ['date', 'trades', 'total_stake', 'total_pnl', 'roi', 'bankroll', 'win_rate']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({k: metrics[k] for k in fieldnames})
        
        logger.info(f"Metrics stored in {self.metrics_file}")
    
    def _check_alerts(self, metrics: Dict):
        """Check if alerts should be triggered based on metrics."""
        roi = metrics['roi']
        
        if roi > self.high_roi_threshold:
            self.alert_system.send_alert(
                AlertType.HIGH_ROI,
                f"High ROI Alert: {roi*100:.1f}%",
                metrics
            )
        elif roi < self.low_roi_threshold:
            self.alert_system.send_alert(
                AlertType.LOW_ROI,
                f"Low ROI Alert: {roi*100:.1f}%",
                metrics
            )


def main():
    """Main entry point for paper trader."""
    # Initialize trader
    trader = PaperTrader(initial_bankroll=1000.0)
    
    # Run for today
    trader.simulate_betting_day(datetime.now())


if __name__ == "__main__":
    main()
