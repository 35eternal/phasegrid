#!/usr/bin/env python3
"""
bankroll_optimizer.py - Intelligent bet sizing using Kelly Criterion with cycle adjustments

This module calculates optimal bet sizes for WNBA prop bets using:
- Kelly Criterion for mathematical edge calculation
- Volatility adjustments from menstrual cycle validation
- Confidence scaling from the prediction model
- Diversification rules for risk management
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class BankrollOptimizer:
    def __init__(self, min_bet_pct=0.005, max_bet_pct=0.025, payout=0.9, kelly_fraction=0.25,
                 max_bets_per_combo=5, max_bets_per_player=2):
        """
        Initialize bankroll optimizer with betting constraints
        
        Args:
            min_bet_pct: Minimum bet as percentage of bankroll (default 0.5%)
            max_bet_pct: Maximum bet as percentage of bankroll (default 2.5%)
            payout: PrizePicks payout ratio (default 0.9 for -110 odds)
            kelly_fraction: Fraction of Kelly to use (default 0.25 for 1/4 Kelly)
            max_bets_per_combo: Maximum bets per phase/risk combination (default 5)
            max_bets_per_player: Maximum bets per player (default 2)
        """
        self.min_bet_pct = min_bet_pct
        self.max_bet_pct = max_bet_pct
        self.payout = payout
        self.kelly_fraction = kelly_fraction  # Use fractional Kelly for safety
        self.max_bets_per_combo = max_bets_per_combo
        self.max_bets_per_player = max_bets_per_player
        
    def load_data(self):
        """Load props data and cycle validation summary"""
        # Load props with cycle data
        props_path = Path('data/final_props_with_advanced_cycles.csv')
        self.props_df = pd.read_csv(props_path)
        
        # Debug: Print available columns
        print(f"Available columns in props data: {list(self.props_df.columns)}")
        
        # Filter to only validated props (with actual results)
        self.props_df = self.props_df[self.props_df['actual_result'].notna()].copy()
        
        # Load cycle validation summary
        summary_path = Path('output/cycle_validation_summary.csv')
        self.validation_summary = pd.read_csv(summary_path)
        
        # Debug: Print validation summary columns
        print(f"Available columns in validation summary: {list(self.validation_summary.columns)}")
        
        print(f"Loaded {len(self.props_df)} validated props")
        print(f"Loaded {len(self.validation_summary)} phase/risk combinations")
        
    def calculate_kelly_fraction(self, win_rate):
        """
        Calculate Kelly fraction for given win rate
        
        Kelly formula: f = (p*b - q) / b
        where:
            f = fraction of bankroll to bet
            p = probability of winning
            b = net odds received on bet (payout)
            q = probability of losing (1-p)
        """
        if win_rate <= 0 or win_rate >= 1:
            return 0
            
        edge = (win_rate * self.payout) - (1 - win_rate)
        kelly_fraction = edge / self.payout
        
        # Kelly can be negative if no edge exists
        return max(0, kelly_fraction)
    
    def adjust_for_volatility(self, kelly_fraction, std_dev):
        """
        Adjust Kelly fraction based on volatility (standard deviation)
        Higher volatility = more conservative betting
        """
        # Calculate volatility factor (normalize std dev)
        # Assuming typical std dev range of 2-6 for WNBA stats
        volatility_factor = 1 - min(0.5, (std_dev - 2) / 8)
        
        return kelly_fraction * volatility_factor
    
    def adjust_for_confidence(self, kelly_fraction, confidence):
        """
        Adjust Kelly fraction based on model confidence
        Scale linearly with confidence score
        """
        # Confidence typically ranges 0.5-1.0
        # Scale to be more conservative with lower confidence
        confidence_factor = (confidence - 0.5) * 2  # Maps 0.5->0, 1.0->1
        confidence_factor = max(0.3, confidence_factor)  # Floor at 30%
        
        return kelly_fraction * confidence_factor
    
    def calculate_bet_percentage(self, prop_row, validation_row):
        """
        Calculate final bet percentage for a single prop
        
        Returns:
            tuple: (kelly_fraction, bet_percentage, dynamic_kelly_fraction)
        """
        try:
            # Get win rate from validation summary
            win_rate = validation_row['win_rate'].iloc[0] if not validation_row.empty else 0.5
            
            # Get standard deviation - check for different column names
            if not validation_row.empty:
                if 'std_dev' in validation_row.columns:
                    std_dev = validation_row['std_dev'].iloc[0]
                elif 'actual_std' in validation_row.columns:
                    std_dev = validation_row['actual_std'].iloc[0]
                else:
                    std_dev = 3.0
            else:
                std_dev = 3.0
            
            # Calculate base Kelly fraction
            kelly_fraction = self.calculate_kelly_fraction(win_rate)
            
            # Get confidence value - check for all possible column names
            if 'confidence' in prop_row:
                confidence = prop_row['confidence']
            elif 'adv_confidence' in prop_row:
                confidence = prop_row['adv_confidence']
            elif 'confidence_score' in prop_row:
                confidence = prop_row['confidence_score']
            else:
                confidence = 0.7
            
            # Apply adjustments
            kelly_adjusted = self.adjust_for_volatility(kelly_fraction, std_dev)
            kelly_adjusted = self.adjust_for_confidence(kelly_adjusted, confidence)
            
            # Apply dynamic fractional Kelly based on confidence
            # Higher confidence = more aggressive Kelly fraction
            if confidence > 0.8:
                dynamic_kelly_fraction = 0.33  # 1/3 Kelly for high confidence
            elif confidence > 0.7:
                dynamic_kelly_fraction = 0.25  # 1/4 Kelly for medium confidence
            else:
                dynamic_kelly_fraction = 0.20  # 1/5 Kelly for lower confidence
                
            kelly_adjusted = kelly_adjusted * dynamic_kelly_fraction
            
            # Apply min/max constraints
            bet_percentage = np.clip(kelly_adjusted, self.min_bet_pct, self.max_bet_pct)
            
            # Always return three values
            return kelly_fraction, bet_percentage, dynamic_kelly_fraction
            
        except Exception as e:
            print(f"Error in calculate_bet_percentage: {e}")
            # Return safe defaults
            return 0.0, self.min_bet_pct, 0.25
    
    def apply_diversification(self, betting_card):
        """
        Apply diversification rules to limit concentration risk
        
        Returns:
            DataFrame with diversification rules applied
        """
        # Only process BET recommendations
        bet_rows = betting_card[betting_card['recommendation'] == 'BET'].copy()
        no_bet_rows = betting_card[betting_card['recommendation'] == 'NO BET'].copy()
        
        if len(bet_rows) == 0:
            return betting_card
        
        # Sort by bet_percentage to prioritize highest value bets
        bet_rows = bet_rows.sort_values('bet_percentage', ascending=False)
        
        # Track counts for diversification
        phase_risk_counts = {}
        player_counts = {}
        selected_bets = []
        
        print("\nApplying diversification rules...")
        
        for idx, row in bet_rows.iterrows():
            # Create phase/risk key
            phase_risk_key = f"{row['adv_phase']}_{row['adv_risk_tag']}"
            
            # Check phase/risk limit
            if phase_risk_key not in phase_risk_counts:
                phase_risk_counts[phase_risk_key] = 0
            
            if phase_risk_counts[phase_risk_key] >= self.max_bets_per_combo:
                continue
            
            # Check player limit
            player = row['player_name']
            if player not in player_counts:
                player_counts[player] = 0
                
            if player_counts[player] >= self.max_bets_per_player:
                continue
            
            # This bet passes diversification rules
            selected_bets.append(row)
            phase_risk_counts[phase_risk_key] += 1
            player_counts[player] += 1
        
        # Convert back to DataFrame
        if selected_bets:
            diversified_bets = pd.DataFrame(selected_bets)
            result = pd.concat([diversified_bets, no_bet_rows])
            
            print(f"Diversification applied: {len(bet_rows)} -> {len(diversified_bets)} bets")
            print(f"Phase/Risk combinations: {len(phase_risk_counts)}")
            print(f"Unique players: {len(player_counts)}")
            
            return result
        else:
            return no_bet_rows
    
    def filter_by_date(self, props_df, hours_ahead=48):
        """
        Filter props to only include games within specified hours
        NOTE: This requires a 'game_datetime' column which may not exist yet
        
        Args:
            props_df: DataFrame of props
            hours_ahead: Number of hours to look ahead (default 48)
            
        Returns:
            Filtered DataFrame
        """
        if 'game_datetime' in props_df.columns:
            from datetime import datetime, timedelta
            
            cutoff_time = datetime.now() + timedelta(hours=hours_ahead)
            props_df['game_datetime'] = pd.to_datetime(props_df['game_datetime'])
            
            filtered = props_df[
                (props_df['game_datetime'] >= datetime.now()) & 
                (props_df['game_datetime'] <= cutoff_time)
            ]
            
            print(f"Filtered to games within next {hours_ahead} hours: {len(filtered)} props")
            return filtered
        else:
            # Column doesn't exist, return all props
            print("Note: 'game_datetime' column not found - using all props")
            return props_df
    
    def generate_betting_card(self, max_bets=20, hours_ahead=48):
        """
        Generate daily betting card with recommendations
        
        Args:
            max_bets: Maximum number of bets to include (default 20)
            hours_ahead: Hours ahead to look for games (default 48)
        """
        results = []
        
        # Process all validated props (no date filtering)
        props_to_analyze = self.props_df.copy()
        
        # Apply date filter if available
        props_to_analyze = self.filter_by_date(props_to_analyze, hours_ahead)
        
        print(f"\nGenerating betting card...")
        print(f"Analyzing {len(props_to_analyze)} validated props...\n")
        
        # Debug: show unique phase/risk combinations in validation summary
        if 'phase' in self.validation_summary.columns and 'risk_tag' in self.validation_summary.columns:
            print("Available phase/risk combinations in validation summary:")
            unique_combos = self.validation_summary[['phase', 'risk_tag']].drop_duplicates()
            print(unique_combos.to_string(index=False))
            print()
        
        # Debug: Show first few rows of validation summary
        print("\nFirst few rows of validation summary:")
        print(self.validation_summary.head(3))
        
        # Track warnings to avoid spam
        warnings_shown = set()
        
        for idx, prop in props_to_analyze.iterrows():
            # Determine which phase and risk columns to use in props
            if 'adv_phase' in prop and pd.notna(prop['adv_phase']):
                phase_col_props = 'adv_phase'
            else:
                phase_col_props = 'cycle_phase'
                
            if 'adv_risk_tag' in prop and pd.notna(prop['adv_risk_tag']):
                risk_col_props = 'adv_risk_tag'
            else:
                risk_col_props = 'cycle_risk_tag'
            
            # Determine which columns exist in validation summary
            phase_col_val = None
            risk_col_val = None
            
            # Check for phase column in validation summary
            if 'adv_phase' in self.validation_summary.columns:
                phase_col_val = 'adv_phase'
            elif 'phase' in self.validation_summary.columns:
                phase_col_val = 'phase'
            elif 'cycle_phase' in self.validation_summary.columns:
                phase_col_val = 'cycle_phase'
                
            # Check for risk tag column in validation summary
            if 'adv_risk_tag' in self.validation_summary.columns:
                risk_col_val = 'adv_risk_tag'
            elif 'risk_tag' in self.validation_summary.columns:
                risk_col_val = 'risk_tag'
            elif 'cycle_risk_tag' in self.validation_summary.columns:
                risk_col_val = 'cycle_risk_tag'
            
            # Lookup validation stats for this phase/risk combo
            if phase_col_val and risk_col_val:
                # Debug first few lookups
                if idx < props_to_analyze.index[0] + 1:  # Only debug first prop
                    print(f"Looking up: phase={prop[phase_col_props]}, risk={prop[risk_col_props]}")
                
                validation_match = self.validation_summary[
                    (self.validation_summary[phase_col_val] == prop[phase_col_props]) &
                    (self.validation_summary[risk_col_val] == prop[risk_col_props])
                ]
                
                if idx < props_to_analyze.index[0] + 1:  # Only debug first prop
                    print(f"  Found {len(validation_match)} matches")
            else:
                print(f"Warning: Could not find phase/risk columns in validation summary")
                print(f"Looking for phase in {self.validation_summary.columns.tolist()}")
                validation_match = pd.DataFrame()
            
            if validation_match.empty:
                # Use default values if no match found
                warning_key = f"{prop[phase_col_props]}/{prop[risk_col_props]}"
                if warning_key not in warnings_shown:
                    print(f"Warning: No validation data for {warning_key}")
                    warnings_shown.add(warning_key)
                
                validation_match = pd.DataFrame({
                    'win_rate': [0.5],
                    'actual_std': [4.0]
                })
            
            # Calculate bet sizing
            result = self.calculate_bet_percentage(prop, validation_match)
            kelly_fraction, bet_percentage, kelly_fraction_used = result
            
            # Get confidence for recommendation logic
            confidence = prop.get('confidence', prop.get('adv_confidence', prop.get('confidence_score', 0.7)))
            
            # Debug first prop
            if idx == props_to_analyze.index[0]:
                print(f"\nDEBUG - First prop calculation:")
                print(f"  Kelly fraction: {kelly_fraction:.3f}")
                print(f"  Bet percentage: {bet_percentage:.3f}")
                print(f"  Kelly used: {kelly_fraction_used:.0%}")
                print(f"  Confidence: {confidence:.1%}")
            
            # Determine recommendation
            # Only bet if we have positive Kelly and reasonable confidence
            # Increased threshold from 0.02 to 0.05 for more selectivity
            recommendation = "BET" if kelly_fraction > 0.05 and confidence > 0.65 else "NO BET"
            
            # Get std_dev value from validation match
            if not validation_match.empty:
                if 'actual_std' in validation_match.columns:
                    std_dev_value = validation_match['actual_std'].iloc[0]
                elif 'std_dev' in validation_match.columns:
                    std_dev_value = validation_match['std_dev'].iloc[0]
                else:
                    std_dev_value = 4.0
            else:
                std_dev_value = 4.0
            
            results.append({
                'player_name': prop['player_name'],
                'stat_type': prop['stat_type'],
                'line': prop['line'],
                'adjusted_prediction': prop.get('adjusted_prediction', prop.get('predicted_value', 0)),
                'adv_phase': prop[phase_col_props],
                'adv_risk_tag': prop[risk_col_props],
                'win_rate': validation_match['win_rate'].iloc[0] if not validation_match.empty else 0.5,
                'std_dev': std_dev_value,
                'kelly_fraction': round(kelly_fraction, 3),
                'kelly_used': round(kelly_fraction_used, 2),
                'bet_percentage': round(bet_percentage, 3),
                'confidence': confidence,
                'recommendation': recommendation
            })
        
        # Convert to DataFrame and sort by bet percentage
        betting_card = pd.DataFrame(results)
        betting_card = betting_card.sort_values('bet_percentage', ascending=False)
        
        # Apply diversification rules BEFORE bankroll constraints
        betting_card = self.apply_diversification(betting_card)
        
        # Re-sort after diversification
        betting_card = betting_card.sort_values('bet_percentage', ascending=False)
        
        # Apply total bankroll constraint
        max_total_allocation = 0.25  # Max 25% of bankroll in play
        
        # Calculate cumulative allocation
        betting_card['cumulative_allocation'] = betting_card['bet_percentage'].cumsum()
        
        # Find cutoff point where we exceed max allocation
        if len(betting_card[betting_card['recommendation'] == 'BET']) > 0:
            total_recommended = betting_card[betting_card['recommendation'] == 'BET']['bet_percentage'].sum()
            
            if total_recommended > max_total_allocation:
                print(f"\nWARNING: Total allocation ({total_recommended:.1%}) exceeds maximum ({max_total_allocation:.1%})")
                print("Applying scaling to fit within bankroll constraints...")
                
                # Save original allocation for reference
                self._scaling_applied = True
                self._original_allocation = total_recommended
                
                # Scale down all bet percentages proportionally
                scale_factor = max_total_allocation / total_recommended
                betting_card.loc[betting_card['recommendation'] == 'BET', 'bet_percentage'] *= scale_factor
                betting_card['bet_percentage'] = betting_card['bet_percentage'].round(3)
            else:
                self._scaling_applied = False
        
        # Remove cumulative column before saving
        betting_card = betting_card.drop('cumulative_allocation', axis=1)
        
        # Limit to top N bets if specified
        if max_bets and len(betting_card[betting_card['recommendation'] == 'BET']) > max_bets:
            print(f"\nLimiting output to top {max_bets} bets...")
            # Keep all NO BET recommendations but limit BET recommendations
            bet_rows = betting_card[betting_card['recommendation'] == 'BET'].head(max_bets)
            no_bet_rows = betting_card[betting_card['recommendation'] == 'NO BET']
            betting_card = pd.concat([bet_rows, no_bet_rows]).sort_values('bet_percentage', ascending=False)
        
        # Save to CSV - sort to show BET recommendations first
        output_path = Path('output/daily_betting_card.csv')
        output_path.parent.mkdir(exist_ok=True)
        
        # Sort by recommendation (BET first) then by bet_percentage
        betting_card['_sort_key'] = betting_card['recommendation'].apply(lambda x: 0 if x == 'BET' else 1)
        betting_card = betting_card.sort_values(['_sort_key', 'bet_percentage'], ascending=[True, False])
        betting_card = betting_card.drop('_sort_key', axis=1)
        
        betting_card.to_csv(output_path, index=False)
        
        print(f"Betting card saved to {output_path}")
        
        return betting_card
    
    def print_summary(self, betting_card):
        """Print summary statistics of betting recommendations"""
        print("\n" + "="*60)
        print("DAILY BETTING CARD SUMMARY")
        print("="*60)
        
        # Overall stats
        total_props = len(betting_card)
        recommended_bets = len(betting_card[betting_card['recommendation'] == 'BET'])
        total_bankroll_pct = betting_card[betting_card['recommendation'] == 'BET']['bet_percentage'].sum()
        
        print(f"\nTotal props analyzed: {total_props}")
        print(f"Recommended bets: {recommended_bets}")
        print(f"Total bankroll allocation: {total_bankroll_pct:.1%}")
        
        # Check if scaled
        if hasattr(self, '_scaling_applied') and self._scaling_applied:
            print(f"(Scaled down from {self._original_allocation:.1%} to fit within 25% constraint)")
        
        # Top bets
        top_bets = betting_card[betting_card['recommendation'] == 'BET'].head(5)
        if len(top_bets) > 0:
            print("\nTOP 5 RECOMMENDED BETS:")
            print("-"*60)
            for idx, bet in top_bets.iterrows():
                print(f"{bet['player_name']} - {bet['stat_type']} "
                      f"O{bet['line']} ({bet['bet_percentage']:.1%} of bankroll)")
                print(f"  Phase: {bet['adv_phase']}, Risk: {bet['adv_risk_tag']}")
                print(f"  Win Rate: {bet['win_rate']:.1%}, Kelly: {bet['kelly_fraction']:.3f}")
                if 'kelly_used' in bet:
                    print(f"  Kelly Fraction Used: {bet['kelly_used']:.0%}")
                if 'confidence' in bet:
                    print(f"  Confidence: {bet['confidence']:.1%}")
                print()
        
        # Phase breakdown
        print("\nBETS BY CYCLE PHASE:")
        print("-"*40)
        phase_col = 'adv_phase' if 'adv_phase' in betting_card.columns else 'cycle_phase'
        if len(betting_card[betting_card['recommendation'] == 'BET']) > 0:
            phase_summary = betting_card[betting_card['recommendation'] == 'BET'].groupby(phase_col).agg({
                'player_name': 'count',
                'bet_percentage': 'sum'
            }).rename(columns={'player_name': 'count'})
            
            for phase, data in phase_summary.iterrows():
                print(f"{phase}: {data['count']} bets, {data['bet_percentage']:.1%} of bankroll")
        else:
            print("No bets recommended")
        
        # Risk tag breakdown
        print("\nBETS BY RISK TAG:")
        print("-"*40)
        risk_col = 'adv_risk_tag' if 'adv_risk_tag' in betting_card.columns else 'cycle_risk_tag'
        if len(betting_card[betting_card['recommendation'] == 'BET']) > 0:
            risk_summary = betting_card[betting_card['recommendation'] == 'BET'].groupby(risk_col).agg({
                'player_name': 'count',
                'bet_percentage': 'sum'
            }).rename(columns={'player_name': 'count'})
            
            for risk, data in risk_summary.iterrows():
                print(f"{risk}: {data['count']} bets, {data['bet_percentage']:.1%} of bankroll")
        else:
            print("No bets recommended")
        
        # Confidence distribution
        print("\nCONFIDENCE DISTRIBUTION (for recommended bets):")
        print("-"*40)
        if len(betting_card[betting_card['recommendation'] == 'BET']) > 0 and 'confidence' in betting_card.columns:
            bets = betting_card[betting_card['recommendation'] == 'BET']
            high_conf = len(bets[bets['confidence'] > 0.8])
            med_conf = len(bets[(bets['confidence'] > 0.7) & (bets['confidence'] <= 0.8)])
            low_conf = len(bets[bets['confidence'] <= 0.7])
            
            print(f"High confidence (>80%): {high_conf} bets (using 33% Kelly)")
            print(f"Medium confidence (70-80%): {med_conf} bets (using 25% Kelly)")
            print(f"Lower confidence (≤70%): {low_conf} bets (using 20% Kelly)")
        
        # Player diversity breakdown
        print("\nPLAYER DIVERSITY:")
        print("-"*40)
        if len(betting_card[betting_card['recommendation'] == 'BET']) > 0:
            player_summary = betting_card[betting_card['recommendation'] == 'BET'].groupby('player_name').agg({
                'stat_type': 'count',
                'bet_percentage': 'sum'
            }).rename(columns={'stat_type': 'count'}).sort_values('bet_percentage', ascending=False)
            
            top_players = player_summary.head(10)
            for player, data in top_players.iterrows():
                print(f"{player}: {data['count']} bets, {data['bet_percentage']:.1%} of bankroll")
        else:
            print("No bets recommended")
        
        print("\n" + "="*60)
        
        # Print constraints applied
        print("\nCONSTRAINTS APPLIED:")
        print(f"- Kelly Fraction: Dynamic (20-33% based on confidence)")
        print(f"- Min Bet Size: {self.min_bet_pct:.1%} of bankroll")
        print(f"- Max Bet Size: {self.max_bet_pct:.1%} of bankroll")
        print(f"- Max Total Allocation: 25.0% of bankroll")
        print(f"- Max Bets per Phase/Risk: {self.max_bets_per_combo}")
        print(f"- Max Bets per Player: {self.max_bets_per_player}")
        print(f"- Min Kelly Edge Required: 5.0%")
        print(f"- Min Confidence Required: 65.0%")


def main():
    """Main execution function"""
    print("Starting Bankroll Optimization with Menstrual Intelligence...")
    print("="*60)
    
    # Initialize optimizer with conservative settings and diversification
    optimizer = BankrollOptimizer(
        min_bet_pct=0.005,         # 0.5% minimum
        max_bet_pct=0.025,         # 2.5% maximum (reduced from 5%)
        kelly_fraction=0.25,       # 1/4 Kelly for safety (not used with dynamic Kelly)
        max_bets_per_combo=5,      # Max 5 bets per phase/risk combination
        max_bets_per_player=2      # Max 2 bets per player
    )
    
    # Load data
    optimizer.load_data()
    
    # Generate betting card with max 20 bets and 48-hour window
    betting_card = optimizer.generate_betting_card(max_bets=20, hours_ahead=48)
    
    # Print summary
    optimizer.print_summary(betting_card)
    
    print("\nOptimization complete! Check output/daily_betting_card.csv for full results.")


if __name__ == "__main__":
    main()