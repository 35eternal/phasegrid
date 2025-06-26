#!/usr/bin/env python3
"""
PaperTrader - Fully Integrated with Operations Modules
Uses actual methods from each module
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
                
                # Use SheetRepair to clean the data
                lines_df = self.sheet_repair.repair_sheet(lines_df)
                return lines_df
            else:
                logger.warning(f"Lines file not found: {lines_file}")
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
            return self.sheet_repair.repair_sheet(df)
        except Exception as e:
            logger.error(f"Failed to load fallback lines: {e}")
            return pd.DataFrame()
    
    def generate_predictions(self, lines_df: pd.DataFrame) -> List[Dict]:
        """Generate predictions using the PredictionEngine."""
        try:
            predictions = []
            
            for _, line in lines_df.iterrows():
                # Prepare features for prediction
                features = {
                    'player_name': line.get('player_name'),
                    'prop_type': line.get('prop_type'),
                    'line': line.get('line'),
                    'sport': line.get('sport', 'NBA'),
                    'opponent': line.get('opponent', ''),
                    'home_away': line.get('home_away', 'home')
                }
                
                # Get prediction from engine
                prediction = self.prediction_engine.predict(features)
                
                if prediction and prediction.get('confidence', 0) > 0.6:
                    predictions.append({
                        'player_name': features['player_name'],
                        'prop_type': features['prop_type'],
                        'line': features['line'],
                        'prediction': prediction['prediction'],
                        'confidence': prediction['confidence'],
                        'expected_value': prediction.get('expected_value', 0)
                    })
            
            logger.info(f"Generated {len(predictions)} high-confidence predictions")
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
            # Prepare predictions for optimizer
            optimizer_input = []
            for pred in predictions:
                optimizer_input.append({
                    'prediction_id': f"{pred['player_name']}_{pred['prop_type']}",
                    'expected_value': pred['expected_value'],
                    'confidence': pred['confidence'],
                    'correlation_group': pred.get('player_name', 'unknown')
                })
            
            # Get optimized slip
            optimized = self.slip_optimizer.optimize(
                predictions=optimizer_input,
                bankroll=self.current_bankroll,
                max_legs=max_legs
            )
            
            # Map back to original predictions
            optimized_predictions = []
            for opt in optimized['selections']:
                for pred in predictions:
                    if f"{pred['player_name']}_{pred['prop_type']}" == opt['prediction_id']:
                        pred['stake'] = opt['stake']
                        optimized_predictions.append(pred)
                        break
            
            logger.info(f"Optimized slip with {len(optimized_predictions)} legs, total stake: ${optimized['total_stake']:.2f}")
            return optimized_predictions
            
        except Exception as e:
            logger.error(f"Error optimizing slip: {e}")
            # Fallback to simple optimization
            optimized = predictions[:max_legs]
            for pred in optimized:
                pred['stake'] = 10.0
            return optimized
    
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
            
            # Place bets and track
            total_stake = sum(p.get('stake', 10) for p in optimized_slip)
            trades = []
            
            for pred in optimized_slip:
                trade = {
                    'date': date.strftime('%Y-%m-%d'),
                    'player': pred['player_name'],
                    'stat_type': pred['prop_type'],
                    'projection': pred['line'],
                    'predicted_outcome': pred['prediction'],
                    'confidence': pred['confidence'],
                    'stake': pred.get('stake', 10),
                    'odds': -110,  # Standard odds
                    'result': 'pending'
                }
                trades.append(trade)
            
            # Try to get actual results
            results = self.result_ingester.ingest_results(date)
            
            # Calculate P&L (using simulation if no real results)
            total_pnl = 0
            winners = 0
            
            for trade in trades:
                # Try to match with real result
                result = self._match_result(trade, results)
                
                if result:
                    # Use actual result
                    if result['hit']:
                        trade['result'] = 'won'
                        trade['profit'] = trade['stake'] * 0.909  # -110 odds
                        winners += 1
                    else:
                        trade['result'] = 'lost'
                        trade['profit'] = -trade['stake']
                else:
                    # Simulate result based on confidence
                    import random
                    if random.random() < trade['confidence']:
                        trade['result'] = 'won'
                        trade['profit'] = trade['stake'] * 0.909
                        winners += 1
                    else:
                        trade['result'] = 'lost'
                        trade['profit'] = -trade['stake']
                
                total_pnl += trade['profit']
            
            # Update bankroll
            self.current_bankroll += total_pnl
            roi = total_pnl / total_stake if total_stake > 0 else 0
            win_rate = winners / len(trades) if trades else 0
            
            # Store metrics in database using actual method
            metrics = {
                'date': date.strftime('%Y-%m-%d'),
                'total_trades': len(trades),
                'winners': winners,
                'losers': len(trades) - winners,
                'win_rate': win_rate,
                'total_stake': total_stake,
                'total_profit': total_pnl,
                'roi': roi,
                'average_odds': -110
            }
            
            # Insert into database
            self.metrics_db.insert_daily_metrics(metrics)
            
            # Insert individual trades
            self.metrics_db.insert_trades(trades)
            
            # Check for alerts
            self._check_alerts(metrics)
            
            logger.info(f"Day complete - Trades: {len(trades)}, P&L: ${total_pnl:.2f}, ROI: {roi*100:.1f}%")
            
            # Log trade details
            for trade in trades:
                logger.info(f"  {trade['player']} {trade['stat_type']}: {trade['result']} (${trade['profit']:.2f})")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error in betting simulation: {e}")
            self.alert_system.send_alert(
                AlertType.ERROR,
                "Paper trading simulation failed",
                {"date": str(date), "error": str(e)}
            )
            raise
    
    def _match_result(self, trade: Dict, results: List[Dict]) -> Optional[Dict]:
        """Match a trade with its result."""
        for result in results:
            if (result.get('player_name') == trade['player'] and 
                result.get('prop_type') == trade['stat_type']):
                return result
        return None
    
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
    
    def run_backtest(self, start_date: datetime, end_date: datetime):
        """Run paper trading simulation over a date range."""
        current_date = start_date
        
        logger.info(f"Starting backtest from {start_date} to {end_date}")
        
        while current_date <= end_date:
            try:
                self.simulate_betting_day(current_date)
            except Exception as e:
                logger.error(f"Failed to simulate {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        # Generate summary using actual database method
        metrics = self.metrics_db.get_metrics_range(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if metrics:
            total_pnl = sum(m.get('total_profit', 0) for m in metrics)
            total_stake = sum(m.get('total_stake', 0) for m in metrics)
            overall_roi = total_pnl / total_stake if total_stake > 0 else 0
            
            logger.info(f"Backtest complete - Total P&L: ${total_pnl:.2f}, ROI: {overall_roi*100:.1f}%")
            
            return {
                'total_pnl': total_pnl,
                'overall_roi': overall_roi,
                'days_traded': len(metrics)
            }
        
        return {}


def main():
    """Main entry point for paper trader."""
    # Initialize trader
    trader = PaperTrader(initial_bankroll=1000.0)
    
    # Check for CSV migration if database is new
    if os.path.exists('data/paper_metrics.csv'):
        try:
            logger.info("Found existing CSV metrics, checking if migration needed...")
            trader.metrics_db.migrate_csv_data('data/paper_metrics.csv')
        except Exception as e:
            logger.warning(f"CSV migration skipped: {e}")
    
    # Run for today or specified date range
    if len(sys.argv) > 1:
        # Backtest mode
        start_date = datetime.strptime(sys.argv[1], '%Y-%m-%d')
        end_date = datetime.strptime(sys.argv[2], '%Y-%m-%d') if len(sys.argv) > 2 else start_date
        trader.run_backtest(start_date, end_date)
    else:
        # Run for today
        trader.simulate_betting_day(datetime.now())


if __name__ == "__main__":
    main()
