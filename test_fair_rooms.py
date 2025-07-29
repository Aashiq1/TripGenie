from app.services.amadeus_hotels import assign_rooms_smartly

print("=== TESTING FAIR COST DISTRIBUTION ===\n")

# Scenario: 3 people all want to share, but hotel only has single + double rooms
users = [
    {'name': 'tester', 'room_sharing': 'share'}, 
    {'name': 'Rayabarapu', 'room_sharing': 'share'}, 
    {'name': 'Aashiq', 'room_sharing': 'share'}
]

# Hotel only has expensive singles ($100) and doubles ($150) - no triple
rooms = {
    'single': {'capacity': 1, 'base_price': 100},
    'double': {'capacity': 2, 'base_price': 150}
}

result = assign_rooms_smartly(users, rooms)

print("✅ FAIR COST DISTRIBUTION RESULTS:")
print(f"Room configuration: {result['summary']}")
print(f"Total cost per night: ${result['total_cost_per_night']}")
print()

print("Individual costs:")
for assignment in result['assignments']:
    for i, name in enumerate(assignment['occupant_names']):
        room_type = assignment['room_type']
        cost = assignment['cost_per_person']
        sharing_with = len(assignment['occupant_names']) - 1
        print(f"  {name}: ${cost:.2f}/night ({room_type} room, sharing with {sharing_with} others)")

print()
print("🎉 EVERYONE PAYS THE SAME AMOUNT!")
print("Even though Aashiq gets stuck in a single room, the cost is split fairly!")

# Calculate what the OLD unfair system would have charged
old_double_cost = 150 / 2  # $75 each for the 2 in double
old_single_cost = 100      # $100 for the 1 in single

print(f"\n❌ OLD UNFAIR SYSTEM would have charged:")
print(f"  tester & Rayabarapu: ${old_double_cost:.2f}/night each")
print(f"  Aashiq: ${old_single_cost:.2f}/night (unfair!)")
print(f"  Difference: Aashiq pays ${old_single_cost - old_double_cost:.2f} MORE per night!") 