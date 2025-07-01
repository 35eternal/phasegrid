#!/usr/bin/env python3
"""Create working enricher based on API structure"""
import json

# Look at what we have
with open('working_slips_30.json', 'r') as f:
    existing_slips = json.load(f)

print("🔍 Analyzing existing slip structure...")
print(f"Found {len(existing_slips)} slips")

# Get unique prizepicks IDs
pp_ids = [slip['prizepicks_id'] for slip in existing_slips if slip.get('prizepicks_id')]
print(f"\nPrizePicks IDs found: {pp_ids[:5]}")

# Now let's create a proper enricher
enricher_code = '''
def enrich_projection_fixed(projection):
    """Fixed enricher that properly parses PrizePicks data"""
    
    # Handle different API response structures
    if isinstance(projection, dict):
        # Check for nested structure
        if 'attributes' in projection:
            attrs = projection['attributes']
            
            # Extract player info
            player_name = "Unknown"
            if 'new_player' in attrs and isinstance(attrs['new_player'], dict):
                player_name = attrs['new_player'].get('name', 'Unknown')
            elif 'player' in attrs:
                player_name = attrs['player'].get('name', 'Unknown')
                
            # Extract stat type
            stat_type = attrs.get('stat_type', 'Unknown')
            if isinstance(stat_type, dict):
                stat_type = stat_type.get('name', 'Unknown')
                
            # Extract line
            line = attrs.get('line_score', 0)
            
            # Extract game info
            game_info = attrs.get('game', {})
            
            return {
                'id': projection.get('id', ''),
                'player_name': player_name,
                'stat_type': stat_type,
                'line': line,
                'game_time': game_info.get('start_time', ''),
                'odds': -110,  # Default
                'confidence': 0.65  # Default
            }
        else:
            # Direct structure
            return {
                'id': projection.get('id', ''),
                'player_name': projection.get('player_name', 'Unknown'),
                'stat_type': projection.get('stat_type', 'Unknown'),
                'line': projection.get('line', 0),
                'game_time': projection.get('game_time', ''),
                'odds': projection.get('odds', -110),
                'confidence': 0.65
            }
    
    return None
'''

# Save the fixed enricher
with open('enricher_fix.py', 'w') as f:
    f.write(enricher_code)

print("\n✅ Created enricher_fix.py")
print("\nNow we need to integrate this into the slips_generator...")
