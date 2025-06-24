#!/usr/bin/env python3
"""
Dynamic Odds Injector - Kelly Criterion-based bet sizing for PhaseGrid

This module calculates recommended wager sizes using the Kelly formula with
phase-based adjustments and bankroll constraints.
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DynamicOddsInjector:
    """Calculate optimal bet sizes using fractional Kelly criterion with phase adjustments."""
    
    def __init__(self):
        # Load environment variables
        self.kelly_fraction = float(os.getenv('KELLY_FRACTION', '0.25'))
        self.bankroll = float(os.getenv('BANKROLL', '1000'))
        self.min_edge = float(os.getenv('MIN_EDGE', '0.02'))  # 2% minimum edge
        self.phase_config_path = os.getenv('PHASE_CONFIG_PATH', 'config/phase_config.json')
        
        # Load phase multipliers
        self.phase_multipliers = self._load_phase_config()
        
        # Get current date for file naming
        self.date_str = datetime.now().strftime('%Y%m%d')
        
    def _load_phase_config(self):
        """Load phase-specific multipliers from config file."""
        try:
            with open(self.phase_config_path, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded phase config: {config}")
                return config
        except FileNotFoundError:
            logger.warning(f"Phase config not found at {self.phase_config_path}, using defaults")
            return {
                "preseason": 0.3,
                "early_season": 0.5,
                "mid_season": 0.8,
                "late_season": 1.0,
                "playoffs": 1.2,
                "default": 0.7
            }
    
    def calculate_kelly_percentage(self, win_prob, odds):
        """
        Calculate Kelly percentage for a single bet.
        
        Kelly formula: f = (p * b - q) / b
        where:
        - f = fraction of bankroll to bet
        - p = probability of winning
        - q = probability of losing (1 - p)
        - b = net odds (decimal odds - 1)
        
        Args:
            win_prob: Model's probability of winning (0-1)
            odds: Decimal odds from sportsbook
            
        Returns:
            Kelly percentage (fraction of bankroll)
        """
        if odds <= 1 or win_prob <= 0 or win_prob >= 1:
            return 0.0
            
        q = 1 - win_prob
        b = odds - 1  # Convert to net odds
        
        # Full Kelly calculation
        kelly = (win_prob * b - q) / b
        
        # Apply fractional Kelly for risk management
        fractional_kelly = kelly * self.kelly_fraction
        
        # Cap at 10% of bankroll per bet for safety
        return min(max(0, fractional_kelly), 0.1)
    
    def get_current_phase(self):
        """Determine current WNBA season phase based on date."""
        month = datetime.now().month
        
        if month == 4 or (month == 5 and datetime.now().day <= 15):
            return "preseason"
        elif month == 5 and datetime.now().day > 15:
            return "early_season"
        elif month in [6, 7]:
            return "mid_season"
        elif month == 8:
            return "late_season"
        elif month in [9, 10]:
            return "playoffs"
        else:
            return "default"  # Off-season (Nov-Mar)
    
    def load_data(self):
        """Load predictions and odds data from CSV files."""
        predictions_file = f"predictions_{self.date_str}.csv"
        odds_file = f"data/prizepicks_lines_{self.date_str}.csv"
        
        try:
            predictions_df = pd.read_csv(predictions_file)
            logger.info(f"Loaded {len(predictions_df)} predictions from {predictions_file}")
        except FileNotFoundError:
            logger.error(f"Predictions file not found: {predictions_file}")
            raise
            
        try:
            odds_df = pd.read_csv(odds_file)
            logger.info(f"Loaded {len(odds_df)} odds from {odds_file}")
        except FileNotFoundError:
            logger.error(f"Odds file not found: {odds_file}")
            raise
            
        return predictions_df, odds_df
    
    def merge_and_calculate_edges(self, predictions_df, odds_df):
        """Merge predictions with odds and calculate edges."""
        # Merge on common identifiers (adjust based on actual CSV structure)
        merged_df = pd.merge(
            predictions_df,
            odds_df,
            on=['player_name', 'market', 'game_date'],
            how='inner'
        )
        
        # Calculate edge: model_prob - implied_prob
        merged_df['implied_prob'] = 1 / merged_df['decimal_odds']
        merged_df['edge'] = merged_df['win_probability'] - merged_df['implied_prob']
        
        # Filter by minimum edge
        positive_edge_df = merged_df[merged_df['edge'] >= self.min_edge]
        logger.info(f"Found {len(positive_edge_df)} bets with edge >= {self.min_edge}")
        
        return positive_edge_df
    
    def calculate_wagers(self, bets_df):
        """Calculate recommended wager sizes using Kelly criterion."""
        current_phase = self.get_current_phase()
        phase_multiplier = self.phase_multipliers.get(current_phase, 0.7)
        logger.info(f"Current phase: {current_phase}, multiplier: {phase_multiplier}")
        
        # Calculate Kelly percentage for each bet
        bets_df['kelly_percentage'] = bets_df.apply(
            lambda row: self.calculate_kelly_percentage(
                row['win_probability'], 
                row['decimal_odds']
            ),
            axis=1
        )
        
        # Apply phase multiplier
        bets_df['phase_multiplier'] = phase_multiplier
        bets_df['adjusted_kelly'] = bets_df['kelly_percentage'] * phase_multiplier
        
        # Calculate raw wager amounts
        bets_df['raw_wager'] = self.bankroll * bets_df['adjusted_kelly']
        
        # Check if we need to scale down due to bankroll constraint
        total_raw_wager = bets_df['raw_wager'].sum()
        
        if total_raw_wager > self.bankroll:
            scale_factor = self.bankroll * 0.95 / total_raw_wager  # Use 95% of bankroll max
            logger.warning(f"Total wagers ({total_raw_wager:.2f}) exceed bankroll ({self.bankroll}). Scaling by {scale_factor:.3f}")
            bets_df['recommended_wager'] = bets_df['raw_wager'] * scale_factor
        else:
            bets_df['recommended_wager'] = bets_df['raw_wager']
        
        # Round to nearest dollar
        bets_df['recommended_wager'] = bets_df['recommended_wager'].round(2)
        
        # Generate slip IDs
        bets_df['slip_id'] = [f"SLIP_{self.date_str}_{i:04d}" for i in range(len(bets_df))]
        
        return bets_df
    
    def save_bets(self, bets_df):
        """Save bet recommendations to CSV."""
        output_columns = [
            'slip_id', 'player_name', 'market', 'recommended_wager',
            'kelly_percentage', 'phase_multiplier', 'edge', 'win_probability',
            'decimal_odds'
        ]
        
        output_df = bets_df[output_columns].copy()
        output_file = f"bets_{self.date_str}.csv"
        
        output_df.to_csv(output_file, index=False)
        logger.info(f"Saved {len(output_df)} bet recommendations to {output_file}")
        
        # Log summary statistics
        total_wager = output_df['recommended_wager'].sum()
        avg_wager = output_df['recommended_wager'].mean()
        max_wager = output_df['recommended_wager'].max()
        
        logger.info(f"Betting summary - Total: ${total_wager:.2f}, Avg: ${avg_wager:.2f}, Max: ${max_wager:.2f}")
        
        return output_file
    
    def run(self):
        """Execute the full dynamic odds injection pipeline."""
        logger.info("Starting Dynamic Odds Injector")
        
        try:
            # Load data
            predictions_df, odds_df = self.load_data()
            
            # Merge and calculate edges
            bets_df = self.merge_and_calculate_edges(predictions_df, odds_df)
            
            if len(bets_df) == 0:
                logger.warning("No positive edge bets found")
                # Create empty output file
                empty_df = pd.DataFrame(columns=['slip_id', 'player_name', 'market', 'recommended_wager'])
                output_file = f"bets_{self.date_str}.csv"
                empty_df.to_csv(output_file, index=False)
                return output_file
            
            # Calculate wager sizes
            final_bets_df = self.calculate_wagers(bets_df)
            
            # Save results
            output_file = self.save_bets(final_bets_df)
            
            logger.info("Dynamic Odds Injector completed successfully")
            return output_file
            
        except Exception as e:
            logger.error(f"Error in Dynamic Odds Injector: {str(e)}")
            raise


if __name__ == "__main__":
    injector = DynamicOddsInjector()
    injector.run()