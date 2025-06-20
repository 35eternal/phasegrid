"""
WNBA Integrated Backtesting System
=================================
Combines the existing backtester architecture with the prediction engine
to create a unified system that leverages the 37.7% ROI model.

Version: 2.0 - Integrated with PredictionEngine
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
import warnings
from dataclasses import dataclass
from scipy import optimize
import json
import os
from pathlib import Path

# Import the existing prediction engine
try:
    from core.prediction_engine import PredictionEngine
except ImportError:
    print("Warning: PredictionEngine not found. Using fallback prediction logic.")
    PredictionEngine = None

# Suppress pandas warnings for cleaner output
warnings.filterwarnings('ignore')

@dataclass
class BacktestConfig:
    """Configuration class for backtesting parameters"""
    start_date: str = "2023-05-01"
    end_date: str = "2024-09-30"
    min_games_for_prediction: int = 5
    volatility_window: int = 10
    cycle_window: int = 5
    confidence_threshold: float = 0.15  # Lowered from 0.65 to get more bets
    kelly_fraction: float = 0.25
    max_bet_size: float = 100.0
    initial_bankroll: float = 10000.0
    prop_types: List[str] = None
    line_variance: float = 0.1  # Variance in synthetic prop lines
    
    def __post_init__(self):
        if self.prop_types is None:
            self.prop_types = ['PTS', 'REB', 'AST', 'STL', 'BLK']
    
@dataclass
class PropLine:
    """Represents a synthetic prop betting line"""
    player_name: str
    game_date: str
    stat_type: str
    line_value: float
    over_odds: float = -110
    under_odds: float = -110
    
@dataclass
class PredictionResult:
    """Stores prediction results for a single prop"""
    player_name: str
    game_date: str
    stat_type: str
    line_value: float
    prediction: str  # 'OVER', 'UNDER', 'SKIP'
    confidence: float
    actual_value: float
    result: str  # 'WIN', 'LOSS', 'PUSH', 'NO_BET'
    ev: float
    recommended_bet: float
    volatility_score: float = 0.0
    trend_direction: str = 'neutral'
    bankroll_after: float = 0.0

class IntegratedWNBABacktester:
    """
    Integrated backtesting system that combines the existing PredictionEngine
    with comprehensive backtesting infrastructure.
    """
    
    def __init__(self, config: BacktestConfig = None):
        """Initialize the backtester with configuration."""
        self.config = config or BacktestConfig()
        self.historical_data = None
        self.synthetic_props = []
        self.prediction_results = []
        self.portfolio_history = []
        self.optimization_results = {}
        
        # Initialize prediction engine if available
        self.prediction_engine = PredictionEngine() if PredictionEngine else None
        
    def load_historical_data(self, filepath: str = "data/wnba_combined_gamelogs.csv") -> pd.DataFrame:
        """Load historical game log data with proper column mapping."""
        try:
            df = pd.read_csv(filepath)
            
            # Map column names to standardized format
            column_mapping = {
                'Date': 'GAME_DATE',
                'Player': 'PLAYER_NAME',
                'GAME_DATE': 'GAME_DATE',  # In case it's already correct
                'PLAYER_NAME': 'PLAYER_NAME'
            }
            
            # Apply column mapping if needed
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns and new_col not in df.columns:
                    df[new_col] = df[old_col]
            
            # Ensure required columns exist
            required_cols = ['GAME_DATE', 'PLAYER_NAME', 'PTS', 'REB', 'AST']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Standardize date format
            df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
            df = df.sort_values(['PLAYER_NAME', 'GAME_DATE']).reset_index(drop=True)
            
            # Filter by date range
            start_date = pd.to_datetime(self.config.start_date)
            end_date = pd.to_datetime(self.config.end_date)
            df = df[(df['GAME_DATE'] >= start_date) & (df['GAME_DATE'] <= end_date)]
            
            print(f"✅ Loaded {len(df)} game logs from {df['GAME_DATE'].min()} to {df['GAME_DATE'].max()}")
            print(f"   Unique players: {df['PLAYER_NAME'].nunique()}")
            print(f"   Available stats: {[col for col in df.columns if col in self.config.prop_types]}")
            
            self.historical_data = df
            return df
            
        except Exception as e:
            raise Exception(f"Error loading historical data: {str(e)}")
    
    def generate_synthetic_props(self) -> List[PropLine]:
        """Generate synthetic historical prop lines based on actual game data."""
        if self.historical_data is None:
            raise ValueError("Must load historical data first")
        
        synthetic_props = []
        prop_count_by_stat = {}
        
        # Group by player and generate props for each game
        for player in self.historical_data['PLAYER_NAME'].unique():
            player_data = self.historical_data[self.historical_data['PLAYER_NAME'] == player].copy()
            player_data = player_data.sort_values('GAME_DATE')
            
            for idx, row in player_data.iterrows():
                game_date = row['GAME_DATE']
                
                # Only use data from before this game (no future leakage)
                historical_games = player_data[player_data['GAME_DATE'] < game_date]
                
                # Need minimum games for realistic prop generation
                if len(historical_games) < self.config.min_games_for_prediction:
                    continue
                
                # Generate props for each stat type
                for stat_type in self.config.prop_types:
                    if stat_type in historical_games.columns:
                        # Calculate recent average (last 10 games or all available)
                        recent_games = historical_games.tail(10)
                        if len(recent_games[stat_type].dropna()) == 0:
                            continue
                            
                        avg_value = recent_games[stat_type].mean()
                        
                        # Add realistic variance to line setting
                        variance = avg_value * self.config.line_variance
                        line_noise = np.random.normal(0, variance)
                        
                        # Market typically sets lines slightly favorable to house
                        market_adjustment = 0.05 * avg_value  # 5% house edge
                        line_value = avg_value + market_adjustment + line_noise
                        
                        # Round to realistic increments (0.5)
                        line_value = max(0.5, round(line_value * 2) / 2)
                        
                        prop = PropLine(
                            player_name=player,
                            game_date=game_date.strftime('%Y-%m-%d'),
                            stat_type=stat_type,
                            line_value=line_value
                        )
                        synthetic_props.append(prop)
                        
                        # Track counts
                        prop_count_by_stat[stat_type] = prop_count_by_stat.get(stat_type, 0) + 1
        
        print(f"✅ Generated {len(synthetic_props)} synthetic prop lines:")
        for stat, count in prop_count_by_stat.items():
            print(f"   {stat}: {count} props")
        
        self.synthetic_props = synthetic_props
        return synthetic_props
    
    def simulate_predictions(self) -> List[PredictionResult]:
        """Simulate predictions using the integrated prediction engine."""
        if not self.synthetic_props:
            raise ValueError("Must generate synthetic props first")
        
        if self.historical_data is None:
            raise ValueError("Must load historical data first")
        
        prediction_results = []
        current_bankroll = self.config.initial_bankroll
        
        # Track portfolio history
        self.portfolio_history = [{'date': None, 'bankroll': current_bankroll, 'bets': 0}]
        
        print(f"🎯 Simulating predictions on {len(self.synthetic_props)} props...")
        
        for i, prop in enumerate(self.synthetic_props):
            if i % 100 == 0:
                print(f"   Processed {i}/{len(self.synthetic_props)} props...")
                
            try:
                # Get actual game result
                game_data = self.historical_data[
                    (self.historical_data['PLAYER_NAME'] == prop.player_name) &
                    (self.historical_data['GAME_DATE'] == pd.to_datetime(prop.game_date))
                ]
                
                if game_data.empty:
                    continue
                
                actual_value = game_data.iloc[0][prop.stat_type]
                if pd.isna(actual_value):
                    continue
                
                # Get historical data up to (but not including) game date
                historical_data = self.historical_data[
                    (self.historical_data['PLAYER_NAME'] == prop.player_name) &
                    (self.historical_data['GAME_DATE'] < pd.to_datetime(prop.game_date))
                ]
                
                if len(historical_data) < self.config.min_games_for_prediction:
                    continue
                
                # Use integrated prediction engine if available
                if self.prediction_engine:
                    prediction_data = self._use_prediction_engine(historical_data, prop)
                else:
                    prediction_data = self._fallback_prediction(historical_data, prop)
                
                # Extract prediction details
                prediction = prediction_data['recommendation'].upper()
                confidence = abs(prediction_data.get('confidence', 0.0))
                ev = prediction_data.get('expected_value', 0.0)
                volatility_score = prediction_data.get('volatility_score', 0.0)
                trend_direction = prediction_data.get('trend_direction', 'neutral')
                
                # Apply confidence threshold
                if confidence < self.config.confidence_threshold:
                    prediction = 'SKIP'
                
                # Calculate bet sizing using Kelly criterion
                if prediction != 'SKIP' and ev > 0:
                    kelly_stake = prediction_data.get('kelly_stake', 0.0)
                    bet_size = min(
                        current_bankroll * kelly_stake * self.config.kelly_fraction,
                        self.config.max_bet_size
                    )
                    bet_size = max(bet_size, 0)
                else:
                    bet_size = 0
                
                # Determine actual result
                if prediction == 'SKIP' or bet_size == 0:
                    result = 'NO_BET'
                    payout = 0
                elif prediction == 'OVER' and actual_value > prop.line_value:
                    result = 'WIN'
                    payout = bet_size * (100/110)  # -110 odds payout
                elif prediction == 'UNDER' and actual_value < prop.line_value:
                    result = 'WIN'
                    payout = bet_size * (100/110)
                elif actual_value == prop.line_value:
                    result = 'PUSH'
                    payout = 0  # Money returned
                else:
                    result = 'LOSS'
                    payout = -bet_size
                
                # Update bankroll
                if result != 'NO_BET':
                    current_bankroll += payout
                
                prediction_result = PredictionResult(
                    player_name=prop.player_name,
                    game_date=prop.game_date,
                    stat_type=prop.stat_type,
                    line_value=prop.line_value,
                    prediction=prediction,
                    confidence=confidence,
                    actual_value=actual_value,
                    result=result,
                    ev=ev,
                    recommended_bet=bet_size,
                    volatility_score=volatility_score,
                    trend_direction=trend_direction,
                    bankroll_after=current_bankroll
                )
                
                prediction_results.append(prediction_result)
                
                # Update portfolio history for placed bets
                if result != 'NO_BET':
                    self.portfolio_history.append({
                        'date': pd.to_datetime(prop.game_date),
                        'bankroll': current_bankroll,
                        'bets': len([r for r in prediction_results if r.result != 'NO_BET'])
                    })
                
            except Exception as e:
                print(f"⚠️  Error processing prop {prop.player_name} {prop.stat_type}: {str(e)}")
                continue
        
        print(f"✅ Generated {len(prediction_results)} prediction results")
        bets_placed = len([r for r in prediction_results if r.result != 'NO_BET'])
        print(f"   Bets placed: {bets_placed}")
        
        self.prediction_results = prediction_results
        return prediction_results
    
    def _use_prediction_engine(self, historical_data: pd.DataFrame, prop: PropLine) -> Dict:
        """Use the integrated prediction engine for predictions."""
        try:
            # Extract stat values for the prediction engine
            stat_values = historical_data[prop.stat_type].dropna().values
            
            if len(stat_values) < self.config.min_games_for_prediction:
                return self._fallback_prediction(historical_data, prop)
            
            # Use the existing prediction engine
            prediction = self.prediction_engine.predict_over_under(
                stat_values,
                prop.line_value,
                volatility_window=self.config.volatility_window,
                cycle_window=self.config.cycle_window
            )
            
            return prediction
            
        except Exception as e:
            print(f"   PredictionEngine failed, using fallback: {e}")
            return self._fallback_prediction(historical_data, prop)
    
    def _fallback_prediction(self, historical_data: pd.DataFrame, prop: PropLine) -> Dict:
        """Fallback prediction logic if PredictionEngine unavailable."""
        stat_values = historical_data[prop.stat_type].dropna().values
        
        if len(stat_values) < 3:
            return {
                'recommendation': 'skip',
                'confidence': 0.0,
                'expected_value': 0.0,
                'volatility_score': 1.0,
                'trend_direction': 'neutral',
                'kelly_stake': 0.0
            }
        
        recent_avg = np.mean(stat_values[-5:])  # Last 5 games
        long_term_avg = np.mean(stat_values)
        volatility = np.std(stat_values) / np.mean(stat_values) if np.mean(stat_values) > 0 else 1.0
        
        # Simple prediction logic
        diff_from_line = abs(recent_avg - prop.line_value) / prop.line_value
        base_confidence = max(0.0, min(0.3, 1.0 - diff_from_line * 2))  # Max 30% confidence
        
        # Adjust for volatility
        volatility_adjustment = max(0.5, 1.0 - volatility)
        final_confidence = base_confidence * volatility_adjustment
        
        recommendation = 'over' if recent_avg > prop.line_value else 'under'
        
        # Simple EV calculation
        implied_prob = 110 / (110 + 100)  # -110 odds
        our_prob = 0.5 + final_confidence  # Slight edge
        ev = (our_prob * (100/110) - (1 - our_prob)) if our_prob > implied_prob else 0.0
        
        return {
            'recommendation': recommendation,
            'confidence': final_confidence,
            'expected_value': ev,
            'volatility_score': volatility,
            'trend_direction': 'up' if recent_avg > long_term_avg else 'down',
            'kelly_stake': max(0.0, (our_prob - implied_prob) / (100/110)) if ev > 0 else 0.0
        }
    
    def calculate_performance_metrics(self) -> Dict[str, float]:
        """Calculate comprehensive performance metrics."""
        if not self.prediction_results:
            raise ValueError("Must run simulate_predictions first")
        
        # Filter to only bets that were placed
        placed_bets = [r for r in self.prediction_results if r.result != 'NO_BET']
        
        if not placed_bets:
            return {"error": "No bets were placed", "total_props_evaluated": len(self.prediction_results)}
        
        # Basic metrics
        total_bets = len(placed_bets)
        wins = len([r for r in placed_bets if r.result == 'WIN'])
        losses = len([r for r in placed_bets if r.result == 'LOSS'])
        pushes = len([r for r in placed_bets if r.result == 'PUSH'])
        
        win_rate = wins / total_bets if total_bets > 0 else 0
        
        # Financial metrics
        total_wagered = sum([r.recommended_bet for r in placed_bets])
        total_profit = sum([
            r.recommended_bet * (100/110) if r.result == 'WIN' else
            0 if r.result == 'PUSH' else
            -r.recommended_bet
            for r in placed_bets
        ])
        
        roi = (total_profit / total_wagered * 100) if total_wagered > 0 else 0
        
        # Advanced metrics
        final_bankroll = placed_bets[-1].bankroll_after if placed_bets else self.config.initial_bankroll
        bankroll_return = ((final_bankroll - self.config.initial_bankroll) / self.config.initial_bankroll * 100)
        
        # Sharpe ratio calculation
        if len(placed_bets) > 1:
            returns = [(r.recommended_bet * (100/110) if r.result == 'WIN' else
                       0 if r.result == 'PUSH' else -r.recommended_bet) / r.recommended_bet
                      for r in placed_bets]
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Breakdown by prediction type
        over_bets = [r for r in placed_bets if r.prediction == 'OVER']
        under_bets = [r for r in placed_bets if r.prediction == 'UNDER']
        
        return {
            'total_bets': total_bets,
            'win_rate': round(win_rate * 100, 2),
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'roi': round(roi, 2),
            'total_wagered': round(total_wagered, 2),
            'total_profit': round(total_profit, 2),
            'final_bankroll': round(final_bankroll, 2),
            'bankroll_return': round(bankroll_return, 2),
            'sharpe_ratio': round(sharpe_ratio, 3),
            'over_bets': len(over_bets),
            'under_bets': len(under_bets),
            'over_win_rate': round(len([r for r in over_bets if r.result == 'WIN']) / len(over_bets) * 100, 2) if over_bets else 0,
            'under_win_rate': round(len([r for r in under_bets if r.result == 'WIN']) / len(under_bets) * 100, 2) if under_bets else 0,
            'avg_confidence': round(np.mean([r.confidence for r in placed_bets]), 3),
            'avg_bet_size': round(np.mean([r.recommended_bet for r in placed_bets]), 2),
            'avg_ev': round(np.mean([r.ev for r in placed_bets]), 4),
            'total_props_evaluated': len(self.prediction_results)
        }
    
    def optimize_parameters(self, param_ranges: Dict[str, Tuple[float, float]] = None) -> Dict[str, float]:
        """Optimize model parameters to maximize ROI."""
        if not self.prediction_results:
            raise ValueError("Must run simulate_predictions first")
        
        if param_ranges is None:
            param_ranges = {
                'confidence_threshold': (0.05, 0.30),
                'kelly_fraction': (0.10, 0.50),
                'volatility_window': (5, 15),
                'cycle_window': (3, 8)
            }
        
        # Store original synthetic props for re-running
        original_props = self.synthetic_props.copy()
        
        def objective_function(params):
            """Objective function to maximize (negative ROI for minimization)"""
            # Update config with new parameters
            old_values = {
                'confidence_threshold': self.config.confidence_threshold,
                'kelly_fraction': self.config.kelly_fraction,
                'volatility_window': self.config.volatility_window,
                'cycle_window': self.config.cycle_window
            }
            
            self.config.confidence_threshold = params[0]
            self.config.kelly_fraction = params[1]
            self.config.volatility_window = int(params[2])
            self.config.cycle_window = int(params[3])
            
            try:
                # Re-run predictions with new parameters
                self.synthetic_props = original_props.copy()
                self.simulate_predictions()
                metrics = self.calculate_performance_metrics()
                
                # Return negative ROI (for minimization)
                roi = metrics.get('roi', -100)
                
                # Penalize if too few bets placed
                if metrics.get('total_bets', 0) < 50:
                    roi -= 10
                
                return -roi
                
            except Exception as e:
                print(f"   Optimization iteration failed: {e}")
                return 100  # Large penalty for failed iterations
            
            finally:
                # Restore old config
                for key, value in old_values.items():
                    setattr(self.config, key, value)
        
        # Set up optimization bounds
        bounds = [param_ranges[param] for param in ['confidence_threshold', 'kelly_fraction', 'volatility_window', 'cycle_window']]
        
        # Initial guess
        x0 = [
            self.config.confidence_threshold,
            self.config.kelly_fraction,
            self.config.volatility_window,
            self.config.cycle_window
        ]
        
        print("🔧 Starting parameter optimization...")
        
        try:
            # Run optimization
            result = optimize.minimize(
                objective_function,
                x0,
                bounds=bounds,
                method='L-BFGS-B',
                options={'maxiter': 20}  # Limit iterations for faster results
            )
            
            optimal_params = {
                'confidence_threshold': round(result.x[0], 3),
                'kelly_fraction': round(result.x[1], 3),
                'volatility_window': int(result.x[2]),
                'cycle_window': int(result.x[3]),
                'optimized_roi': round(-result.fun, 2)
            }
            
            self.optimization_results = optimal_params
            
            print(f"✅ Optimization completed. Best ROI: {optimal_params['optimized_roi']:.2f}%")
            return optimal_params
            
        except Exception as e:
            print(f"❌ Optimization failed: {str(e)}")
            return {}
    
    def generate_comprehensive_report(self, save_path: str = None) -> str:
        """Generate a comprehensive backtesting report."""
        if not self.prediction_results:
            raise ValueError("Must run simulate_predictions first")
        
        metrics = self.calculate_performance_metrics()
        
        # Generate report
        report = f"""
{'='*60}
WNBA INTEGRATED PROP BETTING BACKTEST REPORT
{'='*60}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: {self.config.start_date} to {self.config.end_date}

PERFORMANCE SUMMARY:
{'─'*40}
• Total Props Evaluated: {metrics.get('total_props_evaluated', 0)}
• Total Bets Placed: {metrics.get('total_bets', 0)}
• Overall Win Rate: {metrics.get('win_rate', 0)}%
• Return on Investment: {metrics.get('roi', 0)}%
• Bankroll Return: {metrics.get('bankroll_return', 0)}%
• Sharpe Ratio: {metrics.get('sharpe_ratio', 0)}

FINANCIAL RESULTS:
{'─'*40}
• Starting Bankroll: ${self.config.initial_bankroll:,.2f}
• Final Bankroll: ${metrics.get('final_bankroll', 0):,.2f}
• Total Wagered: ${metrics.get('total_wagered', 0):,.2f}
• Total Profit/Loss: ${metrics.get('total_profit', 0):,.2f}
• Average Bet Size: ${metrics.get('avg_bet_size', 0):.2f}

BET BREAKDOWN:
{'─'*40}
• Wins: {metrics.get('wins', 0)}
• Losses: {metrics.get('losses', 0)}
• Pushes: {metrics.get('pushes', 0)}
• OVER Bets: {metrics.get('over_bets', 0)} (Win Rate: {metrics.get('over_win_rate', 0)}%)
• UNDER Bets: {metrics.get('under_bets', 0)} (Win Rate: {metrics.get('under_win_rate', 0)}%)

PREDICTION QUALITY:
{'─'*40}
• Average Confidence: {metrics.get('avg_confidence', 0):.3f}
• Average Expected Value: {metrics.get('avg_ev', 0):.4f}
• Prediction Engine: {"Integrated PredictionEngine" if self.prediction_engine else "Fallback Logic"}

CONFIGURATION USED:
{'─'*40}
• Confidence Threshold: {self.config.confidence_threshold}
• Kelly Fraction: {self.config.kelly_fraction}
• Volatility Window: {self.config.volatility_window}
• Cycle Window: {self.config.cycle_window}
• Min Games Required: {self.config.min_games_for_prediction}
• Max Bet Size: ${self.config.max_bet_size}

"""
        
        # Add optimization results if available
        if self.optimization_results:
            report += f"""OPTIMIZATION RESULTS:
{'─'*40}
• Optimized Confidence Threshold: {self.optimization_results.get('confidence_threshold', 'N/A')}
• Optimized Kelly Fraction: {self.optimization_results.get('kelly_fraction', 'N/A')}
• Optimized Volatility Window: {self.optimization_results.get('volatility_window', 'N/A')}
• Optimized Cycle Window: {self.optimization_results.get('cycle_window', 'N/A')}
• Optimized ROI: {self.optimization_results.get('optimized_roi', 'N/A')}%

"""
        
        # Add stat type breakdown
        if self.prediction_results:
            placed_bets = [r for r in self.prediction_results if r.result != 'NO_BET']
            stat_breakdown = {}
            
            for result in placed_bets:
                stat = result.stat_type
                if stat not in stat_breakdown:
                    stat_breakdown[stat] = {'bets': 0, 'wins': 0, 'total_profit': 0}
                stat_breakdown[stat]['bets'] += 1
                if result.result == 'WIN':
                    stat_breakdown[stat]['wins'] += 1
                    stat_breakdown[stat]['total_profit'] += result.recommended_bet * (100/110)
                elif result.result == 'LOSS':
                    stat_breakdown[stat]['total_profit'] -= result.recommended_bet
            
            report += f"""STAT TYPE PERFORMANCE:
{'─'*40}
"""
            for stat, data in sorted(stat_breakdown.items()):
                win_rate = (data['wins'] / data['bets'] * 100) if data['bets'] > 0 else 0
                profit = data['total_profit']
                report += f"• {stat}: {data['bets']} bets, {win_rate:.1f}% win rate, ${profit:.2f} profit\n"
        
        report += f"\n{'='*60}\n"
        
        # Save report if path provided
        if save_path:
            try:
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'w') as f:
                    f.write(report)
                print(f"📄 Report saved to {save_path}")
            except Exception as e:
                print(f"❌ Error saving report: {str(e)}")
        
        return report
    
    def run_full_backtest(self, data_path: str = "data/wnba_combined_gamelogs.csv", 
                         optimize: bool = False, save_results: bool = True) -> Dict:
        """Run complete backtesting pipeline."""
        print("🚀 Starting integrated WNBA backtest pipeline...")
        
        try:
            # Step 1: Load data
            print("\n1️⃣ Loading historical data...")
            self.load_historical_data(data_path)
            
            # Step 2: Generate props
            print("\n2️⃣ Generating synthetic prop lines...")
            self.generate_synthetic_props()
            
            # Step 3: Run predictions
            print("\n3️⃣ Simulating predictions...")
            self.simulate_predictions()
            
            # Step 4: Calculate results
            print("\n4️⃣ Calculating performance metrics...")
            metrics = self.calculate_performance_metrics()
            
            # Step 5: Optimize if requested
            if optimize:
                print("\n5️⃣ Optimizing parameters...")
                self.optimize_parameters()
            
            # Step 6: Generate report
            print("\n6️⃣ Generating comprehensive report...")
            report_path = "output/integrated_backtest_report.txt" if save_results else None
            report = self.generate_comprehensive_report(report_path)
            
            # Save detailed results
            if save_results:
                self._save_detailed_results()
            
            print("\n✅ Backtest completed successfully!")
            print(f"📊 Win Rate: {metrics.get('win_rate', 0)}% | ROI: {metrics.get('roi', 0)}% | Bets: {metrics.get('total_bets', 0)}")
            
            return {
                'metrics': metrics,
                'optimization': self.optimization_results,
                'report': report,
                'prediction_count': len(self.prediction_results),
                'prop_count': len(self.synthetic_props)
            }
            
        except Exception as e:
            print(f"❌ Backtest failed: {str(e)}")
            raise e
    
    def _save_detailed_results(self):
        """Save detailed results to JSON files."""
        try:
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            # Save detailed results
            results_data = {
                'config': {
                    'start_date': self.config.start_date,
                    'end_date': self.config.end_date,
                    'confidence_threshold': self.config.confidence_threshold,
                    'kelly_fraction': self.config.kelly_fraction,
                    'volatility_window': self.config.volatility_window,
                    'cycle_window': self.config.cycle_window
                },
                'metrics': self.calculate_performance_metrics(),
                'optimization': self.optimization_results,
                'bet_history': [
                    {
                        'player': r.player_name,
                        'date': r.game_date,
                        'stat': r.stat_type,
                        'line': r.line_value,
                        'actual': r.actual_value,
                        'prediction': r.prediction,
                        'confidence': r.confidence,
                        'ev': r.ev,
                        'bet_size': r.recommended_bet,
                        'result': r.result,
                        'bankroll_after': r.bankroll_after
                    }
                    for r in self.prediction_results if r.result != 'NO_BET'
                ]
            }
            
            with open(output_dir / "integrated_backtest_results.json", 'w') as f:
                json.dump(results_data, f, indent=2, default=str)
            
            print(f"💾 Detailed results saved to output/integrated_backtest_results.json")
            
        except Exception as e:
            print(f"⚠️  Could not save detailed results: {e}")


# Convenience functions for easy usage
def run_quick_integrated_backtest(config_overrides: Dict = None) -> Dict:
    """Run a quick backtest with integrated prediction engine."""
    config = BacktestConfig()
    
    if config_overrides:
        for key, value in config_overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    backtester = IntegratedWNBABacktester(config)
    return backtester.run_full_backtest(optimize=False)

def run_optimized_backtest(data_path: str = "data/wnba_combined_gamelogs.csv") -> Dict:
    """Run backtest with parameter optimization."""
    config = BacktestConfig(
        confidence_threshold=0.12,  # Start with reasonable threshold
        kelly_fraction=0.20,
        start_date="2024-05-01",
        end_date="2024-09-30"
    )
    
    backtester = IntegratedWNBABacktester(config)
    return backtester.run_full_backtest(data_path, optimize=True)


# Example usage
if __name__ == "__main__":
    print("🏀 WNBA Integrated Backtesting System")
    print("="*50)
    
    # Quick test configuration
    test_config = BacktestConfig(
        start_date="2024-06-01",
        end_date="2024-08-31",
        confidence_threshold=0.10,  # Lower threshold for more bets
        kelly_fraction=0.15,
        min_games_for_prediction=5
    )
    
    try:
        backtester = IntegratedWNBABacktester(test_config)
        results = backtester.run_full_backtest(optimize=False)
        
        print(f"\n🎉 BACKTEST COMPLETED!")
        print(f"📊 Total Bets: {results['metrics']['total_bets']}")
        print(f"🎯 Win Rate: {results['metrics']['win_rate']}%")
        print(f"💰 ROI: {results['metrics']['roi']}%")
        print(f"💵 Final Bankroll: ${results['metrics']['final_bankroll']:,.2f}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Make sure data/wnba_combined_gamelogs.csv exists with proper columns")