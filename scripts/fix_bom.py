import os
import glob

files_to_fix = [
    "analyze_bias.py", "analyze_bias_fixed.py", "analyze_props.py",
    "betting_analyzer.py", "betting_dashboard.py", "check_columns.py",
    "check_dates.py", "check_results.py", "create_safe_card.py",
    "create_slips_log.py", "cycle_betting_system.py", "cycle_detector.py",
    "cycle_detector_fixed.py", "cycle_pattern_summary.py", "debug_push.py",
    "diagnose_data.py", "enhanced_cycle_detector.py", "fix_betting_card.py",
    "pipeline.py", "real_roi.py", "robust_backtest.py", "run_backtest_fixed.py",
    "run_betting_workflow.py", "run_enhanced_pipeline.py", "run_enhancement.py",
    "setup_cycle_detector.py", "test_adjustments.py", "test_columns.py",
    "test_connector.py", "test_lines.py", "validation_template.py"
]

for pattern in ["*.py", "**/*.py", "**/**/*.py"]:
    for filepath in glob.glob(pattern, recursive=True):
        if any(f in filepath for f in files_to_fix):
            try:
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed: {filepath}")
            except Exception as e:
                print(f"Error fixing {filepath}: {e}")
