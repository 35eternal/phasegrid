#!/usr/bin/env python3
"""
Phase Threshold Calculator
Shows estimated days until each phase reaches production confidence thresholds.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path


def calculate_days_to_threshold():
    """Calculate estimated days until each phase hits production thresholds."""
    
    print("🎯 PHASE THRESHOLD CALCULATOR")
    print("="*60)
    print(f"Current Date: {datetime.now().strftime('%Y-%m-%d')}")
    print("Production Thresholds: 20+ bets (MEDIUM), 30+ bets (HIGH)")
    print("="*60)
    
    # Load current phase data
    try:
        phase_data = pd.read_csv('output/backtest_by_phase.csv')
        betting_card = pd.read_csv('output/final_betting_card.csv')
    except FileNotFoundError as e:
        print(f"❌ Error loading files: {e}")
        return
        
    # Count bets per phase in today's card
    if 'adv_phase' in betting_card.columns:
        today_bets_by_phase = betting_card['adv_phase'].value_counts()
    elif 'phase' in betting_card.columns:
        today_bets_by_phase = betting_card['phase'].value_counts()
    else:
        print("❌ No phase column found in betting card")
        return
        
    print("\n📊 CURRENT STATUS & PROJECTIONS:")
    print("-"*60)
    print(f"{'Phase':<12} {'Current':<8} {'Today':<8} {'→ 20':<10} {'→ 30':<10} {'Status':<20}")
    print(f"{'':12} {'Bets':<8} {'Bets':<8} {'(days)':<10} {'(days)':<10}")
    print("-"*60)
    
    projections = []
    
    for _, row in phase_data.iterrows():
        phase = row['phase']
        current_bets = int(row['total_bets'])
        win_rate = row['win_rate']
        
        # Get today's bet count for this phase
        today_count = today_bets_by_phase.get(phase, 0)
        
        # Calculate days to thresholds
        if today_count > 0:
            days_to_20 = max(0, np.ceil((20 - current_bets) / today_count))
            days_to_30 = max(0, np.ceil((30 - current_bets) / today_count))
        else:
            days_to_20 = float('inf')
            days_to_30 = float('inf')
            
        # Determine current status
        if win_rate > 1:
            win_rate = win_rate / 100
            
        if current_bets >= 30 and win_rate >= 0.7:
            status = "✅ HIGH Ready!"
        elif current_bets >= 20 and win_rate >= 0.6:
            status = "🟨 MEDIUM Ready!"
        elif win_rate >= 0.7:
            status = "🔥 HIGH trajectory"
        elif win_rate >= 0.6:
            status = "📈 MEDIUM trajectory"
        else:
            status = "⚠️  Needs wins"
            
        # Format output
        days_20_str = "✓" if current_bets >= 20 else f"{int(days_to_20)}"
        days_30_str = "✓" if current_bets >= 30 else f"{int(days_to_30)}" if days_to_30 != float('inf') else "∞"
        
        print(f"{phase:<12} {current_bets:<8} {today_count:<8} {days_20_str:<10} {days_30_str:<10} {status:<20}")
        
        # Store projection data
        if days_to_20 < float('inf'):
            projections.append({
                'phase': phase,
                'milestone': '20 bets (MEDIUM)',
                'date': (datetime.now() + timedelta(days=int(days_to_20))).strftime('%Y-%m-%d'),
                'days': int(days_to_20),
                'win_rate': win_rate * 100
            })
            
    print("-"*60)
    
    # Show timeline
    if projections:
        print("\n\n📅 MILESTONE TIMELINE:")
        print("-"*60)
        
        # Sort by days
        projections.sort(key=lambda x: x['days'])
        
        for proj in projections[:5]:  # Show next 5 milestones
            if proj['days'] == 0:
                print(f"🎯 TODAY: {proj['phase']} reaches {proj['milestone']}")
            elif proj['days'] == 1:
                print(f"🔜 TOMORROW: {proj['phase']} reaches {proj['milestone']}")
            else:
                print(f"📍 {proj['date']}: {proj['phase']} reaches {proj['milestone']} "
                      f"(in {proj['days']} days) - Currently {proj['win_rate']:.1f}% win rate")
                      
    # Risk adapter advice
    print("\n\n💡 RISK ADAPTER STRATEGY:")
    print("-"*60)
    
    ready_for_prod = sum(1 for _, row in phase_data.iterrows() if row['total_bets'] >= 20)
    
    if ready_for_prod == 0:
        print("Status: 🧪 Keep using TEST thresholds (3-4 bets)")
        print("Action: Continue aggressive testing mode")
    elif ready_for_prod < 4:
        print(f"Status: 🔄 {ready_for_prod}/4 phases ready for production")
        print("Action: Consider hybrid approach or wait for all phases")
    else:
        print("Status: ✅ ALL phases have 20+ bets!")
        print("Action: Switch to PRODUCTION thresholds (20-30 bets)")
        
    # Summary stats
    total_bets = phase_data['total_bets'].sum()
    avg_bets_per_phase = total_bets / len(phase_data)
    total_today = today_bets_by_phase.sum()
    
    print(f"\n📊 VELOCITY METRICS:")
    print(f"• Total historical bets: {total_bets}")
    print(f"• Average per phase: {avg_bets_per_phase:.1f}")
    print(f"• Today's bet volume: {total_today}")
    print(f"• Daily run rate: {total_today/4:.1f} bets/phase")
    
    print("\n" + "="*60)
    print("✅ Calculation Complete!")


if __name__ == "__main__":
    calculate_days_to_threshold()