#!/usr/bin/env python3
"""Fix PrizePicks API call with correct parameters"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Read slips_generator.py
content = open('slips_generator.py', 'r').read()

# Fix the API parameters based on Stack Overflow example
fixes = [
    # Add game_mode parameter
    ("'single_stat': True", "'single_stat': True, 'game_mode': 'pickem'"),
    # Fix the parsing to handle actual API structure
    ("projection.get('stat_type', '')", "str(projection.get('stat_type', ''))"),
    # Add better error handling
    ("except requests.RequestException as e:", "except Exception as e:  # Catch all errors")
]

for old, new in fixes:
    content = content.replace(old, new)

# Save fixed version
with open('slips_generator_fixed.py', 'w') as f:
    f.write(content)

print("✅ Created slips_generator_fixed.py with API fixes")

# Now create a working auto_paper that uses the fixed generator
auto_paper_content = open('auto_paper_fixed.py', 'r').read()
auto_paper_content = auto_paper_content.replace('from slips_generator import', 'from slips_generator_fixed import')

with open('auto_paper_final.py', 'w') as f:
    f.write(auto_paper_content)

print("✅ Created auto_paper_final.py that uses fixed generator")
