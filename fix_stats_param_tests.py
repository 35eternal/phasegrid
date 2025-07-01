"""
Fix stats tests that have wrong expectations
"""
# Fix test_stats_main.py to expect named parameters
with open('tests/test_stats_main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace assert_called_with(30) with assert_called_with(days=30)
content = content.replace(
    "mock_generator.load_data.assert_called_with(30)",
    "mock_generator.load_data.assert_called_with(days=30)"
)

with open('tests/test_stats_main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed test_stats_main.py parameter expectations")
