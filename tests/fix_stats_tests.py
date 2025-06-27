"""
Script to fix stats test files
"""
import re

# Fix test_stats_main.py
with open('tests/test_stats_main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace 'from scripts.stats import main' with 'from scripts.stats import cli'
content = re.sub(r'from scripts\.stats import main\b', 'from scripts.stats import cli', content)

# Replace 'runner.invoke(main' with 'runner.invoke(cli'
content = re.sub(r'runner\.invoke\(main\b', 'runner.invoke(cli', content)

with open('tests/test_stats_main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed test_stats_main.py")

# Do the same for test_stats_fixed.py if it exists
try:
    with open('tests/test_stats_fixed.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = re.sub(r'from scripts\.stats import main\b', 'from scripts.stats import cli', content)
    content = re.sub(r'runner\.invoke\(main\b', 'runner.invoke(cli', content)
    
    with open('tests/test_stats_fixed.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed test_stats_fixed.py")
except FileNotFoundError:
    print("test_stats_fixed.py not found, skipping")
