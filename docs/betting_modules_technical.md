# WNBA Betting Intelligence System Documentation
## Modules: Dynamic Odds Injector & Phase-Based Kelly Modifier

### Executive Summary
This document outlines the implementation of two critical modules for the WNBA sports betting intelligence system:
1. **Dynamic Odds Injector**: Integrates real-world payout odds into betting recommendations
2. **Phase-Based Kelly Modifier**: Adjusts bet sizing based on menstrual phase performance data

---

## Module 1: Dynamic Odds Injector

### Purpose
Enhance betting cards with actual payout odds from sportsbooks (PrizePicks, FanDuel, etc.) to improve expected value calculations and bankroll optimization.

### Technical Implementation

#### Input Requirements
- **Primary**: `daily_betting_card.csv` with columns:
  - `player_name`: Player identifier
  - `stat_type`: Betting market type (points, rebounds, etc.)
  - Additional betting metrics
- **Optional**: `live_odds.csv` with columns:
  - `player_name`: Must match primary file exactly
  - `stat_type`: Must match primary file exactly
  - `actual_odds`: Decimal odds format

#### Processing Logic
```python
IF live_odds file exists AND player/stat match found:
    USE live odds value
ELSE:
    IF stat_type in ['fantasy_score', 'fantasy_points', 'fp']:
        USE 1.0 (EV-neutral)
    ELSE:
        USE 0.9 (-110 standard prop)
```

#### Output Schema
Adds column: `actual_odds` (float) - Decimal representation of payout odds

### Assumptions & Hardcoded Rules

1. **Default Odds Mapping**:
   - Standard props: 0.9 (represents -110 or 90.91% implied probability)
   - Fantasy scores: 1.0 (placeholder for EV-neutral calculation)

2. **Name Matching**: Requires exact string match between files (case-sensitive)

3. **Missing Data Handling**: Always provides a value (never null) to maintain downstream compatibility

### Risk Flags 🚩
- **Stale Odds Risk**: No timestamp validation on live odds
- **Name Mismatch Risk**: Player name variations (e.g., "A. Wilson" vs "Aja Wilson") will fail to match
- **Market Type Risk**: New stat types default to standard prop odds without warning

---

## Module 2: Phase-Based Kelly Modifier

### Purpose
Dynamically adjust position sizing based on validated historical performance across menstrual cycle phases.

### Technical Implementation

#### Phase Performance Matrix
| Phase | Historical Win Rate | Risk Strategy | Kelly Divisor |
|-------|-------------------|---------------|---------------|
| Luteal | 80% | Aggressive | 3 |
| Follicular | 67% | Moderate | 5 |
| Menstrual | 20% | Conservative | 10 |
| Ovulation | TBD | Default | 5 |

#### Calculation Formula
```python
kelly_used = raw_kelly / phase_divisor
bet_percentage = kelly_used * 100
```

#### Phase Validation Logic
- Normalizes phase names to lowercase
- Maps variations (e.g., "ovulatory" → "ovulation")
- Missing/invalid phases → default divisor (5)

### Assumptions & Hardcoded Rules

1. **Divisor Selection**: Based on historical backtest data (not dynamically updated)

2. **Phase Categories**: Fixed to 4 phases + default

3. **Conservative Bias**: Default divisor (5) is moderate-conservative

4. **Linear Scaling**: Assumes Kelly criterion scales linearly with divisor

### Risk Flags 🚩
- **Data Quality Risk**: 20% win rate in menstrual phase suggests possible data issues or small sample size
- **Phase Attribution Risk**: No validation that phase data is current/accurate
- **Overfitting Risk**: Divisors may be overfit to historical data
- **Capital Preservation**: Even with 10x divisor, menstrual phase bets may destroy capital at 20% win rate

---

## Integration & Usage

### Quick Start
```python
from betting_enhancer import BettingSystemEnhancer

enhancer = BettingSystemEnhancer()
enhanced_df = enhancer.enhance_betting_card(
    input_path='daily_betting_card.csv',
    output_path='output/daily_betting_card_adjusted.csv',
    live_odds_path='live_odds.csv'  # Optional
)
```

### Output Files
1. **daily_betting_card_adjusted.csv**: Primary output with all enhancements
2. **backtest_ready.csv**: Includes empty `actual_result` column for validation

### Testing Protocol
1. Run with provided test data (5 sample bets)
2. Verify odds injection logic
3. Confirm Kelly adjustments by phase
4. Manually add `actual_result` for backtest validation

---

## Critical Warnings ⚠️

### Capital Risk Management
1. **Menstrual Phase Alert**: Consider removing bets entirely during menstrual phase given 20% win rate
2. **Kelly Override**: Implement maximum bet size caps regardless of Kelly calculation
3. **Odds Validation**: Verify live odds are within reasonable ranges (0.5 - 3.0)

### Data Integrity
1. **Phase Data Currency**: Ensure phase data is updated daily
2. **Player Name Standardization**: Implement fuzzy matching for odds lookup
3. **Backtest Validation**: Minimum 100 bets per phase before trusting divisors

### System Dependencies
- pandas >= 1.3.0
- numpy >= 1.21.0
- Python >= 3.8

---

## Recommended Enhancements

### Immediate (P0)
1. Add timestamp validation for live odds
2. Implement player name fuzzy matching
3. Add maximum bet size caps

### Short-term (P1)
1. Dynamic divisor updates based on rolling performance
2. Multi-source odds aggregation
3. Confidence-weighted Kelly adjustments

### Long-term (P2)
1. ML-based phase impact prediction
2. Real-time odds API integration
3. Automated backtest feedback loop

---

## Handoff Checklist ✅
- [ ] Code tested with 5+ sample bets
- [ ] Output files generated in `output/` directory
- [ ] Backtest-ready format includes all required columns
- [ ] Risk warnings understood and acknowledged
- [ ] Manual `actual_result` entry process documented

## Contact
For questions or issues, consult the senior AI engineering team or review system logs in the enhancement pipeline.