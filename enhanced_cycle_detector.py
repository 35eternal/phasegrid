#!/usr/bin/env python3
"""
Enhanced Cycle-Aware Pattern Detector with detailed diagnostics
"""

import pandas as pd
import numpy as np
from scipy import stats, signal
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class EnhancedCycleDetector:
    """Enhanced detector with more flexible pattern recognition"""
    
    def __init__(self, cycle_length=28, cycle_range=(21, 35), min_games=20):
        self.cycle_length = cycle_length
        self.cycle_range = cycle_range
        self.min_games = min_games
        self.target_metrics = ['PTS', 'REB', 'AST']
        
    def load_data(self, filepath):
        """Load and prepare game log data"""
        self.df = pd.read_csv(filepath)
        self.df['GAME_DATE'] = pd.to_datetime(self.df['GAME_DATE'], format='mixed')
        self.df = self.df.sort_values(['PLAYER_NAME', 'GAME_DATE'])
        
        # Add days since first game for each player
        for player in self.df['PLAYER_NAME'].unique():
            player_mask = self.df['PLAYER_NAME'] == player
            first_game = self.df.loc[player_mask, 'GAME_DATE'].min()
            self.df.loc[player_mask, 'DAYS_SINCE_START'] = (self.df.loc[player_mask, 'GAME_DATE'] - first_game).dt.days
        
        return self.df
    
    def calculate_performance_baseline(self, player_data, metric):
        """Calculate adaptive rolling baseline"""
        # Use shorter window for better sensitivity
        baseline = player_data[metric].rolling(window=7, min_periods=3).mean()
        
        # Fill initial values with early season average
        early_avg = player_data[metric].iloc[:5].mean()
        baseline = baseline.fillna(early_avg)
        
        return baseline
    
    def detect_performance_variations(self, player_data, metric):
        """Detect all significant performance variations"""
        baseline = self.calculate_performance_baseline(player_data, metric)
        
        # Calculate z-scores for better sensitivity
        std_dev = player_data[metric].rolling(window=7, min_periods=3).std().fillna(1)
        z_scores = (player_data[metric] - baseline) / std_dev
        
        # Identify significant dips (z-score < -1)
        dips = []
        peaks = []
        
        for idx, (date, z_score, actual, expected) in enumerate(zip(
            player_data['GAME_DATE'], z_scores, player_data[metric], baseline)):
            
            if z_score < -1 and not pd.isna(z_score):
                dips.append({
                    'date': date,
                    'days_since_start': player_data['DAYS_SINCE_START'].iloc[idx],
                    'z_score': z_score,
                    'actual': actual,
                    'expected': expected,
                    'drop_pct': (expected - actual) / expected if expected > 0 else 0
                })
            elif z_score > 1 and not pd.isna(z_score):
                peaks.append({
                    'date': date,
                    'days_since_start': player_data['DAYS_SINCE_START'].iloc[idx],
                    'z_score': z_score,
                    'actual': actual,
                    'expected': expected
                })
        
        return dips, peaks
    
    def analyze_cycle_patterns(self, dips, player_data):
        """Analyze for cyclical patterns with multiple detection methods"""
        if len(dips) < 3:
            return None
        
        # Method 1: Day-based intervals
        dip_days = [d['days_since_start'] for d in dips]
        intervals = [dip_days[i+1] - dip_days[i] for i in range(len(dip_days)-1)]
        
        # Method 2: Fourier analysis for periodicity
        if len(player_data) > 20:
            try:
                from scipy.fft import fft, fftfreq
                values = player_data[self.target_metrics[0]].fillna(0).values
                fft_vals = fft(values)
                frequencies = fftfreq(len(values))
                
                # Find dominant frequency
                power = np.abs(fft_vals[:len(values)//2])
                dominant_freq_idx = np.argmax(power[1:]) + 1
                dominant_period = 1 / frequencies[dominant_freq_idx] if frequencies[dominant_freq_idx] != 0 else 0
            except:
                dominant_period = 0
        else:
            dominant_period = 0
        
        # Calculate pattern scores
        results = {
            'intervals': intervals,
            'mean_interval': np.mean(intervals) if intervals else 0,
            'std_interval': np.std(intervals) if intervals else 0,
            'median_interval': np.median(intervals) if intervals else 0,
            'fourier_period': abs(dominant_period),
            'cycle_matches': 0,
            'consistency_score': 0
        }
        
        # Count intervals near expected cycle
        for interval in intervals:
            if self.cycle_range[0] <= interval <= self.cycle_range[1]:
                results['cycle_matches'] += 1
        
        # Calculate multiple scoring metrics
        if len(intervals) > 0:
            # Interval consistency
            cv = results['std_interval'] / results['mean_interval'] if results['mean_interval'] > 0 else 1
            interval_score = 1 / (1 + cv)  # Lower CV = higher score
            
            # Cycle match ratio
            match_ratio = results['cycle_matches'] / len(intervals)
            
            # Proximity to expected cycle
            proximity_score = 1 - abs(results['mean_interval'] - self.cycle_length) / self.cycle_length
            proximity_score = max(0, proximity_score)
            
            # Combined score
            results['consistency_score'] = (interval_score + match_ratio + proximity_score) / 3
        
        return results
    
    def classify_pattern(self, pattern_results, dips):
        """More nuanced pattern classification"""
        if pattern_results is None or len(dips) < 3:
            return "Insufficient Data", 0.0
        
        score = pattern_results['consistency_score']
        mean_interval = pattern_results['mean_interval']
        cv = pattern_results['std_interval'] / pattern_results['mean_interval'] if pattern_results['mean_interval'] > 0 else 1
        
        # Multi-factor classification
        if score > 0.6 and self.cycle_range[0] <= mean_interval <= self.cycle_range[1]:
            return "Strong Cycle Pattern", score
        elif score > 0.4 and cv < 0.5:
            return "Moderate Cycle Pattern", score
        elif score > 0.3:
            return "Weak Cycle Pattern", score
        elif cv > 0.7:
            return "Irregular Pattern", 1 - cv
        else:
            return "No Clear Pattern", score
    
    def analyze_player(self, player_name):
        """Comprehensive player analysis with diagnostics"""
        player_data = self.df[self.df['PLAYER_NAME'] == player_name].copy()
        
        if len(player_data) < self.min_games:
            return None
        
        results = {
            'player_name': player_name,
            'total_games': len(player_data),
            'date_range': f"{player_data['GAME_DATE'].min().date()} to {player_data['GAME_DATE'].max().date()}",
            'season_length_days': (player_data['GAME_DATE'].max() - player_data['GAME_DATE'].min()).days,
            'metrics': {}
        }
        
        # Analyze each metric
        all_scores = []
        for metric in self.target_metrics:
            if metric not in player_data.columns:
                continue
            
            # Detect variations
            dips, peaks = self.detect_performance_variations(player_data, metric)
            
            # Analyze patterns
            pattern_results = self.analyze_cycle_patterns(dips, player_data)
            
            # Classify
            if pattern_results:
                classification, confidence = self.classify_pattern(pattern_results, dips)
                
                results['metrics'][metric] = {
                    'dip_count': len(dips),
                    'peak_count': len(peaks),
                    'avg_drop': np.mean([d['drop_pct'] for d in dips]) if dips else 0,
                    'classification': classification,
                    'confidence': confidence,
                    'mean_interval': pattern_results['mean_interval'],
                    'interval_std': pattern_results['std_interval'],
                    'pattern_score': pattern_results['consistency_score'],
                    'recent_dips': [d['date'].strftime('%Y-%m-%d') for d in dips[-5:]],
                    'intervals': pattern_results['intervals'][-5:] if pattern_results else []
                }
                
                all_scores.append(pattern_results['consistency_score'])
            else:
                results['metrics'][metric] = {
                    'dip_count': len(dips),
                    'classification': 'Insufficient Data',
                    'confidence': 0
                }
        
        # Overall consistency score
        results['overall_pattern_score'] = np.mean(all_scores) if all_scores else 0
        
        return results
    
    def analyze_all_players(self, verbose=True):
        """Analyze all players with progress tracking"""
        players = self.df['PLAYER_NAME'].unique()
        all_results = []
        pattern_counts = {'Strong': 0, 'Moderate': 0, 'Weak': 0, 'None': 0}
        
        print(f"\nAnalyzing {len(players)} players for cyclical patterns...")
        print(f"Cycle range: {self.cycle_range[0]}-{self.cycle_range[1]} days")
        print(f"Minimum games: {self.min_games}\n")
        
        for i, player in enumerate(players):
            if verbose and i % 20 == 0:
                print(f"Progress: {i}/{len(players)} players analyzed")
            
            result = self.analyze_player(player)
            if result:
                all_results.append(result)
                
                # Track pattern types
                for metric_data in result['metrics'].values():
                    if 'Strong' in metric_data.get('classification', ''):
                        pattern_counts['Strong'] += 1
                    elif 'Moderate' in metric_data.get('classification', ''):
                        pattern_counts['Moderate'] += 1
                    elif 'Weak' in metric_data.get('classification', ''):
                        pattern_counts['Weak'] += 1
        
        # Sort by overall pattern score
        all_results.sort(key=lambda x: x['overall_pattern_score'], reverse=True)
        
        print(f"\nPattern Summary:")
        print(f"  Strong patterns: {pattern_counts['Strong']}")
        print(f"  Moderate patterns: {pattern_counts['Moderate']}")
        print(f"  Weak patterns: {pattern_counts['Weak']}")
        
        return all_results
    
    def export_detailed_results(self, results, output_file='enhanced_cycle_results.csv'):
        """Export detailed results with all metrics"""
        rows = []
        
        for player_result in results:
            for metric, metric_data in player_result['metrics'].items():
                row = {
                    'player_name': player_result['player_name'],
                    'total_games': player_result['total_games'],
                    'season_days': player_result['season_length_days'],
                    'overall_score': round(player_result['overall_pattern_score'], 3),
                    'metric': metric,
                    'classification': metric_data['classification'],
                    'pattern_score': round(metric_data.get('pattern_score', 0), 3),
                    'dip_count': metric_data['dip_count'],
                    'avg_drop_pct': round(metric_data.get('avg_drop', 0) * 100, 1),
                    'mean_interval': round(metric_data.get('mean_interval', 0), 1),
                    'interval_std': round(metric_data.get('interval_std', 0), 1),
                    'recent_dips': ', '.join(metric_data.get('recent_dips', [])[-3:])
                }
                rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False)
        print(f"\nDetailed results exported to {output_file}")
        
        # Also export top patterns
        top_patterns = df[df['classification'].str.contains('Pattern')].sort_values('pattern_score', ascending=False).head(20)
        if len(top_patterns) > 0:
            top_file = output_file.replace('.csv', '_top_patterns.csv')
            top_patterns.to_csv(top_file, index=False)
            print(f"Top patterns exported to {top_file}")
        
        return df


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced WNBA Cycle Detection')
    parser.add_argument('input_file', help='Path to game logs CSV')
    parser.add_argument('--output', default='enhanced_cycle_results.csv', help='Output filename')
    parser.add_argument('--cycle-length', type=int, default=28, help='Expected cycle length')
    parser.add_argument('--cycle-range', type=str, default='21,35', help='Cycle range (min,max)')
    parser.add_argument('--min-games', type=int, default=20, help='Minimum games for analysis')
    
    args = parser.parse_args()
    
    # Parse cycle range
    cycle_range = tuple(map(int, args.cycle_range.split(',')))
    
    # Initialize detector
    detector = EnhancedCycleDetector(
        cycle_length=args.cycle_length,
        cycle_range=cycle_range,
        min_games=args.min_games
    )
    
    # Load and analyze
    detector.load_data(args.input_file)
    results = detector.analyze_all_players()
    
    # Export results
    df = detector.export_detailed_results(results, args.output)
    
    # Display top players
    print("\n" + "="*60)
    print("TOP PLAYERS WITH CYCLICAL PATTERNS")
    print("="*60)
    
    top_players = [r for r in results if r['overall_pattern_score'] > 0.3][:15]
    
    for i, player in enumerate(top_players, 1):
        print(f"\n{i}. {player['player_name']} (Score: {player['overall_pattern_score']:.3f})")
        for metric, data in player['metrics'].items():
            if 'Pattern' in data.get('classification', ''):
                print(f"   {metric}: {data['classification']} (interval: {data.get('mean_interval', 0):.1f} days)")


if __name__ == "__main__":
    main()
