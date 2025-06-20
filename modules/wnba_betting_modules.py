#!/usr/bin/env python3
"""
WNBA Sports Betting Intelligence System
Modules: Dynamic Odds Injector & Phase-Based Kelly Modifier

Purpose: Enhance betting cards with real-world odds and phase-adjusted Kelly sizing
Author: Senior AI Engineer
Version: 1.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DynamicOddsInjector:
    """
    Module 1: Ingest or simulate real-world payout odds
    """
    
    def __init__(self):
        self.default_odds = {
            'standard_prop': 0.9,  # -110 payout
            'fantasy_score': 1.0   # EV-neutral placeholder
        }
        
    def load_live_odds(self, filepath: str) -> Optional[pd.DataFrame]:
        """Load live odds from external source if available"""
        try:
            if os.path.exists(filepath):
                odds_df = pd.read_csv(filepath)
                logger.info(f"Loaded {len(odds_df)} live odds from {filepath}")
                return odds_df
            else:
                logger.warning(f"Live odds file not found: {filepath}")
                return None
        except Exception as e:
            logger.error(f"Error loading live odds: {e}")
            return None
    
    def get_default_odds(self, stat_type: str) -> float:
        """Return default odds based on stat type"""
        # Map various stat types to categories
        fantasy_types = ['fantasy_score', 'fantasy_points', 'fp']
        
        if stat_type.lower() in fantasy_types:
            return self.default_odds['fantasy_score']
        else:
            return self.default_odds['standard_prop']
    
    def inject_odds(self, betting_card: pd.DataFrame, 
                   live_odds_path: Optional[str] = None) -> pd.DataFrame:
        """
        Add actual_odds column to betting card
        
        Args:
            betting_card: DataFrame with betting recommendations
            live_odds_path: Optional path to live odds CSV
            
        Returns:
            Enhanced DataFrame with actual_odds column
        """
        df = betting_card.copy()
        
        # Initialize actual_odds column
        df['actual_odds'] = np.nan
        
        # Try to load live odds
        live_odds_df = None
        if live_odds_path:
            live_odds_df = self.load_live_odds(live_odds_path)
        
        # Process each bet
        for idx, row in df.iterrows():
            player_name = row.get('player_name', '')
            stat_type = row.get('stat_type', '')
            
            # First try to find live odds
            if live_odds_df is not None:
                match = live_odds_df[
                    (live_odds_df['player_name'] == player_name) & 
                    (live_odds_df['stat_type'] == stat_type)
                ]
                
                if not match.empty:
                    df.at[idx, 'actual_odds'] = match.iloc[0]['actual_odds']
                    continue
            
            # Fallback to default odds
            df.at[idx, 'actual_odds'] = self.get_default_odds(stat_type)
        
        logger.info(f"Injected odds for {len(df)} bets. "
                   f"Live odds used: {df['actual_odds'].notna().sum()}")
        
        return df


class PhaseBasedKellyModifier:
    """
    Module 2: Adjust Kelly criterion based on menstrual phase and historical performance
    """
    
    def __init__(self):
        # Phase-based divisors from backtest results
        self.phase_divisors = {
            'luteal': 3,      # 80% win rate - aggressive
            'follicular': 5,  # 67% win rate - moderate
            'menstrual': 10,  # 20% win rate - conservative
            'ovulation': 5    # TBD - default
        }
        
        self.default_divisor = 5
        
    def validate_phase(self, phase: str) -> str:
        """Validate and normalize phase name"""
        if pd.isna(phase) or phase == '':
            return 'default'
        
        phase_lower = str(phase).lower().strip()
        
        # Map common variations
        phase_mapping = {
            'luteal': 'luteal',
            'follicular': 'follicular',
            'menstrual': 'menstrual',
            'ovulation': 'ovulation',
            'ovulatory': 'ovulation'
        }
        
        return phase_mapping.get(phase_lower, 'default')
    
    def get_phase_divisor(self, phase: str) -> int:
        """Get Kelly divisor for given phase"""
        validated_phase = self.validate_phase(phase)
        
        if validated_phase == 'default':
            return self.default_divisor
        
        return self.phase_divisors.get(validated_phase, self.default_divisor)
    
    def adjust_kelly(self, betting_card: pd.DataFrame) -> pd.DataFrame:
        """
        Adjust Kelly criterion based on phase
        
        Args:
            betting_card: DataFrame with raw Kelly calculations
            
        Returns:
            DataFrame with adjusted kelly_used and bet_percentage
        """
        df = betting_card.copy()
        
        # Track adjustments for logging
        adjustments = []
        
        for idx, row in df.iterrows():
            # Get phase and raw Kelly
            phase = row.get('adv_phase', 'default')
            raw_kelly = row.get('raw_kelly', 0)
            
            # Get phase divisor
            divisor = self.get_phase_divisor(phase)
            
            # Calculate adjusted Kelly
            kelly_used = raw_kelly / divisor
            
            # Update values
            df.at[idx, 'kelly_used'] = kelly_used
            
            # Recalculate bet percentage if bankroll is available
            if 'bankroll' in row:
                bet_percentage = kelly_used * 100
                df.at[idx, 'bet_percentage'] = bet_percentage
            
            adjustments.append({
                'phase': self.validate_phase(phase),
                'divisor': divisor,
                'raw_kelly': raw_kelly,
                'kelly_used': kelly_used
            })
        
        # Log phase distribution
        phase_counts = pd.DataFrame(adjustments)['phase'].value_counts()
        logger.info(f"Phase distribution: {phase_counts.to_dict()}")
        
        return df


class BettingSystemEnhancer:
    """
    Main orchestrator for odds injection and Kelly modification
    """
    
    def __init__(self):
        self.odds_injector = DynamicOddsInjector()
        self.kelly_modifier = PhaseBasedKellyModifier()
        
    def validate_input_file(self, filepath: str) -> bool:
        """Validate that input file exists and has required columns"""
        if not os.path.exists(filepath):
            logger.error(f"Input file not found: {filepath}")
            return False
        
        try:
            df = pd.read_csv(filepath)
            required_cols = ['player_name', 'stat_type', 'raw_kelly']
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating input file: {e}")
            return False
    
    def enhance_betting_card(self, 
                           input_path: str,
                           output_path: str,
                           live_odds_path: Optional[str] = None) -> pd.DataFrame:
        """
        Apply both modules to enhance betting card
        
        Args:
            input_path: Path to daily_betting_card.csv
            output_path: Path for enhanced output
            live_odds_path: Optional path to live odds
            
        Returns:
            Enhanced DataFrame
        """
        # Validate input
        if not self.validate_input_file(input_path):
            raise ValueError(f"Invalid input file: {input_path}")
        
        # Load betting card
        logger.info(f"Loading betting card from {input_path}")
        betting_card = pd.read_csv(input_path)
        
        # Module 1: Inject odds
        logger.info("Applying Dynamic Odds Injector...")
        betting_card = self.odds_injector.inject_odds(betting_card, live_odds_path)
        
        # Module 2: Adjust Kelly
        logger.info("Applying Phase-Based Kelly Modifier...")
        betting_card = self.kelly_modifier.adjust_kelly(betting_card)
        
        # Save enhanced file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        betting_card.to_csv(output_path, index=False)
        logger.info(f"Saved enhanced betting card to {output_path}")
        
        return betting_card
    
    def generate_test_data(self, output_path: str = 'test_betting_card.csv'):
        """Generate sample betting card for testing"""
        test_data = {
            'player_name': ['A. Wilson', 'B. Stewart', 'C. Clark', 'D. Ionescu', 'E. Delle Donne'],
            'stat_type': ['points', 'rebounds', 'fantasy_score', 'assists', 'points'],
            'line': [20.5, 8.5, 35.5, 6.5, 18.5],
            'edge': [0.15, 0.12, 0.08, 0.20, 0.10],
            'confidence': [0.75, 0.70, 0.65, 0.80, 0.68],
            'raw_kelly': [0.30, 0.24, 0.16, 0.40, 0.20],
            'adv_phase': ['luteal', 'follicular', 'menstrual', 'ovulation', 'luteal'],
            'bankroll': [10000, 10000, 10000, 10000, 10000],
            'pred_outcome': ['over', 'over', 'under', 'over', 'under']
        }
        
        df = pd.DataFrame(test_data)
        df.to_csv(output_path, index=False)
        logger.info(f"Generated test data at {output_path}")
        return df


def main():
    """Main execution function"""
    logger.info("="*60)
    logger.info("WNBA Betting System Enhancement Pipeline")
    logger.info("="*60)
    
    # Initialize system
    enhancer = BettingSystemEnhancer()
    
    # Check if we have a real betting card or need to generate test data
    input_file = 'daily_betting_card.csv'
    output_file = 'output/daily_betting_card_adjusted.csv'
    live_odds_file = 'live_odds.csv'  # Optional
    
    if not os.path.exists(input_file):
        logger.warning(f"{input_file} not found. Generating test data...")
        enhancer.generate_test_data(input_file)
    
    # Run enhancement pipeline
    try:
        enhanced_df = enhancer.enhance_betting_card(
            input_path=input_file,
            output_path=output_file,
            live_odds_path=live_odds_file if os.path.exists(live_odds_file) else None
        )
        
        # Display results summary
        logger.info("\n" + "="*60)
        logger.info("Enhancement Summary:")
        logger.info(f"Total bets processed: {len(enhanced_df)}")
        logger.info(f"Average Kelly used: {enhanced_df['kelly_used'].mean():.3f}")
        logger.info(f"Average odds: {enhanced_df['actual_odds'].mean():.3f}")
        
        # Show sample of enhanced data
        logger.info("\nSample of enhanced betting card:")
        print(enhanced_df[['player_name', 'stat_type', 'raw_kelly', 
                          'kelly_used', 'actual_odds', 'adv_phase']].head())
        
        # Risk analysis
        logger.info("\n" + "="*60)
        logger.info("Risk Analysis:")
        phase_risk = enhanced_df.groupby('adv_phase')['kelly_used'].agg(['mean', 'sum', 'count'])
        print(phase_risk)
        
        # Save backtest-ready format
        backtest_file = 'output/backtest_ready.csv'
        enhanced_df['actual_result'] = ''  # Placeholder for manual entry
        enhanced_df.to_csv(backtest_file, index=False)
        logger.info(f"\nBacktest-ready file saved to: {backtest_file}")
        
    except Exception as e:
        logger.error(f"Enhancement pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()