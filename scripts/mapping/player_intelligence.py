import json
import pandas as pd

class PlayerMappingIntelligence:
    def __init__(self):
        self.props_data = self.load_fresh_props()
        self.historical_data = self.load_historical_gamelogs()
        
    def load_fresh_props(self):
        with open('data/wnba_prizepicks_props.json', 'r') as f:
            return json.load(f)
    
    def load_historical_gamelogs(self):
        return pd.read_csv('data/processed/gamelogs_with_cycles.csv')
    
    def analyze_player_profile(self, player_id):
        player_props = []
        for prop in self.props_data:
            if (prop.get('relationships', {}).get('new_player', {}).get('data', {}).get('id') == player_id):
                attrs = prop['attributes']
                player_props.append({
                    'stat': attrs.get('stat_type'),
                    'line': float(attrs.get('line_score', 0)) if attrs.get('line_score') else 0,
                    'game_id': attrs.get('game_id')
                })
        
        point_lines = [p['line'] for p in player_props if p['stat'] == 'Points' and p['line'] > 0]
        assist_lines = [p['line'] for p in player_props if p['stat'] == 'Assists' and p['line'] > 0]
        rebound_lines = [p['line'] for p in player_props if p['stat'] == 'Rebounds' and p['line'] > 0]
        
        profile = {
            'player_id': player_id,
            'total_props': len(player_props),
            'point_lines': sorted(point_lines) if point_lines else [],
            'assist_lines': sorted(assist_lines) if assist_lines else [],
            'rebound_lines': sorted(rebound_lines) if rebound_lines else [],
            'max_points': max(point_lines) if point_lines else 0,
            'max_assists': max(assist_lines) if assist_lines else 0,
            'max_rebounds': max(rebound_lines) if rebound_lines else 0,
            'stat_categories': list(set([p['stat'] for p in player_props]))
        }
        
        return profile
    
    def find_matching_historical_players(self, profile):
        matches = []
        
        if profile['max_points'] > 0:
            recent_scorers = self.historical_data.groupby('PLAYER_NAME')['PTS'].agg(['mean', 'max', 'count']).reset_index()
            
            for _, player in recent_scorers.iterrows():
                pts_match = abs(player['mean'] - profile['max_points']) < 8
                game_count = player['count'] >= 10
                
                if pts_match and game_count:
                    matches.append({
                        'name': player['PLAYER_NAME'],
                        'avg_pts': player['mean'],
                        'max_pts': player['max'],
                        'games': player['count'],
                        'line_diff': abs(player['mean'] - profile['max_points'])
                    })
        
        return sorted(matches, key=lambda x: x['line_diff'])

# Execute the analysis
mapper = PlayerMappingIntelligence()

print('TARS PLAYER IDENTIFICATION PROTOCOL')
print('=' * 50)

target_players = ['237846', '237862', '237844', '237845', '237863', '240007', '213055', '241648']

for player_id in target_players:
    print(f'\nANALYZING PLAYER {player_id}')
    profile = mapper.analyze_player_profile(player_id)
    
    print(f'   Max Points Line: {profile["max_points"]}')
    print(f'   Max Assists Line: {profile["max_assists"]}')  
    print(f'   Max Rebounds Line: {profile["max_rebounds"]}')
    print(f'   Total Props: {profile["total_props"]}')
    
    if profile['max_points'] > 0:
        matches = mapper.find_matching_historical_players(profile)
        print(f'   LIKELY CANDIDATES:')
        for match in matches[:3]:
            print(f'      {match["name"]}: {match["avg_pts"]:.1f} avg pts (+/-{match["line_diff"]:.1f})')
    else:
        print(f'   Non-scoring player (combos/role player)')

print('\nMAPPING ANALYSIS COMPLETE')