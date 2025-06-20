# ✅ Post-Slate Intake Checklist – June 18, 2025

## 📋 Daily Processing Steps

### 1. 📝 Add Actual Results
- [ ] Open `daily_betting_card.csv`
- [ ] Add `actual_result` values for each completed bet
- [ ] Verify all games have concluded

### 2. 🔄 Run Processing Scripts
Execute in this order:

```bash
python add_actual_results.py
```
- [ ] Confirms results added to betting card
- [ ] Updates profit/loss calculations

```bash
python validate_cycle_predictions.py
```
- [ ] Validates phase predictions against actuals
- [ ] Updates phase accuracy metrics

```bash
python backtest_engine.py
```
- [ ] Runs full backtest with new results
- [ ] Updates performance metrics

```bash
python phase_confidence_tracker.py
```
- [ ] Updates confidence levels per phase
- [ ] Checks if 20+ bet threshold met

### 3. 📊 Verify Outputs
- [ ] Check `output/` folder for updated files:
  - [ ] `phase_confidence_levels.csv`
  - [ ] `backtest_summary.csv`
  - [ ] `dynamic_kelly_divisors.csv`

### 4. 🗄️ Archive Results
Create dated archive folder:
```bash
mkdir archived_results/2025-06-18
```

Move these files:
- [ ] `daily_betting_card_adjusted.csv` → `archived_results/2025-06-18/`
- [ ] `output/*.csv` → `archived_results/2025-06-18/`
- [ ] `phase_logs/*.log` → `archived_results/2025-06-18/`

### 5. 🧹 Reset for Next Slate
- [ ] Clear `daily_betting_card.csv` (keep headers only)
- [ ] Run `folder_prep.py` for clean state
- [ ] Verify `input/` folder is ready

### 6. 🎯 Production Mode Checks
- [ ] Verify phase bet counts in `phase_results_tracker.csv`
- [ ] Run `phase_multiplier_engine.py` for updated divisors
- [ ] Confirm confidence levels match expected thresholds

### 7. 📈 Optional Analytics
- [ ] Generate phase performance graphs
- [ ] Update cumulative ROI tracker
- [ ] Review any flagged integrity issues

## 🚨 Troubleshooting

**Missing Results?**
- Check game postponements
- Verify data source availability

**Script Errors?**
- Check `phase_logs/` for error details
- Run `log_integrity_check.py` for diagnostics

**Archive Issues?**
- Ensure sufficient disk space
- Check write permissions

---

**Next Slate Prep Time:** Complete by 11:00 AM ET
**Generated:** 2025-06-17 20:28:35
