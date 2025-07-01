#!/usr/bin/env python3
"""Generate slips bypassing the live-only restriction"""
import os
import sys
from datetime import datetime
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🏀 PHASEGRID BETTING CARD GENERATOR")
print("=" * 50)

# Use the existing auto_paper logic but without live restriction
from auto_paper import AutoPaper

class AutoPaperNoLive(AutoPaper):
    """Modified AutoPaper that gets ALL games, not just live"""
    
    def fetch_live_lines(self, league: str = "WNBA"):
        """Override to fetch ALL lines, not just live"""
        try:
            print(f"📊 Fetching ALL {league} lines (not just live)...")
            
            # Get all projections
            projections = self.prizepicks_client.fetch_projections(
                league=league, 
                include_live=True  # This actually means "include all"
            )
            
            # Process projections
            slips = []
            if isinstance(projections, dict) and 'data' in projections:
                for proj in projections.get('data', []):
                    # Extract projection data properly
                    attrs = proj.get('attributes', {})
                    
                    slip = {
                        'projection_id': proj.get('id'),
                        'player_name': attrs.get('new_player', {}).get('name', 'Unknown'),
                        'stat_type': attrs.get('stat_type', 'Unknown'),
                        'line': attrs.get('line_score', 0),
                        'game_id': attrs.get('game', {}).get('id'),
                        'start_time': attrs.get('game', {}).get('start_time', '')
                    }
                    
                    if slip['player_name'] != 'Unknown':
                        slips.append(slip)
                        
            print(f"✅ Found {len(slips)} valid projections")
            return slips
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

# Run it
if __name__ == "__main__":
    paper = AutoPaperNoLive()
    
    # Initialize
    paper.sheet_id = os.getenv('GOOGLE_SHEET_ID')
    
    # Fetch lines
    lines = paper.fetch_live_lines("WNBA")
    
    if lines:
        print(f"\n📋 Sample lines:")
        for line in lines[:3]:
            print(f"\n{line['player_name']} - {line['stat_type']}: {line['line']}")
            print(f"  Game time: {line['start_time']}")
            
        # Save
        with open('all_lines_found.json', 'w') as f:
            json.dump(lines, f, indent=2)
        print(f"\n💾 Saved {len(lines)} lines to all_lines_found.json")
    else:
        print("\n⚠️ No lines found")
