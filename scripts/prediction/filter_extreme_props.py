#!/usr/bin/env python3
"""
Anomaly detection filter for WNBA prop predictions.
Detects and filters Demon (bait Over) and Goblin (bait Under) props.
"""

import pandas as pd
import os

# Configuration
THRESHOLD = 8.0
INPUT_FILE = "data/wnba_prop_predictions.csv"
OUTPUT_FILTERED = "data/wnba_prop_predictions_filtered.csv"
OUTPUT_ANOMALIES = "output/anomalies.csv"

def main():
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Read the input CSV
    df = pd.read_csv(INPUT_FILE)
    
    # Calculate difference between line and predicted_value
    df['difference'] = df['line'] - df['predicted_value']
    
    # Identify anomalies
    df['is_anomaly'] = (df['difference'] >= THRESHOLD) | (df['difference'] <= -THRESHOLD)
    
    # Classify anomaly type
    df['anomaly_type'] = ''
    df.loc[df['difference'] >= THRESHOLD, 'anomaly_type'] = 'DEMON'
    df.loc[df['difference'] <= -THRESHOLD, 'anomaly_type'] = 'GOBLIN'
    
    # Calculate anomaly score (absolute difference)
    df['anomaly_score'] = df['difference'].abs()
    
    # Split data
    normal_props = df[~df['is_anomaly']].copy()
    anomalous_props = df[df['is_anomaly']].copy()
    
    # Remove the temporary 'difference' column before saving
    df.drop('difference', axis=1, inplace=True)
    normal_props.drop('difference', axis=1, inplace=True)
    anomalous_props.drop('difference', axis=1, inplace=True)
    
    # Save filtered (normal) props
    normal_props.to_csv(OUTPUT_FILTERED, index=False)
    print(f"✓ Saved {len(normal_props)} normal props to {OUTPUT_FILTERED}")
    
    # Save anomalies
    if len(anomalous_props) > 0:
        anomalous_props.to_csv(OUTPUT_ANOMALIES, index=False)
        print(f"✓ Saved {len(anomalous_props)} anomalies to {OUTPUT_ANOMALIES}")
        print(f"  - DEMON props: {len(anomalous_props[anomalous_props['anomaly_type'] == 'DEMON'])}")
        print(f"  - GOBLIN props: {len(anomalous_props[anomalous_props['anomaly_type'] == 'GOBLIN'])}")
    else:
        print("✓ No anomalies detected")
    
    print(f"\nProcessing complete!")
    print(f"Total props: {len(df)}")
    print(f"Normal props: {len(normal_props)} ({len(normal_props)/len(df)*100:.1f}%)")
    print(f"Anomalous props: {len(anomalous_props)} ({len(anomalous_props)/len(df)*100:.1f}%)")

if __name__ == "__main__":
    main()

# Sample Output (3 rows from anomalies.csv):
# player_name,stat_type,line,predicted_value,is_anomaly,anomaly_type,anomaly_score
# Brittney Griner,Points,24.5,15.8,True,DEMON,8.7
# A'ja Wilson,Rebounds,8.5,17.3,True,GOBLIN,8.8
# Diana Taurasi,Assists,12.5,3.2,True,DEMON,9.3