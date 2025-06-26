"""
Fix for test_guardrail.py - replace the incorrect minimum_slips parameter
"""
import re

# Read the test file
with open('tests/test_guardrail.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the SlipProcessor initialization calls that pass a dict
# Replace patterns like SlipProcessor({'minimum_slips': 5}) with SlipProcessor(minimum_slips=5)
content = re.sub(
    r"SlipProcessor\(\{'minimum_slips':\s*(\d+)\}\)",
    r"SlipProcessor(minimum_slips=\1)",
    content
)

# Also fix any that might have bypass_guard_rail in dict form
content = re.sub(
    r"SlipProcessor\(\{'minimum_slips':\s*(\d+),\s*'bypass_guard_rail':\s*(True|False)\}\)",
    r"SlipProcessor(minimum_slips=\1, bypass_guard_rail=\2)",
    content
)

# Write back the fixed content
with open('tests/test_guardrail.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed test_guardrail.py")
