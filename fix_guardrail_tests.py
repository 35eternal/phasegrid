import re

# Read and fix test_guardrail.py
with open('tests/test_guardrail.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace dict-style initialization with keyword arguments
content = re.sub(r"SlipProcessor\(\{'minimum_slips':\s*(\d+)\}\)", r"SlipProcessor(minimum_slips=\1)", content)
content = re.sub(r"SlipProcessor\(\{'minimum_slips':\s*(\d+),\s*'bypass_guard_rail':\s*(True|False)\}\)", r"SlipProcessor(minimum_slips=\1, bypass_guard_rail=\2)", content)

with open('tests/test_guardrail.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed test_guardrail.py")
