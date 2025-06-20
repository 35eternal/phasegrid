import pandas as pd
import os

print("="*60)
print("WNBA BETTING PERFORMANCE ANALYSIS")
print("="*60)

# Load results
df = pd.read_csv("output/phase_results_tracker.csv")

# Basic stats
total_bets = len(df)
wins = len(df[df["Result"] == "W"])
losses = len(df[df["Result"] == "L"])
win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
total_pnl = df["Payout"].sum()

print(f"\nOVERALL PERFORMANCE:")
print(f"Total Bets: {total_bets}")
print(f"Record: {wins}W-{losses}L")
print(f"Win Rate: {win_rate:.1f}%")
print(f"Total P/L: {total_pnl:+.3f} units")
print(f"Average Bet Size: {df['Kelly'].mean():.3f}")

# Phase breakdown
print("\nPERFORMANCE BY PHASE:")
for phase in df["Phase"].unique():
    if phase != "Unknown":
        phase_df = df[df["Phase"] == phase]
        phase_wins = len(phase_df[phase_df["Result"] == "W"])
        phase_total = len(phase_df)
        phase_wr = (phase_wins / phase_total * 100) if phase_total > 0 else 0
        phase_pnl = phase_df["Payout"].sum()
        
        print(f"\n{phase.upper()}:")
        print(f"  Record: {phase_wins}W-{phase_total-phase_wins}L")
        print(f"  Win Rate: {phase_wr:.1f}%")
        print(f"  P/L: {phase_pnl:+.3f} units")

# Today's slate summary
if os.path.exists("output/optimal_betting_slate.csv"):
    print("\n" + "="*60)
    print("TODAY'S OPTIMAL SLATE:")
    slate = pd.read_csv("output/optimal_betting_slate.csv")
    print(f"Total Bets: {len(slate)}")
    print(f"Total Exposure: {slate['bet_percentage'].sum():.2f}%")
    
    phase_counts = slate["adv_phase"].value_counts()
    print("\nPhase Distribution:")
    for phase, count in phase_counts.items():
        print(f"  {phase}: {count} bets ({count/len(slate)*100:.0f}%)")
