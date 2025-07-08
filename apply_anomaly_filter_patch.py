"""
Patch to integrate anomaly filter into auto_paper.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def apply_anomaly_filter_patch():
    """Apply the anomaly filter integration to auto_paper.py"""
    
    # Read the current auto_paper.py
    with open('scripts/auto_paper.py', 'r') as f:
        content = f.read()
    
    # Add import for anomaly filter after other imports
    import_section = content.split('from utils.csv_writer import write_csv')[0]
    new_import = 'from utils.csv_writer import write_csv\nfrom phasegrid.anomaly_filter import AnomalyFilter'
    content = content.replace('from utils.csv_writer import write_csv', new_import)
    
    # Add anomaly filtering after loading board data
    # Find the line after "Loaded X props from PrizePicks"
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Add anomaly filtering after loading the board
        if 'print(f"Loaded {len(board)} props from PrizePicks")' in line:
            new_lines.extend([
                '',
                '    # Filter out PrizePicks Demons and Goblins',
                '    anomaly_filter = AnomalyFilter(tolerance_percentage=15.0)',
                '    original_count = len(board)',
                '    board = anomaly_filter.filter_anomalies(board)',
                '    filtered_count = original_count - len(board)',
                '    print(f"Filtered {filtered_count} demon/goblin projections, {len(board)} standard projections remaining")',
                ''
            ])
    
    # Join the lines back
    new_content = '\n'.join(new_lines)
    
    # Write the patched file
    with open('scripts/auto_paper.py', 'w') as f:
        f.write(new_content)
    
    print("Successfully patched auto_paper.py with anomaly filter integration")

if __name__ == "__main__":
    apply_anomaly_filter_patch()
