import pandas as pd
import numpy as np
from datetime import datetime

def analyze_props():
    """Analyze props data"""
    df = pd.read_csv("data/processed/merged_props_with_gamelogs.csv")
    df = df.dropna(subset=['stat_type', 'line_score', 'PTS', 'AST', 'TRB'])
    
    # Create rolling averages
    df['rolling_5_PTS'] = df.groupby('PLAYER_NAME')['PTS'].rolling(5, min_periods=1).mean().reset_index(0, drop=True)
    df['rolling_5_AST'] = df.groupby('PLAYER_NAME')['AST'].rolling(5, min_periods=1).mean().reset_index(0, drop=True)
    df['rolling_5_TRB'] = df.groupby('PLAYER_NAME')['TRB'].rolling(5, min_periods=1).mean().reset_index(0, drop=True)
    
    # Calculate edges
    df['edge_PTS'] = df['rolling_5_PTS'] - df['line_score']
    df['edge_AST'] = df['rolling_5_AST'] - df['line_score'] 
    df['edge_TRB'] = df['rolling_5_TRB'] - df['line_score']
    
    # Find high edge opportunities
    high_edges = df[abs(df['edge_PTS']) > 3].sort_values('edge_PTS', ascending=False)
    
    print("=== HIGH EDGE OPPORTUNITIES ===")
    print(high_edges[['PLAYER_NAME', 'stat_type', 'line_score', 'rolling_5_PTS', 'edge_PTS']].head(10))
    
    return df

def get_player_analysis(player_name):
    """Get detailed analysis for a specific player"""
    df = analyze_props()
    player_data = df[df['PLAYER_NAME'] == player_name]
    
    if len(player_data) == 0:
        return None
        
    return {
        'player': player_name,
        'avg_pts': player_data['PTS'].mean(),
        'recent_5_avg': player_data['rolling_5_PTS'].iloc[-1] if len(player_data) > 0 else None,
        'total_games': len(player_data)
    }

if __name__ == "__main__":
    analyze_props()