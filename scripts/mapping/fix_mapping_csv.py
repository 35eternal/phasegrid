#!/usr/bin/env python3
"""
Quick fix for the missing Chelsea Gray and Jackie Young mappings
"""
import pandas as pd
import csv

def fix_player_mappings():
    """Fix the missing player mappings in the CSV file"""
    
    print("🔧 Fixing player mappings...\n")
    
    # Read current mappings
    df = pd.read_csv("data/player_final_mapping.csv")
    
    print("📋 Current mappings:")
    print(df.to_string(index=False))
    
    # Manual fixes based on known WNBA rosters
    fixes = {
        'Chelsea Gray': {
            'bbref_name': 'Chelsea Gray',
            'confidence': 100,
            'team': 'LAS',
            'position': 'G',
            'bbref_url': 'https://www.basketball-reference.com/wnba/players/g/grayche01w.html',
            'status': 'manual_fix'
        },
        'Jackie Young': {
            'bbref_name': 'Jackie Young', 
            'confidence': 100,
            'team': 'LAS',
            'position': 'G',
            'bbref_url': 'https://www.basketball-reference.com/wnba/players/y/youngja01w.html',
            'status': 'manual_fix'
        }
    }
    
    # Apply fixes
    for prizepicks_name, fix_data in fixes.items():
        mask = df['prizepicks_name'] == prizepicks_name
        
        if mask.any():
            for column, value in fix_data.items():
                df.loc[mask, column] = value
            print(f"✅ Fixed: {prizepicks_name} → {fix_data['bbref_name']}")
        else:
            print(f"⚠️ Player not found in CSV: {prizepicks_name}")
    
    # Save fixed mappings
    df.to_csv("data/player_final_mapping.csv", index=False)
    
    print(f"\n📊 FINAL MAPPING RESULTS:")
    mapped_count = len(df[df['bbref_name'] != ''])
    total_count = len(df)
    success_rate = (mapped_count / total_count) * 100
    
    print(f"  Total players: {total_count}")
    print(f"  Successfully mapped: {mapped_count}")
    print(f"  Success rate: {success_rate:.1f}%")
    
    print(f"\n✅ Updated mappings:")
    print(df.to_string(index=False))
    
    print(f"\n💾 Fixed mappings saved to data/player_final_mapping.csv")
    
    return df

if __name__ == "__main__":
    print("🔧 Player Mapping Fix Tool\n")
    fixed_df = fix_player_mappings()
    
    print(f"\n🎉 All players should now be mapped!")
    print(f"🔗 Ready to run your analysis pipeline")