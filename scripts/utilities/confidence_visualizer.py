#!/usr/bin/env python3
"""
Confidence Visualizer - Creates interactive Plotly visualizations showing
bet count progression and confidence evolution over time for each phase.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import os

class ConfidenceVisualizer:
    def __init__(self):
        self.phase_colors = {
            'luteal': '#9b59b6',      # Purple
            'menstrual': '#e74c3c',   # Red
            'follicular': '#3498db',   # Blue
            'ovulatory': '#2ecc71'     # Green
        }
        self.confidence_colors = {
            'HIGH': '#27ae60',
            'MEDIUM': '#f39c12',
            'LOW': '#e74c3c',
            'INSUFFICIENT': '#95a5a6'
        }
    
    def load_phase_data(self, filepath='phase_results_tracker.csv'):
        """Load and prepare phase results data."""
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return None
        
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    def create_bet_count_timeline(self, df):
        """Create timeline showing cumulative bet count by phase."""
        fig = go.Figure()
        
        for phase in ['luteal', 'menstrual', 'follicular', 'ovulatory']:
            phase_data = df[df['phase'] == phase].copy()
            phase_data = phase_data.sort_values('date')
            phase_data['cumulative_count'] = range(1, len(phase_data) + 1)
            
            fig.add_trace(go.Scatter(
                x=phase_data['date'],
                y=phase_data['cumulative_count'],
                mode='lines+markers',
                name=phase.capitalize(),
                line=dict(color=self.phase_colors[phase], width=3),
                marker=dict(size=6)
            ))
        
        # Add 20-bet threshold line
        fig.add_hline(
            y=20, 
            line_dash="dash", 
            line_color="red",
            annotation_text="Production Threshold (20 bets)"
        )
        
        fig.update_layout(
            title="Cumulative Bet Count by Phase",
            xaxis_title="Date",
            yaxis_title="Cumulative Bets",
            hovermode='x unified',
            height=500,
            template='plotly_white'
        )
        
        return fig
    
    def create_win_rate_evolution(self, df):
        """Create moving win rate chart for each phase."""
        fig = go.Figure()
        
        for phase in ['luteal', 'menstrual', 'follicular', 'ovulatory']:
            phase_data = df[df['phase'] == phase].copy()
            phase_data = phase_data.sort_values('date')
            
            # Calculate rolling win rate (last 10 bets)
            phase_data['win'] = (phase_data['actual_result'] == 'win').astype(int)
            phase_data['rolling_wr'] = phase_data['win'].rolling(
                window=10, min_periods=1
            ).mean()
            
            fig.add_trace(go.Scatter(
                x=phase_data['date'],
                y=phase_data['rolling_wr'],
                mode='lines',
                name=phase.capitalize(),
                line=dict(color=self.phase_colors[phase], width=2)
            ))
        
        # Add reference lines
        fig.add_hline(y=0.55, line_dash="dash", line_color="gray", 
                     annotation_text="Target WR (55%)")
        
        fig.update_layout(
            title="Rolling Win Rate by Phase (10-bet window)",
            xaxis_title="Date",
            yaxis_title="Win Rate",
            yaxis_tickformat='.0%',
            hovermode='x unified',
            height=500,
            template='plotly_white'
        )
        
        return fig
    
    def create_confidence_progression(self, df):
        """Create confidence score progression chart."""
        # Calculate confidence scores over time
        phases = ['luteal', 'menstrual', 'follicular', 'ovulatory']
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[p.capitalize() for p in phases],
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        positions = [(1,1), (1,2), (2,1), (2,2)]
        
        for idx, phase in enumerate(phases):
            row, col = positions[idx]
            phase_data = df[df['phase'] == phase].copy()
            phase_data = phase_data.sort_values('date')
            
            # Calculate cumulative metrics
            phase_data['cumulative_count'] = range(1, len(phase_data) + 1)
            phase_data['win'] = (phase_data['actual_result'] == 'win').astype(int)
            phase_data['cumulative_wins'] = phase_data['win'].cumsum()
            phase_data['cumulative_wr'] = phase_data['cumulative_wins'] / phase_data['cumulative_count']
            
            # Calculate confidence score
            phase_data['bet_score'] = phase_data['cumulative_count'].apply(
                lambda x: min(x / 30 * 50, 50)
            )
            phase_data['wr_score'] = phase_data['cumulative_wr'] * 50
            phase_data['confidence_score'] = phase_data['bet_score'] + phase_data['wr_score']
            
            # Determine confidence level
            phase_data['confidence_level'] = phase_data.apply(
                lambda x: 'HIGH' if x['cumulative_count'] >= 20 and x['cumulative_wr'] >= 0.65
                else 'MEDIUM' if x['cumulative_count'] >= 15 and x['cumulative_wr'] >= 0.55
                else 'LOW' if x['cumulative_count'] >= 10
                else 'INSUFFICIENT', axis=1
            )
            
            # Plot
            fig.add_trace(
                go.Scatter(
                    x=phase_data['date'],
                    y=phase_data['confidence_score'],
                    mode='lines+markers',
                    name=phase,
                    line=dict(color=self.phase_colors[phase], width=2),
                    showlegend=False
                ),
                row=row, col=col
            )
            
            # Add threshold lines
            fig.add_hline(y=75, line_dash="dash", line_color="green", 
                         row=row, col=col)
            fig.add_hline(y=50, line_dash="dash", line_color="orange", 
                         row=row, col=col)
        
        fig.update_yaxes(title_text="Confidence Score", range=[0, 100])
        fig.update_xaxes(title_text="Date")
        
        fig.update_layout(
            title="Confidence Score Progression by Phase",
            height=700,
            template='plotly_white'
        )
        
        return fig
    
    def create_phase_comparison_radar(self, df):
        """Create radar chart comparing phase performance metrics."""
        # Calculate current metrics for each phase
        metrics = []
        
        for phase in ['luteal', 'menstrual', 'follicular', 'ovulatory']:
            phase_data = df[df['phase'] == phase]
            
            if len(phase_data) > 0:
                wins = len(phase_data[phase_data['actual_result'] == 'win'])
                total = len(phase_data)
                win_rate = wins / total if total > 0 else 0
                
                # Normalize metrics to 0-100 scale
                metrics.append({
                    'phase': phase.capitalize(),
                    'Win Rate': win_rate * 100,
                    'Bet Count': min(total / 30 * 100, 100),
                    'Consistency': self._calculate_consistency(phase_data) * 100,
                    'Recent Form': self._calculate_recent_form(phase_data) * 100
                })
        
        # Create radar chart
        categories = ['Win Rate', 'Bet Count', 'Consistency', 'Recent Form']
        
        fig = go.Figure()
        
        for metric in metrics:
            fig.add_trace(go.Scatterpolar(
                r=[metric[cat] for cat in categories],
                theta=categories,
                fill='toself',
                name=metric['phase'],
                line=dict(color=self.phase_colors[metric['phase'].lower()])
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            title="Phase Performance Comparison",
            height=500
        )
        
        return fig
    
    def _calculate_consistency(self, phase_data):
        """Calculate consistency score (lower variance = higher consistency)."""
        if len(phase_data) < 5:
            return 0.5
        
        # Use rolling 5-bet win rate variance
        phase_data['win'] = (phase_data['actual_result'] == 'win').astype(int)
        rolling_wr = phase_data['win'].rolling(window=5).mean()
        variance = rolling_wr.var()
        
        # Convert to 0-1 score (lower variance = higher score)
        consistency = max(0, 1 - variance * 2)
        return consistency
    
    def _calculate_recent_form(self, phase_data, last_n=10):
        """Calculate recent form (last N bets win rate)."""
        if len(phase_data) == 0:
            return 0.5
        
        recent = phase_data.tail(last_n)
        wins = len(recent[recent['actual_result'] == 'win'])
        return wins / len(recent)
    
    def create_daily_performance_heatmap(self, df):
        """Create heatmap of daily performance by phase."""
        # Prepare data
        daily_perf = df.groupby(['date', 'phase']).agg({
            'actual_result': lambda x: (x == 'win').sum() / len(x)
        }).reset_index()
        
        # Pivot for heatmap
        heatmap_data = daily_perf.pivot(
            index='phase', 
            columns='date', 
            values='actual_result'
        )
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='RdYlGn',
            zmid=0.5,
            text=heatmap_data.values,
            texttemplate='%{text:.0%}',
            textfont={"size": 10},
            colorbar=dict(title="Win Rate")
        ))
        
        fig.update_layout(
            title="Daily Win Rate Heatmap by Phase",
            xaxis_title="Date",
            yaxis_title="Phase",
            height=400
        )
        
        return fig
    
    def save_all_visualizations(self, df, output_dir='output/visualizations'):
        """Generate and save all visualizations."""
        os.makedirs(output_dir, exist_ok=True)
        
        visualizations = {
            'bet_count_timeline': self.create_bet_count_timeline(df),
            'win_rate_evolution': self.create_win_rate_evolution(df),
            'confidence_progression': self.create_confidence_progression(df),
            'phase_comparison': self.create_phase_comparison_radar(df),
            'daily_heatmap': self.create_daily_performance_heatmap(df)
        }
        
        for name, fig in visualizations.items():
            # Save as HTML
            html_path = os.path.join(output_dir, f'{name}.html')
            fig.write_html(html_path)
            print(f"✅ Saved: {html_path}")
            
            # Save as static image (requires kaleido)
            try:
                img_path = os.path.join(output_dir, f'{name}.png')
                fig.write_image(img_path, width=1200, height=800)
                print(f"✅ Saved: {img_path}")
            except:
                print(f"⚠️  Could not save PNG for {name} (install kaleido)")
        
        return visualizations

def main():
    """Run confidence visualizer."""
    print("📊 Starting Confidence Visualizer...")
    
    visualizer = ConfidenceVisualizer()
    
    # Load data
    df = visualizer.load_phase_data()
    
    if df is None:
        print("❌ Cannot create visualizations without data")
        return
    
    print(f"✅ Loaded {len(df)} betting records")
    
    # Generate visualizations
    print("\n🎨 Generating visualizations...")
    visualizations = visualizer.save_all_visualizations(df)
    
    print(f"\n✅ Generated {len(visualizations)} visualizations")
    print("   View in: output/visualizations/")
    
    # Display summary
    print("\n📈 Current Phase Status:")
    for phase in ['luteal', 'menstrual', 'follicular', 'ovulatory']:
        phase_data = df[df['phase'] == phase]
        if len(phase_data) > 0:
            wins = len(phase_data[phase_data['actual_result'] == 'win'])
            wr = wins / len(phase_data)
            print(f"  {phase.capitalize()}: {len(phase_data)} bets, {wr:.1%} WR")

if __name__ == "__main__":
    main()