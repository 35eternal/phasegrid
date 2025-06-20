import pandas as pd

def analyze_props():
    print("🎯 ANALYZING PRIZEPICKS PROPS FOR EDGES")
    
    try:
        df = pd.read_csv("data/wnba_prizepicks_props.csv")
        print(f"📊 Loaded {len(df)} props from {df['player_name'].nunique()} players")
        
        # League averages for WNBA stats
        league_averages = {
            'Points': 11.5, 'Assists': 3.1, 'Rebounds': 6.2,
            '3-PT Made': 1.3, 'Steals': 1.0, 'Blocks': 0.7
        }
        
        print(f"\n🔍 Analyzing props...\n")
        edges = []
        
        for _, prop in df.iterrows():
            player = prop['player_name'] 
            stat = prop['stat_type']
            line = prop['line_score']
            
            if pd.isna(player) or pd.isna(stat) or pd.isna(line):
                continue
                
            if stat in league_averages:
                expected = league_averages[stat]
                edge = expected - line
                
                print(f"📊 {player} {stat}: Expected {expected:.1f} vs Line {line} = {edge:+.1f} edge")
                
                if abs(edge) >= 1.5:
                    recommendation = "OVER" if edge > 0 else "UNDER"
                    confidence = "HIGH" if abs(edge) >= 2.5 else "MEDIUM"
                    print(f"  🎯 EDGE FOUND: {recommendation} {line} ({confidence} confidence)")
                    edges.append({
                        'player': player, 'stat': stat, 'line': line, 
                        'expected': expected, 'edge': edge, 'recommendation': recommendation
                    })
                else:
                    print(f"  ✅ No significant edge")
            else:
                print(f"📊 {player} {stat}: No baseline data for this stat")
            
            print()
        
        print(f"📊 SUMMARY: Found {len(edges)} betting edges!")
        
        if edges:
            print(f"\n🎯 RECOMMENDED BETS:")
            for edge in edges:
                print(f"  {edge['recommendation']} {edge['line']} - {edge['player']} {edge['stat']} (Edge: {edge['edge']:+.1f})")
            
            # Save results
            edges_df = pd.DataFrame(edges)
            edges_df.to_csv("data/betting_edges.csv", index=False)
            print(f"\n💾 Results saved to data/betting_edges.csv")
        else:
            print(f"\n🔍 No significant edges found")
        
        return edges
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    analyze_props()
