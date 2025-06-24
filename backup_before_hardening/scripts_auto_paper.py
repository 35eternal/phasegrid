#!/usr/bin/env python3
"""
Auto Paper Script with PrizePicks Integration
Automates the process of generating predictions and optionally fetching live lines
"""
import os
import sys
import argparse
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from odds_provider.prizepicks import fetch_current_board
from slips_generator import generate_slips  # Assuming this exists


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Generate predictions with optional PrizePicks line fetching"
    )
    parser.add_argument(
        "--fetch_lines",
        action="store_true",
        help="Fetch current lines from PrizePicks before generating predictions"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=".",
        help="Output directory for predictions CSV (default: project root)"
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        default="data",
        help="Directory for data files (default: data)"
    )
    return parser.parse_args()


def merge_projections_with_lines(projections_df, lines_df):
    """
    Merge model projections with PrizePicks lines
    
    Args:
        projections_df: DataFrame with model projections
        lines_df: DataFrame with PrizePicks lines
        
    Returns:
        Merged DataFrame with predictions
    """
    # Standardize column names for merging
    lines_df["player"] = lines_df["player"].str.strip().str.title()
    projections_df["player"] = projections_df["player"].str.strip().str.title()
    
    # Merge on player and prop_type
    merged = pd.merge(
        projections_df,
        lines_df[["player", "prop_type", "line", "over_odds", "under_odds"]],
        on=["player", "prop_type"],
        how="left",
        suffixes=("_model", "_prizepicks")
    )
    
    # Calculate edge if we have both projection and line
    if "projection" in merged.columns and "line" in merged.columns:
        merged["edge"] = merged["projection"] - merged["line"]
        merged["edge_pct"] = (merged["edge"] / merged["line"] * 100).round(2)
        
        # Recommend plays based on edge
        merged["recommendation"] = merged.apply(
            lambda row: "OVER" if row["edge"] > 0 else "UNDER" if row["edge"] < 0 else "PASS",
            axis=1
        )
    
    return merged


def main():
    """Main execution function"""
    args = parse_args()
    
    try:
        # Step 1: Fetch lines if requested
        lines_path = None
        if args.fetch_lines:
            print("Fetching current PrizePicks lines...")
            lines_path = fetch_current_board(args.data_dir)
            print(f"Lines saved to: {lines_path}")
        
        # Step 2: Generate model projections (placeholder - adapt to actual implementation)
        print("Generating model projections...")
        # This would call your existing slips_generator or model code
        # For now, creating a placeholder
        projections_data = {
            "player": ["Player A", "Player B", "Player C"],
            "prop_type": ["Points", "Rebounds", "Assists"],
            "projection": [25.5, 8.2, 6.8]
        }
        projections_df = pd.DataFrame(projections_data)
        
        # If you have an actual slips generator:
        # projections_df = generate_slips()  # Adjust based on actual function
        
        # Step 3: Merge with lines if available
        if lines_path and os.path.exists(lines_path):
            print("Merging projections with PrizePicks lines...")
            lines_df = pd.read_csv(lines_path)
            predictions_df = merge_projections_with_lines(projections_df, lines_df)
        else:
            predictions_df = projections_df
        
        # Step 4: Save predictions
        today = datetime.now().strftime("%Y%m%d")
        output_path = os.path.join(args.output_dir, f"predictions_{today}.csv")
        
        predictions_df.to_csv(output_path, index=False)
        print(f"Predictions saved to: {output_path}")
        
        # Display summary
        if "recommendation" in predictions_df.columns:
            print("\nPrediction Summary:")
            print(predictions_df["recommendation"].value_counts())
            
            # Show top plays by edge
            top_plays = predictions_df.nlargest(5, "edge_pct")[
                ["player", "prop_type", "projection", "line", "edge_pct", "recommendation"]
            ]
            print("\nTop 5 Plays by Edge:")
            print(top_plays.to_string(index=False))
        
        return 0
        
    except Exception as e:
        print(f"Error in auto_paper: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())