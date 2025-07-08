import json

with open("data/wnba_prizepicks_props.json", "r") as f:
    data = json.load(f)
    
print(f"Total entries: {len(data['data'])}")

# Show first entry structure
if data['data']:
    first = data['data'][0]
    print("\nFirst entry structure:")
    for key in first.keys():
        print(f"  {key}: {type(first[key]).__name__}")
    
    # Show attributes if present
    if 'attributes' in first:
        print("\nAttributes:")
        for key, value in first['attributes'].items():
            print(f"  {key}: {value}")
            if isinstance(value, dict):
                for k, v in value.items():
                    print(f"    {k}: {v}")
