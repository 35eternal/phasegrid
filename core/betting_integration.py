#!/usr/bin/env python3
"""
betting_integration_example.py - Integration Example
Shows how to combine cycle dip detection with existing betting analysis.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

class BettingIntelligenceSystem:
    """
    Combines performance dip detection with props analysis for betting intelligence.
    """
    
    def __init__(self, dips_file='output/detected_performance_dips.csv', 
                 props_file='data/wnba_prizepicks_props.csv'):
        """
        Initialize the betting intelligence system.
        
        Args:
            dips_file (str): Path to performance dips analysis
            props_file (str): Path to current props data
        """
        self.dips_file = dips_file
        self.props_file = props_file
        self.dips_data = None
        self.props_data = None
        self.opportunities = None
        
    def load_data(self):
        """Load both performance dips and props data."""
        print("Loading performance dips and props data...")
        
        try:
            # Load performance dips
            if Path(self.dips_file).exists():
                self.dips_data = pd.read_csv(self.dips_file)
                self.dips_data['date'] = pd.to_datetime(self.dips_data['date'])
                print(f"✅ Loaded {len(self.dips_data)} dip records")
            else:
                print(f"❌ Dips file not found: {self.dips_file}")
                return False
            
            # Load props data  
            if Path(self.props_file).exists():
                self.props_data = pd.read_csv(self.props_file)
                print(f"✅ Loaded {len(self.props_data)} prop records")
            else:
                print(f"❌ Props file not found: {self.props_file}")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    def identify_under_opportunities(self):
        """
        Identify UNDER betting opportunities based on performance dips.
        
        Returns:
            pd.DataFrame: Betting opportunities with recommendations
        """
        print("Identifying UNDER betting opportunities...")
        
        if self.dips_data is None or self.props_data is None:
            print("Data not loaded!")
            return pd.DataFrame()
        
        # Get players currently in concerning phases
        concerning_phases = ['Descending', 'Trough']
        recent_concerns = self.dips_data[
            self.dips_data['trend_phase'].isin(concerning_phases)
        ].copy()
        
        # Get most recent record for each concerning player
        latest_concerns = recent_concerns.groupby('player').apply(
            lambda x: x.loc[x['date'].idxmax()]
        ).reset_index(drop=True)
        
        # Match with current props
        opportunities = []
        
        for _, concern in latest_concerns.iterrows():
            player_name = concern['player']
            
            # Find matching props (try exact match first, then fuzzy)
            player_props = self.props_data[
                self.props_data['player_name'] == player_name
            ].copy()
            
            if len(player_props) == 0:
                # Try fuzzy matching for slight name differences
                player_props = self.props_data[
                    self.props_data['player_name'].str.contains(
                        player_name.split()[0], case=False, na=False
                    )
                ].copy()
            
            # Create opportunity records for each prop
            for _, prop in player_props.iterrows():
                opportunity = {
                    'player': player_name,
                    'stat_type': prop['stat_type'],
                    'line_score': prop['line_score'],
                    'trend_phase': concern['trend_phase'],
                    'games_in_trend': concern['games_in_trend'],
                    'dip_type': concern['dip_type'],
                    'confidence_score': self._calculate_confidence_score(concern, prop),
                    'recommendation': 'UNDER',
                    'reasoning': self._generate_reasoning(concern, prop)
                }
                
                # Add recent performance data if available
                if 'fantasy_points_roll_3' in concern.index:
                    opportunity['recent_avg'] = concern['fantasy_points_roll_3']
                if 'percent_drop_from_avg' in concern.index:
                    opportunity['drop_percentage'] = concern['percent_drop_from_avg']
                    
                opportunities.append(opportunity)
        
        self.opportunities = pd.DataFrame(opportunities)
        
        if len(self.opportunities) > 0:
            # Sort by confidence score
            self.opportunities = self.opportunities.sort_values(
                'confidence_score', ascending=False
            )
            print(f"✅ Found {len(self.opportunities)} UNDER opportunities")
        else:
            print("ℹ️ No UNDER opportunities found")
            
        return self.opportunities
    
    def _calculate_confidence_score(self, concern, prop):
        """
        Calculate confidence score for the betting opportunity.
        
        Args:
            concern (pd.Series): Performance concern data
            prop (pd.Series): Props data
            
        Returns:
            float: Confidence score (0-100)
        """
        score = 50  # Base score
        
        # Trend phase scoring
        if concern['trend_phase'] == 'Trough':
            score += 30
        elif concern['trend_phase'] == 'Descending':
            score += 20
            
        # Trend duration scoring
        games_in_trend = concern['games_in_trend']
        if games_in_trend >= 4:
            score += 20
        elif games_in_trend >= 2:
            score += 10
            
        # Dip type scoring
        if concern['dip_type'] == 'cycle':
            score += 15
        elif concern['dip_type'] == 'fatigue':
            score += 10
            
        # Performance drop scoring
        if 'percent_drop_from_avg' in concern.index:
            drop_pct = abs(concern['percent_drop_from_avg'])
            if drop_pct > 25:
                score += 20
            elif drop_pct > 15:
                score += 10
                
        # Stat type considerations
        stat_type = prop['stat_type'].lower()
        if stat_type in ['points', 'fantasy_points']:
            score += 5  # High-impact stats
        elif stat_type in ['assists', 'rebounds']:
            score += 3  # Medium-impact stats
            
        return min(score, 95)  # Cap at 95
    
    def _generate_reasoning(self, concern, prop):
        """
        Generate human-readable reasoning for the recommendation.
        
        Args:
            concern (pd.Series): Performance concern data  
            prop (pd.Series): Props data
            
        Returns:
            str: Reasoning text
        """
        reasons = []
        
        # Trend information
        trend = concern['trend_phase']
        games = concern['games_in_trend']
        reasons.append(f"{trend} trend for {games} games")
        
        # Dip type information
        dip_type = concern['dip_type']
        if dip_type == 'cycle':
            reasons.append("cyclical performance pattern detected")
        elif dip_type == 'fatigue':
            reasons.append("potential fatigue-related decline")
        elif dip_type == 'unknown':
            reasons.append("unclear dip cause")
            
        # Performance drop information
        if 'percent_drop_from_avg' in concern.index:
            drop = abs(concern['percent_drop_from_avg'])
            reasons.append(f"{drop:.1f}% below season average")
            
        return "; ".join(reasons)
    
    def generate_daily_report(self, min_confidence=60):
        """
        Generate a daily betting report.
        
        Args:
            min_confidence (int): Minimum confidence score to include
            
        Returns:
            str: Formatted report
        """
        if self.opportunities is None:
            self.identify_under_opportunities()
            
        high_confidence = self.opportunities[
            self.opportunities['confidence_score'] >= min_confidence
        ].copy()
        
        report = []
        report.append("="*60)
        report.append("WNBA DAILY BETTING INTELLIGENCE REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*60)
        
        if len(high_confidence) == 0:
            report.append("No high-confidence opportunities found today.")
            return "\n".join(report)
            
        report.append(f"\nHIGH-CONFIDENCE UNDER OPPORTUNITIES ({min_confidence}+ confidence):")
        report.append("-" * 40)
        
        for i, (_, opp) in enumerate(high_confidence.iterrows(), 1):
            report.append(f"\n{i}. {opp['player']} - {opp['stat_type']}")
            report.append(f"   Line: {opp['line_score']}")
            report.append(f"   Recommendation: {opp['recommendation']}")
            report.append(f"   Confidence: {opp['confidence_score']:.0f}%")
            report.append(f"   Reasoning: {opp['reasoning']}")
            
            if 'recent_avg' in opp.index and pd.notna(opp['recent_avg']):
                report.append(f"   Recent 3-game avg: {opp['recent_avg']:.1f}")
        
        # Summary statistics
        report.append(f"\nSUMMARY:")
        report.append(f"  Total opportunities: {len(self.opportunities)}")
        report.append(f"  High-confidence: {len(high_confidence)}")
        
        if len(high_confidence) > 0:
            avg_confidence = high_confidence['confidence_score'].mean()
            report.append(f"  Average confidence: {avg_confidence:.1f}%")
        
        report.append("="*60)
        
        return "\n".join(report)
    
    def export_opportunities(self, filename='betting_opportunities.csv'):
        """
        Export opportunities to CSV file.
        
        Args:
            filename (str): Output filename
        """
        if self.opportunities is None:
            self.identify_under_opportunities()
            
        if len(self.opportunities) > 0:
            self.opportunities.to_csv(filename, index=False)
            print(f"✅ Exported {len(self.opportunities)} opportunities to {filename}")
        else:
            print("ℹ️ No opportunities to export")

def main():
    """
    Example usage of the betting intelligence system.
    """
    print("WNBA Betting Intelligence System - Example Usage")
    print("=" * 50)
    
    # Initialize system
    betting_system = BettingIntelligenceSystem()
    
    # Load data
    if not betting_system.load_data():
        print("❌ Failed to load data. Make sure files exist:")
        print("  - output/detected_performance_dips.csv")
        print("  - data/wnba_prizepicks_props.csv")
        return
    
    # Identify opportunities
    opportunities = betting_system.identify_under_opportunities()
    
    # Generate and print daily report
    report = betting_system.generate_daily_report(min_confidence=70)
    print("\n" + report)
    
    # Export opportunities
    betting_system.export_opportunities('output/daily_betting_opportunities.csv')
    
    print("\n" + "="*50)
    print("INTEGRATION COMPLETE")
    print("="*50)
    print("Next steps:")
    print("1. Review opportunities in output/daily_betting_opportunities.csv")
    print("2. Cross-reference with your risk management rules")
    print("3. Place UNDER bets on high-confidence opportunities")
    print("4. Track results for system validation")

if __name__ == "__main__":
    main()