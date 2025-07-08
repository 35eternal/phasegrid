from phasegrid.uuid_mapper import UUIDMapper

# Create mapper
mapper = UUIDMapper("data/demo_uuid_mappings.json")

# Test with different name formats
names = [
    "A'ja Wilson",
    "A'JA WILSON",  # Different case
    "Aja Wilson",   # No apostrophe
    "Breanna Stewart",
    "Diana Taurasi"
]

print("UUID Mapping Demo")
print("=" * 50)

for name in names:
    uuid = mapper.get_or_create_uuid(name)
    print(f"Player: {name}")
    print(f"UUID: {uuid}")
    print()

# Show stats
stats = mapper.get_mapping_stats()
print(f"Total unique players: {stats['total_players']}")
print(f"Total UUIDs: {stats['unique_uuids']}")
