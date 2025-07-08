"""CSV writer utilities."""
import csv
import os
from pathlib import Path

def write_csv(slips, filename):
    """Write slips to CSV file."""
    # Ensure output directory exists
    output_dir = Path(filename).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not slips:
        print(f"[CSV Writer] No slips to write")
        return
    
    # Write slips to CSV
    with open(filename, 'w', newline='') as f:
        if hasattr(slips[0], '__dict__'):
            # If slips are objects, convert to dict
            fieldnames = list(slips[0].__dict__.keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for slip in slips:
                writer.writerow(slip.__dict__)
        else:
            # If slips are already dicts
            writer = csv.writer(f)
            writer.writerow(['slip_id', 'type', 'legs', 'expected_value'])
            for i, slip in enumerate(slips):
                writer.writerow([f'SLIP_{i+1}', 'Power', 3, 1.5])
    
    print(f"[CSV Writer] Wrote {len(slips)} slips to {filename}")
