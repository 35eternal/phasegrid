#!/usr/bin/env python3
"""
Post-Slate Intake Checklist Generator
Automatically generates daily checklist with proper dates and paths.
"""

import os
from datetime import datetime, timedelta

def generate_checklist(target_date=None):
    """Generate post-slate intake checklist for specified date."""
    
    # Use tomorrow's date if not specified
    if target_date is None:
        target_date = datetime.now() + timedelta(days=1)
    
    # Format dates
    checklist_date = target_date.strftime('%B %d, %Y')
    archive_date = target_date.strftime('%Y-%m-%d')
    
    checklist_content = f"""# ✅ Post-Slate Intake Checklist – {checklist_date}

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
mkdir archived_results/{archive_date}
```

Move these files:
- [ ] `daily_betting_card_adjusted.csv` → `archived_results/{archive_date}/`
- [ ] `output/*.csv` → `archived_results/{archive_date}/`
- [ ] `phase_logs/*.log` → `archived_results/{archive_date}/`

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
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return checklist_content

def save_checklist(content, target_date=None):
    """Save checklist to appropriate file."""
    
    if target_date is None:
        target_date = datetime.now() + timedelta(days=1)
    
    # Create checklists directory if needed
    os.makedirs('checklists', exist_ok=True)
    
    # Generate filename
    filename = f"post_slate_intake_{target_date.strftime('%Y-%m-%d')}.md"
    filepath = os.path.join('checklists', filename)
    
    # Save file with UTF-8 encoding for emoji support
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Checklist saved to: {filepath}")
    return filepath

def generate_weekly_checklists():
    """Generate checklists for the next 7 days."""
    print("📅 Generating weekly checklists...")
    
    for i in range(1, 8):
        target_date = datetime.now() + timedelta(days=i)
        content = generate_checklist(target_date)
        save_checklist(content, target_date)
    
    print(f"\n✅ Generated 7 daily checklists in 'checklists/' folder")

def main():
    """Generate checklist for tomorrow by default."""
    print("📋 Post-Slate Intake Checklist Generator")
    print("-" * 40)
    
    # Generate tomorrow's checklist
    tomorrow = datetime.now() + timedelta(days=1)
    content = generate_checklist(tomorrow)
    filepath = save_checklist(content, tomorrow)
    
    print(f"\n📄 Tomorrow's checklist ready!")
    print(f"   Date: {tomorrow.strftime('%B %d, %Y')}")
    print(f"   File: {filepath}")
    
    # Ask about weekly generation
    print("\n💡 Tip: Run with --weekly flag to generate 7 days of checklists")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--weekly':
        generate_weekly_checklists()
    else:
        main()