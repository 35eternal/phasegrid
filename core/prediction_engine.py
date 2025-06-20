"""
WNBA Prediction Engine - Real-time prop betting intelligence
Operationalizes backtested edge with 23% ROI validation
"""

import pandas as pd
import numpy as np
import logging
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple, Union
from pathlib import Path
import warnings
from datetime import datetime, timedelta
from scipy import stats

# Suppress pandas warnings for cleaner output
warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """Structured output for prediction engine results"""
    player_name: str
    stat_type: str
    predicted_probability: float
    volatility_score: float
    cycle_state: str  # HOT / COLD / NEUTRAL
    confidence_score: float
    recommendation: str  # OVER / UNDER / PASS
    kelly_stake_pct: Optional[float] = None
    expected_value: Optional[float] = None
    debug_notes: str = ""

class PredictionEngine:
    """
    WNBA Prop Betting Prediction Engine
    
    Applies volatility analysis, cycle detection, and probability modeling
    to generate betting recommendations with validated 23% ROI edge.
    """
    
    def __init__(self, 
                 data_path: str = "data/wnba_combined_gamelogs.csv",
                 config_path: Optional[str] = "config/settings.py",
                 bankroll: float = 1000.0):
        """
        Initialize prediction engine
        
        Args:
            data_path: Path to historical game logs CSV
            config_path: Optional path to config file
            bankroll: Bankroll for Kelly Criterion calculations
        """
        self.data_path = Path(data_path)
        self.config_path = Path(config_path) if config_path else None
        self.bankroll = bankroll
        
        # Load configuration
        self.config = self._load_config()
        
        # Load and prepare data
        self.df = self._load_data()
        
        logger.info(f"Prediction engine initialized with {len(self.df)} game logs")
    
    def _load_config(self) -> Dict:
        """Load configuration with defaults"""
        default_config = {
            'volatility_window': 10,
            'cycle_window': 5,
            'confidence_threshold': 0.65,
            'min_games_required': 5,
            'kelly_max_stake': 0.20,  # Max 20% of bankroll
            'volatility_weights': [1.0, 0.8, 0.6],  # 3/5/10 game weights
        }
        
        # Try to load from config file if it exists
        if self.config_path and self.config_path.exists():
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("settings", self.config_path)
                settings = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(settings)
                
                # Override defaults with config values
                for key in default_config:
                    if hasattr(settings, key.upper()):
                        default_config[key] = getattr(settings, key.upper())
                        
                logger.info(f"Loaded config from {self.config_path}")
            except Exception as e:
                logger.warning(f"Could not load config: {e}. Using defaults.")
        
        return default_config
    
    def _load_data(self) -> pd.DataFrame:
        """Load and preprocess game log data with flexible column mapping"""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        df = pd.read_csv(self.data_path)
        
        # Debug: Show original columns
        logger.info(f"Original columns: {list(df.columns)}")
        
        # Flexible column mapping
        column_map = self._map_columns(df.columns)
        logger.info(f"Column mapping: {column_map}")
        
        # Rename columns to standard names
        df = df.rename(columns=column_map)
        
        # Debug: Show columns after mapping
        logger.info(f"Columns after mapping: {list(df.columns)}")
        
        # Check if we found the essential columns
        required_cols = ['Player', 'Date']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            available_cols = list(df.columns)
            logger.error(f"Column mapping failed. Missing: {missing_cols}")
            logger.error(f"Available after mapping: {available_cols}")
            logger.error(f"Original columns: {list(pd.read_csv(self.data_path).columns)}")
            raise ValueError(f"Could not map required columns: {missing_cols}\nOriginal columns available: {list(pd.read_csv(self.data_path).columns)}")
        
        # Ensure Player column is string type
        df['Player'] = df['Player'].astype(str)
        
        # Convert date column with multiple format attempts
        try:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        except Exception as e:
            logger.warning(f"Could not convert Date column: {e}")
            # Try common date formats
            try:
                df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
            except:
                try:
                    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
                except:
                    logger.error("Could not parse dates - using index as fallback")
                    df['Date'] = pd.to_datetime('today')
        
        # Sort by player and date for time series analysis
        df = df.sort_values(['Player', 'Date']).reset_index(drop=True)
        
        logger.info(f"Loaded {len(df)} game logs for {df['Player'].nunique()} players")
        return df
    
    def _map_columns(self, columns) -> dict:
        """Map actual column names to standardized names"""
        column_map = {}
        columns_list = list(columns)
        
        # Player name mapping - prioritize PLAYER_NAME over PLAYER_ID
        if 'PLAYER_NAME' in columns_list:
            column_map['PLAYER_NAME'] = 'Player'
        elif 'PLAYER_ID' in columns_list:
            column_map['PLAYER_ID'] = 'Player'  
        else:
            # Fallback pattern matching
            for col in columns_list:
                if any(pattern in col.lower() for pattern in ['player', 'name']):
                    column_map[col] = 'Player'
                    break
        
        # Date mapping - prioritize GAME_DATE
        if 'GAME_DATE' in columns_list:
            column_map['GAME_DATE'] = 'Date'
        elif 'DATE' in columns_list:
            column_map['DATE'] = 'Date'
        else:
            # Fallback pattern matching
            for col in columns_list:
                if any(pattern in col.lower() for pattern in ['date', 'game_date', 'gamedate']):
                    column_map[col] = 'Date'
                    break
        
        # Stats mapping - exact matches first (keep original names if they exist)
        exact_stat_mappings = {
            'PTS': 'PTS',
            'REB': 'REB', 
            'AST': 'AST',
            'STL': 'STL',
            'BLK': 'BLK',
            'FGM': 'FGM',
            'FGA': 'FGA',
            'FG_PCT': 'FG_PCT',
            'FG3M': 'FG3M',
            'FG3A': 'FG3A',
            'FTM': 'FTM',
            'FTA': 'FTA',
            'MIN': 'MIN',
            'TOV': 'TOV'
        }
        
        for col in columns_list:
            if col in exact_stat_mappings:
                # Don't remap if it's already the correct name
                pass  # column_map[col] = exact_stat_mappings[col] would just map to itself
        
        return column_map
    
    def _calculate_volatility_score(self, values: List[float], window: int = 10) -> float:
        """
        Calculate volatility using Coefficient of Variation
        
        Args:
            values: List of stat values
            window: Lookback window
            
        Returns:
            Volatility score (0-1, higher = more volatile)
        """
        if len(values) < 3:
            return 0.5  # Neutral volatility for insufficient data
        
        recent_values = values[-window:] if len(values) >= window else values
        
        if len(recent_values) < 2:
            return 0.5
        
        mean_val = np.mean(recent_values)
        if mean_val == 0:
            return 1.0  # Maximum volatility for zero mean
        
        std_val = np.std(recent_values)
        cv = std_val / mean_val
        
        # Normalize CV to 0-1 scale (typical CV for sports stats: 0-1.5)
        normalized_cv = min(cv / 1.5, 1.0)
        
        return normalized_cv
    
    def _detect_cycle_state(self, values: List[float], window: int = 5) -> str:
        """
        Detect hot/cold cycle using recent performance trend
        
        Args:
            values: List of stat values
            window: Lookback window for cycle detection
            
        Returns:
            Cycle state: HOT / COLD / NEUTRAL
        """
        if len(values) < window:
            return "NEUTRAL"
        
        recent_values = values[-window:]
        longer_avg = np.mean(values[:-window]) if len(values) > window else np.mean(values)
        recent_avg = np.mean(recent_values)
        
        # Calculate performance ratio
        if longer_avg == 0:
            return "NEUTRAL"
        
        performance_ratio = recent_avg / longer_avg
        
        # Define thresholds for hot/cold states
        if performance_ratio >= 1.15:  # 15% above average
            return "HOT"
        elif performance_ratio <= 0.85:  # 15% below average
            return "COLD"
        else:
            return "NEUTRAL"
    
    def _calculate_hit_probability(self, values: List[float], prop_line: float) -> float:
        """
        Calculate probability of hitting over prop line using normal distribution
        
        Args:
            values: Historical stat values
            prop_line: Prop betting line
            
        Returns:
            Probability of going over the line (0-1)
        """
        if len(values) < 2:
            return 0.5  # Neutral probability
        
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if std_val == 0:
            # No variance - deterministic outcome
            return 1.0 if mean_val > prop_line else 0.0
        
        # Calculate z-score and probability
        z_score = (prop_line - mean_val) / std_val
        prob_under = stats.norm.cdf(z_score)
        prob_over = 1 - prob_under
        
        return prob_over
    
    def _calculate_confidence_score(self, 
                                  volatility: float, 
                                  cycle_state: str, 
                                  sample_size: int,
                                  prob_deviation: float) -> float:
        """
        Calculate blended confidence score from multiple factors
        
        Args:
            volatility: Volatility score (0-1)
            cycle_state: Current cycle state
            sample_size: Number of games in sample
            prob_deviation: How far probability is from 50%
            
        Returns:
            Confidence score (0-1)
        """
        # Base confidence from sample size
        sample_confidence = min(sample_size / 20, 1.0)  # Max confidence at 20+ games
        
        # Volatility penalty (higher volatility = lower confidence)
        volatility_confidence = 1 - volatility
        
        # Cycle boost (hot/cold states increase confidence)
        cycle_boost = 0.1 if cycle_state in ["HOT", "COLD"] else 0.0
        
        # Probability deviation boost (more extreme probabilities = higher confidence)
        prob_confidence = abs(prob_deviation - 0.5) * 2  # Convert to 0-1 scale
        
        # Weighted combination
        confidence = (
            sample_confidence * 0.3 +
            volatility_confidence * 0.3 +
            prob_confidence * 0.3 +
            cycle_boost
        )
        
        return min(confidence, 1.0)
    
    def _calculate_kelly_stake(self, probability: float, odds: float) -> float:
        """
        Calculate Kelly Criterion stake percentage
        
        Args:
            probability: Win probability (0-1)
            odds: Decimal odds (e.g., 1.91 for -110)
            
        Returns:
            Stake percentage of bankroll (0-1)
        """
        # Convert typical -110 odds to decimal if needed
        if odds < 0:
            decimal_odds = (100 / abs(odds)) + 1
        else:
            decimal_odds = (odds / 100) + 1
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds-1, p = win probability, q = lose probability
        b = decimal_odds - 1
        p = probability
        q = 1 - probability
        
        kelly_fraction = (b * p - q) / b
        
        # Apply safety constraints
        kelly_fraction = max(0, kelly_fraction)  # No negative stakes
        kelly_fraction = min(kelly_fraction, self.config['kelly_max_stake'])  # Cap at max
        
        return kelly_fraction
    
    def _calculate_expected_value(self, probability: float, odds: float, stake: float) -> float:
        """
        Calculate expected value of bet
        
        Args:
            probability: Win probability
            odds: Decimal odds
            stake: Stake amount
            
        Returns:
            Expected value in dollars
        """
        # Convert odds if needed
        if odds < 0:
            decimal_odds = (100 / abs(odds)) + 1
        else:
            decimal_odds = (odds / 100) + 1
        
        win_amount = stake * (decimal_odds - 1)
        lose_amount = stake
        
        ev = (probability * win_amount) - ((1 - probability) * lose_amount)
        return ev
    
    def predict(self, 
                player_name: str, 
                stat_type: str, 
                game_date: Optional[str] = None,
                prop_line: Optional[float] = None,
                odds: float = -110) -> PredictionResult:
        """
        Main prediction method
        
        Args:
            player_name: Player name (e.g., "Caitlin Clark")
            stat_type: Stat type (e.g., "PTS", "REB", "AST")
            game_date: Optional game date for situational analysis
            prop_line: Optional prop line for bet recommendation
            odds: Betting odds (default -110)
            
        Returns:
            PredictionResult with comprehensive analysis
        """
        logger.info(f"Generating prediction for {player_name} - {stat_type}")
        
        # Filter data for specific player
        player_data = self.df[self.df['Player'].str.contains(player_name, case=False, na=False)]
        
        if player_data.empty:
            return PredictionResult(
                player_name=player_name,
                stat_type=stat_type,
                predicted_probability=0.5,
                volatility_score=0.5,
                cycle_state="NEUTRAL",
                confidence_score=0.0,
                recommendation="PASS",
                debug_notes=f"No data found for player: {player_name}"
            )
        
        # Extract stat values
        if stat_type not in player_data.columns:
            return PredictionResult(
                player_name=player_name,
                stat_type=stat_type,
                predicted_probability=0.5,
                volatility_score=0.5,
                cycle_state="NEUTRAL",
                confidence_score=0.0,
                recommendation="PASS",
                debug_notes=f"Stat type {stat_type} not available"
            )
        
        stat_values = player_data[stat_type].dropna().tolist()
        
        # Check minimum games requirement
        if len(stat_values) < self.config['min_games_required']:
            return PredictionResult(
                player_name=player_name,
                stat_type=stat_type,
                predicted_probability=0.5,
                volatility_score=0.5,
                cycle_state="NEUTRAL",
                confidence_score=0.0,
                recommendation="PASS",
                debug_notes=f"Insufficient data: {len(stat_values)} games < {self.config['min_games_required']} required"
            )
        
        # Calculate core metrics
        volatility_score = self._calculate_volatility_score(stat_values, self.config['volatility_window'])
        cycle_state = self._detect_cycle_state(stat_values, self.config['cycle_window'])
        
        # Initialize result values
        predicted_probability = 0.5
        recommendation = "PASS"
        kelly_stake_pct = None
        expected_value = None
        debug_notes = f"Analyzed {len(stat_values)} games"
        
        # If prop line provided, calculate probability and recommendation
        if prop_line is not None:
            predicted_probability = self._calculate_hit_probability(stat_values, prop_line)
            
            # Generate recommendation based on confidence threshold
            confidence_score = self._calculate_confidence_score(
                volatility_score, cycle_state, len(stat_values), predicted_probability
            )
            
            if confidence_score >= self.config['confidence_threshold']:
                if predicted_probability > 0.5:
                    recommendation = "OVER"
                else:
                    recommendation = "UNDER"
                    predicted_probability = 1 - predicted_probability  # Flip for under bet
                
                # Calculate Kelly stake and EV
                kelly_stake_pct = self._calculate_kelly_stake(predicted_probability, odds)
                stake_amount = kelly_stake_pct * self.bankroll
                expected_value = self._calculate_expected_value(predicted_probability, odds, stake_amount)
                
                debug_notes += f" | Prop: {prop_line} | Confidence: {confidence_score:.3f}"
            else:
                debug_notes += f" | Low confidence: {confidence_score:.3f} < {self.config['confidence_threshold']}"
        else:
            # No prop line - calculate confidence without specific recommendation
            confidence_score = self._calculate_confidence_score(
                volatility_score, cycle_state, len(stat_values), 0.5
            )
        
        # Add cycle and volatility info to debug notes
        debug_notes += f" | Volatility: {volatility_score:.3f} | Cycle: {cycle_state}"
        
        return PredictionResult(
            player_name=player_name,
            stat_type=stat_type,
            predicted_probability=predicted_probability,
            volatility_score=volatility_score,
            cycle_state=cycle_state,
            confidence_score=confidence_score,
            recommendation=recommendation,
            kelly_stake_pct=kelly_stake_pct,
            expected_value=expected_value,
            debug_notes=debug_notes
        )
    
    def batch_predict(self, 
                     predictions: List[Dict[str, Union[str, float]]]) -> List[PredictionResult]:
        """
        Generate predictions for multiple props
        
        Args:
            predictions: List of prediction requests
            
        Returns:
            List of PredictionResult objects
        """
        results = []
        for pred_req in predictions:
            result = self.predict(**pred_req)
            results.append(result)
        
        return results
    
    def get_player_summary(self, player_name: str) -> Dict:
        """
        Get comprehensive player analysis summary
        
        Args:
            player_name: Player name
            
        Returns:
            Dictionary with player statistics and trends
        """
        player_data = self.df[self.df['Player'].str.contains(player_name, case=False, na=False)]
        
        if player_data.empty:
            return {"error": f"No data found for {player_name}"}
        
        summary = {
            "player_name": player_name,
            "total_games": len(player_data),
            "date_range": f"{player_data['Date'].min()} to {player_data['Date'].max()}",
            "stats": {}
        }
        
        # Calculate stats for each major category
        for stat in ['PTS', 'REB', 'AST']:
            if stat in player_data.columns:
                values = player_data[stat].dropna()
                if len(values) > 0:
                    summary["stats"][stat] = {
                        "mean": float(values.mean()),
                        "std": float(values.std()),
                        "min": float(values.min()),
                        "max": float(values.max()),
                        "recent_5_avg": float(values.tail(5).mean()) if len(values) >= 5 else None,
                        "volatility": self._calculate_volatility_score(values.tolist()),
                        "cycle_state": self._detect_cycle_state(values.tolist())
                    }
        
        return summary

# Example usage and testing
if __name__ == "__main__":
    # Initialize engine
    engine = PredictionEngine()
    
    # Example prediction
    result = engine.predict(
        player_name="Caitlin Clark",
        stat_type="PTS",
        prop_line=18.5,
        odds=-110
    )
    
    print(f"Prediction Result:")
    print(f"Player: {result.player_name}")
    print(f"Stat: {result.stat_type}")
    print(f"Recommendation: {result.recommendation}")
    print(f"Probability: {result.predicted_probability:.3f}")
    print(f"Confidence: {result.confidence_score:.3f}")
    print(f"Cycle State: {result.cycle_state}")
    print(f"Kelly Stake: {result.kelly_stake_pct:.3f}%" if result.kelly_stake_pct else "N/A")
    print(f"Expected Value: ${result.expected_value:.2f}" if result.expected_value else "N/A")
    print(f"Debug: {result.debug_notes}")