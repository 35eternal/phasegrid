#!/usr/bin/env python3
"""
Simple analyzer that works with available data and provides betting edges
"""
import pandas as pd
import numpy as np
from datetime import datetime

def load_props_data():
    """Load the current PrizePicks props data"""
    try:
        df = pd.read_csv("data/wnba_prizepicks_props.csv")
        print(f"📊 Loaded {len(df)} props from PrizePicks")
        return df
    except Exception as e:
        print(f"❌ Error loading props data: {e}")
        return None

def load_historical_data():
    """Load any available historical WNBA data"""
    historical_files = [
        "data/wnba_2024_gamelogs.csv",
        "data/unified_gamelogs_with_features.csv", 
        "data/unified_gamelogs_boosted.csv",
        "data/unified_gamelogs.csv"
    ]
    
    for file_path in historical_files:
        try:
            df = pd.read_csv(file_path)
            print(f"📊 Loaded historical data: {file_path} ({len(df)} rows)")
            return df, file_path
        except Exception:
            continue
    
    print("⚠️ No historical data files found")
    return None, None

def get_league_baselines():
    """Get typical WNBA performance baselines for common stats"""
    
    # These are approximate WNBA averages based on recent seasons
    baselines = {
        'Points': {
            'guard_avg': 12.5,
            'forward_avg': 11.8,
            'center_avg': 10.2,
            'league_avg': 11.5
        },
        'Assists': {
            'guard_avg': 4.2,
            'forward_avg': 2.8,
            'center_avg': 1.9,
            'league_avg': 3.1
        },
        'Rebounds': {
            'guard_avg': 4.8,
            'forward_avg': 7.2,
            'center_avg': 8.1,
            'league_avg': 6.2
        },
        '3-PT Made': {
            'guard_avg': 1.8,
            'forward_avg': 1.2,
            'center_avg': 0.4,
            'league_avg': 1.3
        },
        'Steals': {
            'guard_avg': 1.3,
            'forward_avg': 1.0,
            'center_avg': 0.7,
            'league_avg': 1.0
        },
        'Blocks': {
            'guard_avg': 0.3,
            'forward_avg': 0.8,
            'center_avg': 1.4,
            'league_avg': 0.7
        }
    }
    
    return baselines

def estimate_player_performance(player_name, stat_type, historical_df=None):
    """Estimate player performance using available data"""
    
    if historical_df is not None:
        # Try to find this player in historical data
        player_data = historical_df[
            historical_df['Player'].str.contains(player_name, case=False, na=False) |
            historical_df.get('player_name', pd.Series()).str.contains(player_name, case=False, na=False)
        ]
        
        if not player_data.empty:
            # Map stat types to column names
            stat_mapping = {
                'Points': ['PTS', 'pts', 'Points'],
                'Assists': ['AST', 'ast', 'Assists'], 
                'Rebounds': ['TRB', 'trb', 'REB', 'reb', 'Rebounds'],
                '3-PT Made': ['3P', '3PA', 'fg3', 'FG3'],
                'Steals': ['STL', 'stl', 'Steals'],
                'Blocks': ['BLK', 'blk', 'Blocks']
            }
            
            possible_cols = stat_mapping.get(stat_type, [])
            
            for col in possible_cols:
                if col in player_data.columns:
                    avg_performance = player_data[col].mean()
                    if not pd.isna(avg_performance):
                        print(f"  📊 {player_name} {stat_type}: {avg_performance:.1f} (from historical data)")
                        return avg_performance, 'historical'
    
    # Fall back to league baselines
    baselines = get_league_baselines()
    
    if stat_type in baselines:
        # Use league average as baseline
        league_avg = baselines[stat_type]['league_avg']
        print(f"  📊 {player_name} {stat_type}: {league_avg:.1f} (league baseline)")
        return league_avg, 'baseline'
    
    return None, 'unknown'

def analyze_props():
    """Analyze all current props for betting edges"""
    
    print("🎯 ANALYZING PRIZEPICKS PROPS FOR EDGES\n")
    
    # Load data
    props_df = load_props_data()
    if props_df is None:
        return
    
    historical_df, hist_file = load_historical_data()
    
    # Get unique active props
    active_props = props_df[
        (props_df['player_name'].notna()) & 
        (props_df['stat_type'].notna()) & 
        (props_df['line_score'].notna())
    ].drop_duplicates(['player_name', 'stat_type', 'line_score'])
    
    print(f"📋 Analyzing {len(active_props)} unique props...\n")
    
    edges_found = []
    
    for _, prop in active_props.iterrows():
        player_name = prop['player_name']
        stat_type = prop['stat_type']
        line_score = float(prop['line_score'])
        
        print(f"🔍 {player_name} - {stat_type} (Line: {line_score})")
        
        # Estimate player performance
        estimated_performance, data_source = estimate_player_performance(
            player_name, stat_type, historical_df
        )
        
        if estimated_performance is None:
            print(f"  ⚠️ No performance data available")
            continue
        
        # Calculate edge
        edge = estimated_performance - line_score
        edge_percentage = (edge / line_score) * 100 if line_score != 0 else 0
        
        # Determine if this is a significant edge
        if abs(edge) >= 1.5:  # Lower threshold since we're using estimates
            recommendation = "OVER" if edge > 0 else "UNDER"
            confidence = "HIGH" if abs(edge) >= 2.5 else "MEDIUM"
            
            if data_source == 'baseline':
                confidence = "LOW"  # Lower confidence for baseline estimates
            
            edges_found.append({
                'player': player_name,
                'stat': stat_type,
                'line': line_score,
                'estimated_performance': estimated_performance,
                'edge': edge,
                'edge_pct': edge_percentage,
                'recommendation': recommendation,
                'confidence': confidence,
                'data_source': data_source
            })
            
            print(f"  🎯 EDGE FOUND!")
            print(f"     Estimated Performance: {estimated_performance:.1f}")
            print(f"     Edge: {edge:+.1f} ({edge_percentage:+.1f}%)")
            print(f"     Recommendation: {recommendation} {line_score}")
            print(f"     Confidence: {confidence} ({data_source})")
            
        else:
            print(f"     Estimated: {estimated_performance:.1f}, Edge: {edge:+.1f} (no significant edge)")
        
        print()
    
    # Summary
    print(f"📊 ANALYSIS SUMMARY:")
    print(f"  Props analyzed: {len(active_props)}")
    print(f"  Edges found: {len(edges_found)}")
    
    if edges_found:
        print(f"\n🎯 RECOMMENDED BETS:")
        for edge in edges_found:
            confidence_emoji = "🔥" if edge['confidence'] == "HIGH" else "⚡" if edge['confidence'] == "MEDIUM" else "💡"
            print(f"  {confidence_emoji} {edge['recommendation']} {edge['line']} - {edge['player']} {edge['stat']}")
            print(f"      Edge: {edge['edge']:+.1f} ({edge['confidence']} confidence)")
        
        # Save edges
        edges_df = pd.DataFrame(edges_found)
        edges_df.to_csv("data/betting_edges.csv", index=False)
        print(f"\n💾 Edges saved to: data/betting_edges.csv")
        
    else:
        print(f"\n🔍 No significant edges found in current props")
    
    return edges_found

def quick_player_analysis(player_name):
    """Quick analysis for a specific player"""
    
    print(f"🎯 Quick Analysis: {player_name}\n")
    
    props_df = load_props_data()
    if props_df is None:
        return
    
    historical_df, _ = load_historical_data()
    
    # Get props for this player
    player_props = props_df[props_df['player_name'] == player_name]
    
    if player_props.empty:
        print(f"❌ No props found for {player_name}")
        return
    
    for _, prop in player_props.iterrows():
        stat_type = prop['stat_type']
        line_score = prop['line_score']
        
        if pd.isna(stat_type) or pd.isna(line_score):
            continue
        
        estimated_perf, source = estimate_player_performance(player_name, stat_type, historical_df)
        
        if estimated_perf:
            edge = estimated_perf - float(line_score)
            print(f"📊 {stat_type}: {estimated_perf:.1f} estimated vs {line_score} line = {edge:+.1f} edge ({source})")
        else:
            print(f"⚠️ {stat_type}: No performance data available")

def show_available_data():
    """Show what data is available for analysis"""
    
    print("📋 Available Data Summary:\n")
    
    # Check props data
    props_df = load_props_data()
    if props_df is not None:
        unique_players = props_df['player_name'].dropna().nunique()
        unique_stats = props_df['stat_type'].dropna().nunique() 
        print(f"✅ Current Props: {len(props_df)} props, {unique_players} players, {unique_stats} stat types")
        
        print(f"   Players: {sorted(props_df['player_name'].dropna().unique())}")
        print(f"   Stats: {sorted(props_df['stat_type'].dropna().unique())}")
    
    # Check historical data
    historical_df, hist_file = load_historical_data()
    if historical_df is not None:
        print(f"✅ Historical Data: {hist_file}")
        print(f"   Columns: {list(historical_df.columns)}")
    else:
        print(f"⚠️ No historical data available - using league baselines")

if __name__ == "__main__":
    print("🏀 Simple WNBA Props Analyzer\n")
    
    show_available_data()
    print()
    
    edges = analyze_props()