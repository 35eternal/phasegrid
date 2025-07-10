import re

# Read the workflow file
with open('.github/workflows/test.yml', 'r') as f:
    content = f.read()

# Replace cov-fail-under=20 with cov-fail-under=80
updated = re.sub(r'--cov-fail-under=20', '--cov-fail-under=80', content)

# Write back
with open('.github/workflows/test.yml', 'w') as f:
    f.write(updated)

print("Updated CI coverage threshold from 20% to 80%")
