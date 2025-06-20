#!/usr/bin/env python3
"""
TARS Module: Cycle Risk Tag Backtesting Engine
Purpose: Validate cycle_risk_tag effectiveness on prop betting outcomes
Integration: Analyzes historical performance of risk tags vs actual outcomes
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
import json

class CycleRiskBacktester:
    """
    Backtests the effectiveness of cycle risk tags on prop performance.
    Validates FADE_LUTEAL, TARGET_OVULATION, and other risk signals.
    """
    
    def __init__(self, hit_threshold: float = 0.5):
        self.hit_threshold = hit_threshold  # For over/under analysis
        self.results = {}
        self.tag_performance = {}
        
    def backtest_props(self, props_df: pd.DataFrame, gamelogs_df: pd.DataFrame) -> Dict:
        """
        Main backtesting function for cycle risk tags.
        
        Args:
            props_df: Props with predictions and cycle_risk_tags
            gamelogs_df: Historical gamelogs with actual outcomes
            
        Returns:
            Dictionary with backtest results
        """
        print("[TARS] Initiating cycle risk tag backtest...")
        
        # Merge props with actuals
        merged_df = self._merge_props_with_actuals(props_df, gamelogs_df)
        
        # Analyze each risk tag
        risk_tags = merged_df['cycle_risk_tag'].unique()
        
        for tag in risk_tags:
            if pd.notna(tag):
                self.tag_performance[tag] = self._analyze_risk_tag(merged_df, tag)
                
        # Calculate overall statistics
        self.results = {
            'tag_performance': self.tag_performance,
            'best_fade_tags': self._identify_best_fade_tags(),
            'best_target_tags': self._identify_best_target_tags(),
            'phase_correlations': self._calculate_phase_correlations(merged_df),
            'volatility_accuracy': self._validate_volatility_scores(merged_df)
        }
        
        return self.results
    
    def _merge_props_with_actuals(self, props_df: pd.DataFrame, 
                                  gamelogs_df: pd.DataFrame) -> pd.DataFrame:
        """Merge predicted props with actual game outcomes."""
        # Ensure date formats match
        props_df['game_date'] = pd.to_datetime(props_df['game_date'])
        gamelogs_df['game_date'] = pd.to_datetime(gamelogs_df['game_date'])
        
        # Select relevant columns from gamelogs
        actuals_cols = [
            'player_id', 'game_date', 'actual_fantasy_points', 
            'points', 'rebounds', 'assists', 'minutes'
        ]
        
        # Merge on player_id and game_date
        merged = pd.merge(
            props_df,
            gamelogs_df[actuals_cols],
            on=['player_id', 'game_date'],
            how='inner'
        )
        
        return merged
    
    def _analyze_risk_tag(self, df: pd.DataFrame, tag: str) -> Dict:
        """Analyze performance of a specific risk tag."""
        tag_data = df[df['cycle_risk_tag'] == tag].copy()
        
        if len(tag_data) == 0:
            return {}
            
        results = {
            'tag': tag,
            'sample_size': len(tag_data),
            'prop_types': {}
        }
        
        # Analyze different prop types
        for prop_type in ['points', 'rebounds', 'assists', 'fantasy_points']:
            if f'predicted_{prop_type}' in tag_data.columns:
                prop_results = self._analyze_prop_type(tag_data, prop_type)
                results['prop_types'][prop_type] = prop_results
                
        # Calculate tag effectiveness metrics
        results['fade_effectiveness'] = self._calculate_fade_effectiveness(tag, results)
        results['target_effectiveness'] = self._calculate_target_effectiveness(tag, results)
        
        return results
    
    def _analyze_prop_type(self, df: pd.DataFrame, prop_type: str) -> Dict:
        """Analyze specific prop type performance."""
        pred_col = f'predicted_{prop_type}'
        actual_col = prop_type if prop_type != 'fantasy_points' else 'actual_fantasy_points'
        
        if pred_col not in df.columns or actual_col not in df.columns:
            return {}
            
        # Remove rows with missing data
        clean_df = df[[pred_col, actual_col]].dropna()
        
        if len(clean_df) == 0:
            return {}
            
        # Calculate hit rates for over/under
        clean_df['hit_over'] = clean_df[actual_col] > clean_df[pred_col]
        clean_df['hit_under'] = clean_df[actual_col] < clean_df[pred_col]
        clean_df['push'] = clean_df[actual_col] == clean_df[pred_col]
        
        # Calculate percentage differences
        clean_df['pct_diff'] = (clean_df[actual_col] - clean_df[pred_col]) / clean_df[pred_col]
        clean_df['pct_diff'] = clean_df['pct_diff'].replace([np.inf, -np.inf], np.nan)
        
        return {
            'over_rate': clean_df['hit_over'].mean(),
            'under_rate': clean_df['hit_under'].mean(),
            'push_rate': clean_df['push'].mean(),
            'avg_pct_diff': clean_df['pct_diff'].mean(),
            'std_pct_diff': clean_df['pct_diff'].std(),
            'sample_size': len(clean_df)
        }
    
    def _calculate_fade_effectiveness(self, tag: str, results: Dict) -> float:
        """Calculate how effective a FADE tag is."""
        if 'FADE' not in tag:
            return 0.0
            
        fade_scores = []
        
        for prop_type, prop_results in results['prop_types'].items():
            if 'under_rate' in prop_results:
                # FADE tags should have high under rates
                fade_scores.append(prop_results['under_rate'])
                
        return np.mean(fade_scores) if fade_scores else 0.0
    
    def _calculate_target_effectiveness(self, tag: str, results: Dict) -> float:
        """Calculate how effective a TARGET tag is."""
        if 'TARGET' not in tag:
            return 0.0
            
        target_scores = []
        
        for prop_type, prop_results in results['prop_types'].items():
            if 'over_rate' in prop_results:
                # TARGET tags should have high over rates
                target_scores.append(prop_results['over_rate'])
                
        return np.mean(target_scores) if target_scores else 0.0
    
    def _identify_best_fade_tags(self) -> List[Tuple[str, float]]:
        """Identify the most effective FADE tags."""
        fade_tags = []
        
        for tag, performance in self.tag_performance.items():
            if 'FADE' in tag and 'fade_effectiveness' in performance:
                fade_tags.append((tag, performance['fade_effectiveness']))
                
        return sorted(fade_tags, key=lambda x: x[1], reverse=True)[:5]
    
    def _identify_best_target_tags(self) -> List[Tuple[str, float]]:
        """Identify the most effective TARGET tags."""
        target_tags = []
        
        for tag, performance in self.tag_performance.items():
            if 'TARGET' in tag and 'target_effectiveness' in performance:
                target_tags.append((tag, performance['target_effectiveness']))
                
        return sorted(target_tags, key=lambda x: x[1], reverse=True)[:5]
    
    def _calculate_phase_correlations(self, df: pd.DataFrame) -> Dict:
        """Calculate correlations between cycle phases and performance."""
        phase_correlations = {}
        
        # Map phases to numeric values for correlation
        phase_map = {
            'menstrual': 1,
            'follicular': 2, 
            'ovulation': 3,
            'luteal': 4
        }
        
        df['phase_numeric'] = df['cycle_phase'].map(phase_map)
        
        # Calculate correlations for each stat
        for stat in ['points', 'rebounds', 'assists', 'actual_fantasy_points']:
            if stat in df.columns:
                # Calculate actual vs predicted difference
                pred_stat = f'predicted_{stat}' if stat != 'actual_fantasy_points' else 'predicted_fantasy_points'
                if pred_stat in df.columns:
                    df[f'{stat}_diff'] = df[stat] - df[pred_stat]
                    
                    # Correlation between phase and performance difference
                    corr = df[['phase_numeric', f'{stat}_diff']].corr().iloc[0, 1]
                    phase_correlations[stat] = corr
                    
        return phase_correlations
    
    def _validate_volatility_scores(self, df: pd.DataFrame) -> Dict:
        """Validate if volatility scores accurately predict variance."""
        volatility_validation = {}
        
        # Group by volatility score ranges
        df['volatility_bucket'] = pd.cut(
            df['volatility_score'], 
            bins=[0, 0.8, 0.9, 1.0, 1.1, 1.2, np.inf],
            labels=['very_low', 'low', 'normal', 'high', 'very_high', 'extreme']
        )
        
        for bucket in df['volatility_bucket'].unique():
            if pd.notna(bucket):
                bucket_data = df[df['volatility_bucket'] == bucket]
                
                # Calculate actual variance in outcomes
                variances = []
                for stat in ['points', 'rebounds', 'assists']:
                    if f'predicted_{stat}' in bucket_data.columns:
                        pred_col = f'predicted_{stat}'
                        actual_col = stat
                        
                        # Calculate percentage variance from prediction
                        pct_vars = np.abs(
                            (bucket_data[actual_col] - bucket_data[pred_col]) / 
                            bucket_data[pred_col]
                        ).replace([np.inf, -np.inf], np.nan).dropna()
                        
                        if len(pct_vars) > 0:
                            variances.append(pct_vars.mean())
                            
                volatility_validation[str(bucket)] = {
                    'avg_variance': np.mean(variances) if variances else 0,
                    'sample_size': len(bucket_data)
                }
                
        return volatility_validation
    
    def generate_backtest_report(self, output_path: str = 'output/cycle_risk_backtest_report.json'):
        """Generate comprehensive backtest report."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_tags_analyzed': len(self.tag_performance),
                'best_fade_tags': self.results['best_fade_tags'],
                'best_target_tags': self.results['best_target_tags']
            },
            'detailed_results': self.results,
            'recommendations': self._generate_recommendations()
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        print(f"[TARS] Backtest report saved to {output_path}")
        
        # Print summary
        self._print_summary()
        
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations from backtest."""
        recommendations = []
        
        # Check FADE effectiveness
        if self.results['best_fade_tags']:
            top_fade = self.results['best_fade_tags'][0]
            if top_fade[1] > 0.55:  # 55% under rate
                recommendations.append(
                    f"STRONG SIGNAL: {top_fade[0]} shows {top_fade[1]:.1%} under rate. "
                    "Consider increasing fade confidence for this tag."
                )
                
        # Check TARGET effectiveness  
        if self.results['best_target_tags']:
            top_target = self.results['best_target_tags'][0]
            if top_target[1] > 0.55:  # 55% over rate
                recommendations.append(
                    f"STRONG SIGNAL: {top_target[0]} shows {top_target[1]:.1%} over rate. "
                    "Consider increasing target confidence for this tag."
                )
                
        # Check phase correlations
        phase_corrs = self.results['phase_correlations']
        for stat, corr in phase_corrs.items():
            if abs(corr) > 0.15:  # Significant correlation
                direction = "higher" if corr > 0 else "lower"
                recommendations.append(
                    f"PHASE PATTERN: {stat} shows {direction} performance in later cycle phases "
                    f"(correlation: {corr:.3f})"
                )
                
        # Volatility validation
        vol_accuracy = self.results['volatility_accuracy']
        high_vol_variance = vol_accuracy.get('very_high', {}).get('avg_variance', 0)
        low_vol_variance = vol_accuracy.get('low', {}).get('avg_variance', 0)
        
        if high_vol_variance > low_vol_variance * 1.5:
            recommendations.append(
                "VOLATILITY VALIDATED: High volatility scores correctly predict "
                f"{(high_vol_variance/low_vol_variance - 1)*100:.0f}% more variance"
            )
            
        return recommendations
    
    def _print_summary(self):
        """Print backtest summary to console."""
        print("\n" + "="*60)
        print("[TARS] CYCLE RISK TAG BACKTEST SUMMARY")
        print("="*60)
        
        print("\nTOP FADE TAGS:")
        for tag, effectiveness in self.results['best_fade_tags'][:3]:
            print(f"  - {tag}: {effectiveness:.1%} under rate")
            
        print("\nTOP TARGET TAGS:")
        for tag, effectiveness in self.results['best_target_tags'][:3]:
            print(f"  - {tag}: {effectiveness:.1%} over rate")
            
        print("\nVOLATILITY VALIDATION:")
        for bucket, stats in sorted(self.results['volatility_accuracy'].items()):
            if stats['sample_size'] > 10:
                print(f"  - {bucket}: {stats['avg_variance']:.1%} avg variance "
                      f"(n={stats['sample_size']})")
                      
        print("\nKEY RECOMMENDATIONS:")
        for i, rec in enumerate(self.results['recommendations'][:3], 1):
            print(f"  {i}. {rec}")
            
        print("="*60)

def run_backtest(props_path: str, gamelogs_path: str):
    """Execute full backtest pipeline."""
    # Load data
    props_df = pd.read_csv(props_path)
    gamelogs_df = pd.read_csv(gamelogs_path)
    
    # Initialize backtester
    backtester = CycleRiskBacktester(hit_threshold=0.5)
    
    # Run backtest
    results = backtester.backtest_props(props_df, gamelogs_df)
    
    # Generate report
    backtester.generate_backtest_report()
    
    return results

if __name__ == "__main__":
    # Example execution
    run_backtest(
        props_path='data/wnba_clean_props_for_betting.csv',
        gamelogs_path='data/wnba_gamelogs_with_cycle_phases.csv'
    )