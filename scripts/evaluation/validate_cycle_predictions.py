#!/usr/bin/env python3
"""
validate_cycle_predictions.py

Validates the effectiveness of menstrual cycle-based adjustments in WNBA prop predictions.
Compares adjusted predictions to actual outcomes and evaluates performance by phase and risk tag.

Author: Senior AI Engineer
Date: June 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging
from typing import Dict, Tuple, Any
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CyclePredictionValidator:
    """Validates menstrual cycle-based prop predictions against actual outcomes."""
    
    def __init__(self, data_path: str, output_dir: str):
        """
        Initialize the validator.
        
        Args:
            data_path: Path to the CSV with predictions and results
            output_dir: Directory for output files
        """
        self.data_path = Path(data_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.df = None
        self.validation_results = {}
        
    def load_data(self) -> pd.DataFrame:
        """Load and validate the predictions data."""
        try:
            self.df = pd.read_csv(self.data_path)
            logger.info(f"Loaded {len(self.df)} predictions from {self.data_path}")
            
            # Validate required columns
            required_cols = [
                'player_name', 'stat_type', 'line', 'adjusted_prediction',
                'actual_result', 'adv_phase', 'adv_modifier', 'adv_confidence',
                'adv_risk_tag'
            ]
            
            missing_cols = [col for col in required_cols if col not in self.df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Clean data
            self.df = self.df.dropna(subset=['adjusted_prediction', 'actual_result', 'line'])
            logger.info(f"Data cleaned: {len(self.df)} valid predictions")
            
            # Add computed columns
            self.df['prediction_margin'] = self.df['adjusted_prediction'] - self.df['line']
            self.df['actual_margin'] = self.df['actual_result'] - self.df['line']
            self.df['went_over'] = self.df['actual_result'] > self.df['line']
            
            # Determine if prediction was correct
            self.df['prediction_correct'] = (
                ((self.df['adjusted_prediction'] > self.df['line']) & 
                 (self.df['actual_result'] > self.df['line'])) |
                ((self.df['adjusted_prediction'] <= self.df['line']) & 
                 (self.df['actual_result'] <= self.df['line']))
            )
            
            return self.df
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def calculate_phase_metrics(self) -> pd.DataFrame:
        """Calculate performance metrics grouped by phase."""
        phase_metrics = []
        
        for phase in self.df['adv_phase'].unique():
            phase_data = self.df[self.df['adv_phase'] == phase]
            
            metrics = {
                'phase': phase,
                'count': len(phase_data),
                'win_rate': phase_data['prediction_correct'].mean(),
                'avg_prediction_margin': phase_data['prediction_margin'].mean(),
                'avg_actual_margin': phase_data['actual_margin'].mean(),
                'actual_std': phase_data['actual_result'].std(),
                'over_tendency': phase_data['went_over'].mean(),
                'avg_modifier': phase_data['adv_modifier'].mean(),
                'avg_confidence': phase_data['adv_confidence'].mean()
            }
            
            phase_metrics.append(metrics)
        
        return pd.DataFrame(phase_metrics)
    
    def calculate_risk_tag_metrics(self) -> pd.DataFrame:
        """Calculate performance metrics grouped by risk tag."""
        risk_metrics = []
        
        for risk_tag in self.df['adv_risk_tag'].unique():
            risk_data = self.df[self.df['adv_risk_tag'] == risk_tag]
            
            metrics = {
                'risk_tag': risk_tag,
                'count': len(risk_data),
                'win_rate': risk_data['prediction_correct'].mean(),
                'avg_prediction_margin': risk_data['prediction_margin'].mean(),
                'avg_actual_margin': risk_data['actual_margin'].mean(),
                'actual_std': risk_data['actual_result'].std(),
                'over_tendency': risk_data['went_over'].mean(),
                'margin_mae': abs(risk_data['prediction_margin'] - risk_data['actual_margin']).mean()
            }
            
            risk_metrics.append(metrics)
        
        return pd.DataFrame(risk_metrics)
    
    def calculate_combined_metrics(self) -> pd.DataFrame:
        """Calculate metrics for phase + risk tag combinations."""
        combined_metrics = []
        
        for phase in self.df['adv_phase'].unique():
            for risk_tag in self.df['adv_risk_tag'].unique():
                combo_data = self.df[
                    (self.df['adv_phase'] == phase) & 
                    (self.df['adv_risk_tag'] == risk_tag)
                ]
                
                if len(combo_data) > 0:
                    metrics = {
                        'phase': phase,
                        'risk_tag': risk_tag,
                        'count': len(combo_data),
                        'win_rate': combo_data['prediction_correct'].mean(),
                        'avg_prediction_margin': combo_data['prediction_margin'].mean(),
                        'avg_actual_margin': combo_data['actual_margin'].mean(),
                        'actual_std': combo_data['actual_result'].std(),
                        'over_tendency': combo_data['went_over'].mean()
                    }
                    
                    combined_metrics.append(metrics)
        
        return pd.DataFrame(combined_metrics)
    
    def calculate_global_metrics(self) -> Dict[str, float]:
        """Calculate overall model performance metrics."""
        global_metrics = {
            'total_predictions': len(self.df),
            'overall_win_rate': self.df['prediction_correct'].mean(),
            'overall_over_tendency': self.df['went_over'].mean(),
            'overall_prediction_mae': abs(self.df['adjusted_prediction'] - self.df['actual_result']).mean(),
            'overall_margin_mae': abs(self.df['prediction_margin'] - self.df['actual_margin']).mean(),
            
            # Phase-specific global stats
            'menstrual_win_rate': self.df[self.df['adv_phase'] == 'menstrual']['prediction_correct'].mean(),
            'follicular_win_rate': self.df[self.df['adv_phase'] == 'follicular']['prediction_correct'].mean(),
            'ovulation_win_rate': self.df[self.df['adv_phase'] == 'ovulation']['prediction_correct'].mean(),
            'luteal_win_rate': self.df[self.df['adv_phase'] == 'luteal']['prediction_correct'].mean(),
            
            # Risk tag global stats
            'neutral_win_rate': self.df[self.df['adv_risk_tag'] == 'NEUTRAL']['prediction_correct'].mean(),
            'target_ovulation_win_rate': self.df[self.df['adv_risk_tag'] == 'TARGET_OVULATION']['prediction_correct'].mean(),
            'fade_luteal_win_rate': self.df[self.df['adv_risk_tag'] == 'FADE_LUTEAL']['prediction_correct'].mean(),
        }
        
        # Handle NaN values
        global_metrics = {k: v if not pd.isna(v) else 0.0 for k, v in global_metrics.items()}
        
        return global_metrics
    
    def create_phase_winrate_chart(self, phase_metrics: pd.DataFrame):
        """Create horizontal bar chart of win rates by phase."""
        plt.figure(figsize=(10, 6))
        
        # Sort by win rate for better visualization
        phase_metrics_sorted = phase_metrics.sort_values('win_rate')
        
        # Create horizontal bar chart
        bars = plt.barh(phase_metrics_sorted['phase'], phase_metrics_sorted['win_rate'])
        
        # Color bars based on performance
        colors = ['red' if x < 0.5 else 'green' for x in phase_metrics_sorted['win_rate']]
        for bar, color in zip(bars, colors):
            bar.set_color(color)
            bar.set_alpha(0.7)
        
        # Add value labels
        for i, (phase, win_rate) in enumerate(zip(phase_metrics_sorted['phase'], 
                                                  phase_metrics_sorted['win_rate'])):
            plt.text(win_rate + 0.01, i, f'{win_rate:.3f}', 
                    va='center', fontsize=10)
        
        # Add 50% reference line
        plt.axvline(x=0.5, color='black', linestyle='--', alpha=0.5, label='50% (Random)')
        
        plt.xlabel('Win Rate', fontsize=12)
        plt.ylabel('Menstrual Phase', fontsize=12)
        plt.title('Prediction Win Rate by Menstrual Phase', fontsize=14, fontweight='bold')
        plt.xlim(0, max(0.7, phase_metrics['win_rate'].max() + 0.1))
        plt.legend()
        plt.tight_layout()
        
        output_path = self.output_dir / 'phase_winrate_chart.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Phase win rate chart saved to {output_path}")
    
    def create_risk_tag_margin_distribution(self):
        """Create boxplot of actual margins by risk tag."""
        plt.figure(figsize=(12, 8))
        
        # Create boxplot
        risk_tags = sorted(self.df['adv_risk_tag'].unique())
        data_by_tag = [self.df[self.df['adv_risk_tag'] == tag]['actual_margin'].values 
                      for tag in risk_tags]
        
        bp = plt.boxplot(data_by_tag, labels=risk_tags, patch_artist=True)
        
        # Color boxes based on risk tag type
        colors = {
            'NEUTRAL': 'lightblue',
            'TARGET_OVULATION': 'lightgreen',
            'FADE_LUTEAL': 'lightcoral',
            'FADE_MENSTRUAL': 'lightyellow',
            'TARGET_FOLLICULAR': 'lightpink'
        }
        
        for patch, tag in zip(bp['boxes'], risk_tags):
            patch.set_facecolor(colors.get(tag, 'lightgray'))
            patch.set_alpha(0.7)
        
        # Add horizontal line at 0
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        
        # Add sample sizes
        for i, tag in enumerate(risk_tags):
            count = len(self.df[self.df['adv_risk_tag'] == tag])
            plt.text(i + 1, plt.ylim()[0] + 0.5, f'n={count}', 
                    ha='center', fontsize=9, style='italic')
        
        plt.xlabel('Risk Tag', fontsize=12)
        plt.ylabel('Actual Margin (Actual Result - Line)', fontsize=12)
        plt.title('Distribution of Actual Margins by Risk Tag', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        output_path = self.output_dir / 'risk_tag_margin_distribution.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Risk tag margin distribution saved to {output_path}")
    
    def save_validation_summary(self, phase_metrics: pd.DataFrame, 
                               risk_metrics: pd.DataFrame,
                               combined_metrics: pd.DataFrame,
                               global_metrics: Dict[str, float]):
        """Save comprehensive validation summary to CSV."""
        # Create summary dataframe
        summary_data = []
        
        # Add phase metrics
        for _, row in phase_metrics.iterrows():
            summary_data.append({
                'grouping_type': 'phase',
                'grouping_value': row['phase'],
                **row.to_dict()
            })
        
        # Add risk tag metrics
        for _, row in risk_metrics.iterrows():
            summary_data.append({
                'grouping_type': 'risk_tag',
                'grouping_value': row['risk_tag'],
                **row.to_dict()
            })
        
        # Add combined metrics
        for _, row in combined_metrics.iterrows():
            summary_data.append({
                'grouping_type': 'phase_risk_combo',
                'grouping_value': f"{row['phase']}_{row['risk_tag']}",
                **row.to_dict()
            })
        
        # Add global metrics
        for key, value in global_metrics.items():
            summary_data.append({
                'grouping_type': 'global',
                'grouping_value': key,
                'metric_value': value
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        output_path = self.output_dir / 'cycle_validation_summary.csv'
        summary_df.to_csv(output_path, index=False)
        logger.info(f"Validation summary saved to {output_path}")
    
    def print_key_findings(self, phase_metrics: pd.DataFrame, 
                          risk_metrics: pd.DataFrame,
                          global_metrics: Dict[str, float]):
        """Print key findings to console."""
        print("\n" + "="*60)
        print("CYCLE PREDICTION VALIDATION - KEY FINDINGS")
        print("="*60)
        
        print(f"\nOVERALL PERFORMANCE:")
        print(f"  Total Predictions: {global_metrics['total_predictions']:,}")
        print(f"  Overall Win Rate: {global_metrics['overall_win_rate']:.1%}")
        print(f"  Overall MAE: {global_metrics['overall_prediction_mae']:.2f}")
        
        print(f"\nPERFORMANCE BY PHASE:")
        for _, row in phase_metrics.iterrows():
            print(f"  {row['phase'].capitalize():12} - Win Rate: {row['win_rate']:.1%} "
                  f"(n={row['count']:,}, modifier: {row['avg_modifier']:+.3f})")
        
        print(f"\nPERFORMANCE BY RISK TAG:")
        for _, row in risk_metrics.iterrows():
            print(f"  {row['risk_tag']:20} - Win Rate: {row['win_rate']:.1%} "
                  f"(n={row['count']:,})")
        
        # Identify best and worst performing segments
        best_phase = phase_metrics.loc[phase_metrics['win_rate'].idxmax()]
        worst_phase = phase_metrics.loc[phase_metrics['win_rate'].idxmin()]
        
        print(f"\nBEST PHASE: {best_phase['phase']} ({best_phase['win_rate']:.1%})")
        print(f"WORST PHASE: {worst_phase['phase']} ({worst_phase['win_rate']:.1%})")
        
        print("\n" + "="*60)
    
    def run_validation(self):
        """Execute the full validation pipeline."""
        logger.info("Starting cycle prediction validation...")
        
        # Load data
        self.load_data()
        
        # Calculate metrics
        phase_metrics = self.calculate_phase_metrics()
        risk_metrics = self.calculate_risk_tag_metrics()
        combined_metrics = self.calculate_combined_metrics()
        global_metrics = self.calculate_global_metrics()
        
        # Create visualizations
        self.create_phase_winrate_chart(phase_metrics)
        self.create_risk_tag_margin_distribution()
        
        # Save results
        self.save_validation_summary(phase_metrics, risk_metrics, 
                                   combined_metrics, global_metrics)
        
        # Print findings
        self.print_key_findings(phase_metrics, risk_metrics, global_metrics)
        
        logger.info("Validation complete!")
        
        return {
            'phase_metrics': phase_metrics,
            'risk_metrics': risk_metrics,
            'combined_metrics': combined_metrics,
            'global_metrics': global_metrics
        }


def main():
    """Main execution function."""
    # Set up paths relative to project root
    project_root = Path.cwd()
    data_path = project_root / 'data' / 'final_props_with_advanced_cycles.csv'
    output_dir = project_root / 'output'
    
    # Initialize and run validator
    validator = CyclePredictionValidator(
        data_path=str(data_path),
        output_dir=str(output_dir)
    )
    
    try:
        results = validator.run_validation()
        logger.info("Validation completed successfully!")
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    main()