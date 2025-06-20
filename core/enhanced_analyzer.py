import pandas as pd

def load_historical_performance():
    try:
        df = pd.read_csv('data/wnba_combined_gamelogs.csv')
        print(f'📊 Loaded historical data: {len(df)} games')
        return df
    except:
        return None

def get_player_averages(historical_df, player_name):
    if historical_df is None:
        return None
    
    # Find player in historical data using PLAYER_NAME column
    player_data = historical_df[
        historical_df['PLAYER_NAME'].str.contains(player_name, case=False, na=False)
    ]
    
    if not player_data.empty:
        print(f'  📈 Found {len(player_data)} games for {player_name}')
        return {
            'Points': player_data['PTS'].mean(),
            'Assists': player_data['AST'].mean(), 
            'Rebounds': player_data['REB'].mean(),
            '3-PT Made': player_data['FG3M'].mean(),
            'Steals': player_data['STL'].mean(),
            'Blocks': player_data['BLK'].mean(),
        }
    else:
        print(f'  ⚠️ No historical data found for {player_name}')
        return None

def analyze_props_with_real_data():
    print('🎯 ENHANCED ANALYSIS WITH REAL PLAYER DATA\\n')
    
    props_df = pd.read_csv('data/wnba_prizepicks_props.csv')
    historical_df = load_historical_performance()
    
    print(f'📋 Analyzing {len(props_df)} props...\\n')
    
    edges = []
    
    for _, prop in props_df.iterrows():
        player = prop['player_name']
        stat = prop['stat_type'] 
        line = prop['line_score']
        
        if pd.isna(player) or pd.isna(stat) or pd.isna(line):
            continue
            
        print(f'🔍 {player} - {stat} (Line: {line})')
        
        # Get real player averages
        player_avgs = get_player_averages(historical_df, player)
        
        if player_avgs and stat in player_avgs:
            expected = player_avgs[stat]
            if pd.notna(expected) and expected > 0:
                edge = expected - line
                
                print(f'  📊 Real 2024 average: {expected:.1f}')
                print(f'  📈 Edge: {edge:+.1f} ({(edge/line*100):+.1f}%)')
                
                if abs(edge) >= 1.5:
                    rec = 'OVER' if edge > 0 else 'UNDER'
                    conf = 'HIGH' if abs(edge) >= 2.5 else 'MEDIUM'
                    print(f'  🎯 STRONG EDGE: {rec} {line} ({conf} confidence - REAL DATA)')
                    edges.append({
                        'player': player, 'stat': stat, 'line': line, 
                        'real_avg': expected, 'edge': edge, 'rec': rec, 
                        'confidence': conf, 'source': 'real_data'
                    })
                else:
                    print(f'  ✅ No significant edge')
                print()
                continue
        
        # Fallback to league averages if no real data
        league_avgs = {
            'Points': 11.5, 'Assists': 3.1, 'Rebounds': 6.2, 
            '3-PT Made': 1.3, 'Steals': 1.0, 'Blocks': 0.7
        }
        
        if stat in league_avgs:
            expected = league_avgs[stat]
            edge = expected - line
            print(f'  📊 League baseline: {expected:.1f}')
            print(f'  📈 Edge: {edge:+.1f} (baseline estimate)')
            
            if abs(edge) >= 2.0:  # Higher threshold for baseline estimates
                rec = 'OVER' if edge > 0 else 'UNDER'
                print(f'  💡 BASELINE EDGE: {rec} {line}')
                edges.append({
                    'player': player, 'stat': stat, 'line': line,
                    'real_avg': expected, 'edge': edge, 'rec': rec,
                    'confidence': 'LOW', 'source': 'baseline'
                })
            else:
                print(f'  ✅ No significant baseline edge')
        else:
            print(f'  ⚠️ No data available for {stat}')
        
        print()
    
    # Results summary
    print(f'🎯 ENHANCED ANALYSIS COMPLETE!')
    print(f'📊 Total edges found: {len(edges)}')
    
    real_data_edges = [e for e in edges if e['source'] == 'real_data']
    baseline_edges = [e for e in edges if e['source'] == 'baseline']
    
    print(f'🔥 Real data edges: {len(real_data_edges)}')
    print(f'💡 Baseline edges: {len(baseline_edges)}')
    
    if edges:
        print(f'\\n🎯 TOP RECOMMENDED BETS:')
        
        # Sort by edge magnitude
        sorted_edges = sorted(edges, key=lambda x: abs(x['edge']), reverse=True)
        
        for edge in sorted_edges[:10]:  # Top 10 edges
            source_emoji = '🔥' if edge['source'] == 'real_data' else '💡'
            conf_emoji = '🎯' if edge['confidence'] == 'HIGH' else '⚡' if edge['confidence'] == 'MEDIUM' else '💭'
            print(f'  {source_emoji}{conf_emoji} {edge["rec"]} {edge["line"]} - {edge["player"]} {edge["stat"]}')
            print(f'      Real Avg: {edge["real_avg"]:.1f}, Edge: {edge["edge"]:+.1f} ({edge["source"]})')
        
        # Save detailed results
        edges_df = pd.DataFrame(edges)
        edges_df.to_csv('data/enhanced_betting_edges.csv', index=False)
        print(f'\\n💾 Enhanced results saved to: data/enhanced_betting_edges.csv')
    else:
        print(f'\\n🔍 No significant edges found')
    
    return edges

if __name__ == '__main__':
    edges = analyze_props_with_real_data()
