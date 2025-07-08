# PG-108: Goblins & Demons Anomaly Handling - Implementation Summary

## Overview
Successfully implemented anomaly filtering for PrizePicks Demons and Goblins to ensure only standard projections are used for slip optimization.

## What are Demons and Goblins?
- **Demons** (red icon): Higher projections that are harder to hit but offer higher payouts (up to 100x-2000x)
- **Goblins** (green icon): Lower projections that are easier to hit but offer reduced payouts
- Both require picking "MORE" (over) only

## Implementation Details

### 1. Created phasegrid/anomaly_filter.py
- AnomalyFilter class with configurable tolerance percentage (default 15%)
- Identifies multiple projections for same player/prop combination
- Filters out extreme values (demons/goblins), keeping only standard projections
- For 3+ projections: keeps middle value
- For 2 projections with >15% difference: keeps lower value (conservative approach)

### 2. Integrated into scripts/auto_paper.py
- Added anomaly filtering after loading board data
- Logs number of filtered projections for transparency
- Maintains guard rail check (≥5 slips required)

### 3. Comprehensive Testing
- Created 	ests/test_anomaly_filter.py with 8 test cases
- Tests cover: empty inputs, single projections, tolerance percentage, real-world scenarios
- All tests passing ✅

### 4. Verified Integration
- Integration test confirms filtering works with board data format
- Maintains backward compatibility with existing pipeline
- Triple fallback flow (API → HTML → mock) continues to work

## Example Filtering
Input: A'ja Wilson points with 3 lines (18.5, 22.5, 26.5)
- 18.5 = Goblin (easier, lower payout)
- 22.5 = Standard ✅ (kept)
- 26.5 = Demon (harder, higher payout)
Output: Only 22.5 line remains

## Files Modified/Created
- Created: phasegrid/anomaly_filter.py
- Created: 	ests/test_anomaly_filter.py
- Modified: scripts/auto_paper.py

## Next Steps for Merge
1. Commit changes to feature branch
2. Ensure CI passes (coverage ≥80%)
3. Create PR for review
4. After merge, monitor dry runs to verify demon/goblin filtering in production
