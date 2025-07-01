"""Fix test_guardrail.py comprehensively"""
import re

# Read the file
with open('tests/test_guardrail.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Look for the actual problem - it seems like the test is comparing with a dict
# Let's check if minimum_slips is being set as a dict somewhere
if "'minimum_slips':" in content or '"minimum_slips":' in content:
    print("Found dict-style initialization")
    
    # Replace all dict-style initializations
    content = re.sub(
        r"SlipProcessor\(\s*\{[^}]+\}\s*\)",
        lambda m: convert_dict_to_kwargs(m.group(0)),
        content
    )

# Also check if tests are setting minimum_slips incorrectly
# Replace patterns like processor.minimum_slips = {'minimum_slips': 5}
content = re.sub(
    r"\.minimum_slips\s*=\s*\{[^}]+\}",
    lambda m: '.minimum_slips = ' + extract_value(m.group(0)),
    content
)

def convert_dict_to_kwargs(match_str):
    """Convert dict initialization to kwargs"""
    # Extract the dict content
    dict_match = re.search(r'\{([^}]+)\}', match_str)
    if dict_match:
        dict_content = dict_match.group(1)
        # Parse key-value pairs
        kwargs = []
        for pair in dict_content.split(','):
            if ':' in pair:
                key, value = pair.split(':', 1)
                key = key.strip().strip("'\"")
                value = value.strip()
                kwargs.append(f"{key}={value}")
        return f"SlipProcessor({', '.join(kwargs)})"
    return match_str

def extract_value(match_str):
    """Extract numeric value from dict assignment"""
    value_match = re.search(r":\s*(\d+)", match_str)
    if value_match:
        return value_match.group(1)
    return "5"  # default

# Write the fixed content
with open('tests/test_guardrail.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed test_guardrail.py")

# Let's also check the actual line causing the error
print("\nChecking for the actual error source...")
with open('phasegrid/slip_processor.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'if slip_count < self.minimum_slips' in line:
            print(f"Line {i+1}: {line.strip()}")
            print("This line expects minimum_slips to be an int")
