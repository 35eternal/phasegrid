#!/usr/bin/env python3
"""
Cycle-Aware Pattern Detector for WNBA Performance Analysis
Analyzes player performance data for cyclical patterns and variations
"""

import pandas as pd
import numpy as np
from scipy import stats, signal
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class CycleAwarePatternDetector:
    """Detects cyclical performance patterns in WNBA player statistics"""
    
    def __init__(self, cycle_length=28, cycle_range=(25, 32), min_games=30):
        self.cycle_length = cycle_length
        self.cycle_range = cycle_range
        self.min_games = min_games
        self.target_metrics = ['PTS', 'REB', 'AST']
        
    def load_data(self, filepath):
        """Load and prepare game log data"""
        self.df = pd.read_csv(filepath)
        # Fix date parsing with explicit format
        self.df['GAME_DATE'] = pd.to_datetime(self.df['GAME_DATE'], format='%Y-%m-%d')
        self.df = self.df.sort_values(['PLAYER_NAME', 'GAME_DATE'])
        return self.df
    
    def calculate_performance_baseline(self, player_data, metric):
        """Calculate rolling baseline performance for a metric"""
        # Use 10-game rolling average as baseline
        baseline = player_data[metric].rolling(window=10, min_periods=5).mean()
        # Fill initial values with season average
        season_avg = player_data[metric].mean()
        baseline = baseline.fillna(season_avg)
        return baseline
    
    def detect_performance_dips(self, player_data, metric, threshold=0.8):
        """Identify significant performance dips below baseline"""
        baseline = self.calculate_performance_baseline(player_data, metric)
        
        # Calculate relative performance
        relative_perf = player_data[metric] / baseline
        
        # Identify dips (performance < 80% of baseline)
        dips = []
        for idx, (date, perf) in enumerate(zip(player_data['GAME_DATE'], relative_perf)):
            if perf < threshold and not pd.isna(perf):
                # Calculate dip magnitude
                magnitude = 1 - perf
                dips.append({
                    'date': date,
                    'index': idx,
                    'magnitude': magnitude,
                    'actual': player_data[metric].iloc[idx],
                    'expected': baseline.iloc[idx]
                })
        
        return dips
    
    def analyze_dip_periodicity(self, dips, player_data):
        """Analyze if dips follow a cyclical pattern"""
        if len(dips) < 3:
            return None
        
        # Extract dip dates and calculate intervals
        dip_dates = [d['date'] for d in dips]
        intervals = []
        for i in range(1, len(dip_dates)):
            interval = (dip_dates[i] - dip_dates[i-1]).days
            intervals.append(interval)
        
        if not intervals:
            return None
        
        # Check if intervals cluster around expected cycle length
        results = {
            'intervals': intervals,
            'mean_interval': np.mean(intervals),
            'std_interval': np.std(intervals),
            'cycle_matches': 0,
            'periodicity_score': 0
        }
        
        # Count intervals within cycle range
        for interval in intervals:
            if self.cycle_range[0] <= interval <= self.cycle_range[1]:
                results['cycle_matches'] += 1
        
        # Calculate periodicity score (0-1)
        if len(intervals) > 0:
            match_ratio = results['cycle_matches'] / len(intervals)
            interval_consistency = 1 - (results['std_interval'] / results['mean_interval'] if results['mean_interval'] > 0 else 1)
            results['periodicity_score'] = (match_ratio + interval_consistency) / 2
        
        return results
    
    def classify_dip_pattern(self, periodicity_results, dip_magnitudes):
        """Classify the nature of performance dips"""
        if periodicity_results is None:
            return "Unknown", 0.0
        
        periodicity_score = periodicity_results['periodicity_score']
        avg_magnitude = np.mean(dip_magnitudes)
        
        # Classification logic
        if periodicity_score > 0.7 and avg_magnitude > 0.15:
            return "Possible Cycle Dip", periodicity_score
        elif periodicity_score < 0.4 and avg_magnitude > 0.2:
            return "Likely Fatigue", 1 - periodicity_score
        else:
            return "Unknown", 0.5
        
    def find_optimal_cycle_length(self, player_data, metric):
        """Find the cycle length that best fits the data"""
        best_score = 0
        best_length = self.cycle_length
        
        for test_length in range(self.cycle_range[0], self.cycle_range[1] + 1):
            # Temporary update cycle length
            original_length = self.cycle_length
            self.cycle_length = test_length
            
            # Detect dips and analyze periodicity
            dips = self.detect_performance_dips(player_data, metric)
            if len(dips) >= 3:
                periodicity = self.analyze_dip_periodicity(dips, player_data)
                if periodicity and periodicity['periodicity_score'] > best_score:
                    best_score = periodicity['periodicity_score']
                    best_length = test_length
            
            self.cycle_length = original_length
        
        return best_length, best_score
    
    def analyze_player(self, player_name):
        """Comprehensive analysis for a single player"""
        player_data = self.df[self.df['PLAYER_NAME'] == player_name].copy()
        
        if len(player_data) < self.min_games:
            return None
        
        results = {
            'player_name': player_name,
            'total_games': len(player_data),
            'date_range': f"{player_data['GAME_DATE'].min().date()} to {player_data['GAME_DATE'].max().date()}",
            'metrics': {}
        }
        
        # Analyze each metric
        for metric in self.target_metrics:
            if metric not in player_data.columns:
                continue
                
            # Find optimal cycle length for this metric
            optimal_length, opt_score = self.find_optimal_cycle_length(player_data, metric)
            
            # Detect dips
            dips = self.detect_performance_dips(player_data, metric)
            
            if len(dips) >= 3:
                # Analyze periodicity
                periodicity = self.analyze_dip_periodicity(dips, player_data)
                
                # Get magnitudes
                magnitudes = [d['magnitude'] for d in dips]
                
                # Classify pattern
                classification, confidence = self.classify_dip_pattern(periodicity, magnitudes)
                
                # Store results
                results['metrics'][metric] = {
                    'dip_count': len(dips),
                    'avg_magnitude': np.mean(magnitudes),
                    'classification': classification,
                    'confidence': confidence,
                    'optimal_cycle_length': optimal_length,
                    'periodicity_score': periodicity['periodicity_score'] if periodicity else 0,
                    'dip_dates': [d['date'].strftime('%Y-%m-%d') for d in dips[-5:]],  # Last 5 dips
                    'intervals': periodicity['intervals'][-4:] if periodicity else []  # Last 4 intervals
                }
            else:
                results['metrics'][metric] = {
                    'dip_count': len(dips),
                    'classification': 'Insufficient Data',
                    'confidence': 0
                }
        
        # Calculate overall consistency score
        consistency_scores = []
        for metric_data in results['metrics'].values():
            if metric_data.get('periodicity_score'):
                consistency_scores.append(metric_data['periodicity_score'])
        
        results['cycle_consistency_score'] = np.mean(consistency_scores) if consistency_scores else 0
        
        return results
    
    def generate_predictions(self, player_results):
        """Generate future dip predictions based on detected patterns"""
        predictions = []
        
        for metric, data in player_results['metrics'].items():
            if data['classification'] == 'Possible Cycle Dip' and data['dip_dates']:
                # Get last dip date
                last_dip = datetime.strptime(data['dip_dates'][-1], '%Y-%m-%d')
                optimal_cycle = data['optimal_cycle_length']
                
                # Predict next 3 potential dip dates
                next_dips = []
                for i in range(1, 4):
                    next_dip = last_dip + timedelta(days=optimal_cycle * i)
                    next_dips.append(next_dip.strftime('%Y-%m-%d'))
                
                predictions.append({
                    'metric': metric,
                    'next_potential_dips': next_dips,
                    'confidence': data['confidence']
                })
        
        return predictions
    
    def analyze_all_players(self):
        """Analyze all players in the dataset"""
        players = self.df['PLAYER_NAME'].unique()
        all_results = []
        
        print(f"Analyzing {len(players)} players...")
        
        for i, player in enumerate(players):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(players)} players analyzed")
            
            result = self.analyze_player(player)
            if result and result['cycle_consistency_score'] > 0:
                all_results.append(result)
        
        # Sort by consistency score
        all_results.sort(key=lambda x: x['cycle_consistency_score'], reverse=True)
        
        return all_results
    
    def export_results(self, results, output_file='cycle_analysis_results.csv'):
        """Export results to CSV format"""
        rows = []
        
        for player_result in results:
            base_row = {
                'player_name': player_result['player_name'],
                'total_games': player_result['total_games'],
                'date_range': player_result['date_range'],
                'cycle_consistency_score': round(player_result['cycle_consistency_score'], 3)
            }
            
            # Add predictions
            predictions = self.generate_predictions(player_result)
            
            # Create a row for each metric
            for metric in self.target_metrics:
                if metric in player_result['metrics']:
                    metric_data = player_result['metrics'][metric]
                    row = base_row.copy()
                    row.update({
                        'metric': metric,
                        'classification': metric_data['classification'],
                        'confidence': round(metric_data.get('confidence', 0), 3),
                        'dip_count': metric_data['dip_count'],
                        'avg_drop_magnitude': round(metric_data.get('avg_magnitude', 0), 3),
                        'optimal_cycle_days': metric_data.get('optimal_cycle_length', self.cycle_length),
                        'recent_dip_dates': ', '.join(metric_data.get('dip_dates', [])[-3:]),
                        'recent_intervals': ', '.join(map(str, metric_data.get('intervals', [])[-3:]))
                    })
                    
                    # Add predictions for this metric
                    metric_predictions = [p for p in predictions if p['metric'] == metric]
                    if metric_predictions:
                        pred = metric_predictions[0]
                        row['next_potential_dips'] = ', '.join(pred['next_potential_dips'][:2])
                    
                    rows.append(row)
        
        # Convert to DataFrame and save
        results_df = pd.DataFrame(rows)
        results_df.to_csv(output_file, index=False)
        print(f"\nResults exported to {output_file}")
        
        return results_df
    
    def get_top_pattern_players(self, results, min_score=0.6, max_players=20):
        """Get players with strongest cyclical patterns"""
        top_players = []
        
        for result in results:
            if result['cycle_consistency_score'] >= min_score:
                # Find best metric for this player
                best_metric = None
                best_confidence = 0
                
                for metric, data in result['metrics'].items():
                    if data.get('confidence', 0) > best_confidence:
                        best_confidence = data['confidence']
                        best_metric = metric
                
                if best_metric:
                    top_players.append({
                        'player': result['player_name'],
                        'consistency_score': result['cycle_consistency_score'],
                        'best_metric': best_metric,
                        'classification': result['metrics'][best_metric]['classification'],
                        'confidence': best_confidence
                    })
        
        # Sort and limit
        top_players.sort(key=lambda x: x['consistency_score'], reverse=True)
        return top_players[:max_players]


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WNBA Cycle-Aware Pattern Detection')
    parser.add_argument('input_file', help='Path to combined game logs CSV')
    parser.add_argument('--output', default='cycle_analysis_results.csv', help='Output CSV filename')
    parser.add_argument('--cycle-length', type=int, default=28, help='Default cycle length in days')
    parser.add_argument('--min-games', type=int, default=30, help='Minimum games required for analysis')
    parser.add_argument('--top-players', type=int, default=20, help='Number of top pattern players to display')
    
    args = parser.parse_args()
    
    # Initialize detector
    print(f"Initializing Cycle-Aware Pattern Detector...")
    print(f"Default cycle length: {args.cycle_length} days")
    print(f"Minimum games threshold: {args.min_games}")
    
    detector = CycleAwarePatternDetector(
        cycle_length=args.cycle_length,
        min_games=args.min_games
    )
    
    # Load data
    print(f"\nLoading data from {args.input_file}...")
    detector.load_data(args.input_file)
    print(f"Loaded {len(detector.df)} game records")
    
    # Analyze all players
    print("\nAnalyzing performance patterns...")
    results = detector.analyze_all_players()
    
    # Export results
    detector.export_results(results, args.output)
    
    # Display top pattern players
    print("\n" + "="*60)
    print("TOP PLAYERS WITH CYCLICAL PATTERNS")
    print("="*60)
    
    top_players = detector.get_top_pattern_players(results, max_players=args.top_players)
    
    for i, player in enumerate(top_players, 1):
        print(f"\n{i}. {player['player']}")
        print(f"   Consistency Score: {player['consistency_score']:.3f}")
        print(f"   Best Metric: {player['best_metric']}")
        print(f"   Pattern Type: {player['classification']}")
        print(f"   Confidence: {player['confidence']:.3f}")
    
    print(f"\n[SUCCESS] Analysis complete! Results saved to {args.output}")
    print(f"   Total players analyzed: {len(results)}")
    print(f"   Players with patterns: {len([r for r in results if r['cycle_consistency_score'] > 0.5])}")


if __name__ == "__main__":
    main()