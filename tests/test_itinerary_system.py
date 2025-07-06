#!/usr/bin/env python3
"""
Test: New Itinerary-Focused System
Demonstrates the improved approach where users provide destinations and AI creates detailed itineraries
"""

import asyncio
import json
import os

# Mock environment variables before importing
os.environ.setdefault('AMADEUS_CLIENT_ID', 'test_client_id')
os.environ.setdefault('AMADEUS_CLIENT_SECRET', 'test_client_secret')
os.environ.setdefault('OPENAI_API_KEY', 'test_openai_key')
os.environ.setdefault('TAVILY_API_KEY', 'test_tavily_key')

from app.tools.tavily_itinerary_tool import ItineraryTool
from app.tools.amadeus_flight_tool import AmadeusFlightTool
from app.tools.amadeus_hotel_tool import HotelSearchTool

async def test_itinerary_system():
    """Test the new itinerary creation system"""
    
    print("🧪 TESTING: Itinerary-Focused Travel Planning System")
    print("=" * 60)
    
    # Simulate user input based on the 10 questions approach
    user_input = {
        "departure_city": "Los Angeles",
        "budget_per_person": 1200,
        "top_destinations": ["San Diego", "Barcelona", "Tokyo"],  # User's top 3 choices (ranked)
        "interests": ["food tours", "museums", "photography", "beach"],  # From hardcoded list
        "group_size": 4,  # Impacts lodging, reservations, group activities
        "trip_pace": "balanced",  # 1-2 major activities/day
        "trip_duration_days": 5,
        "travel_style": "mid-range"
    }
    
    print("👥 USER INPUT:")
    print(f"  • Departure: {user_input['departure_city']}")
    print(f"  • Budget: ${user_input['budget_per_person']} per person")
    print(f"  • Top 3 Destinations: {', '.join(user_input['top_destinations'])}")
    print(f"  • Interests: {', '.join(user_input['interests'])}")
    print(f"  • Group Size: {user_input['group_size']} people")
    print(f"  • Trip Pace: {user_input['trip_pace']}")
    print(f"  • Duration: {user_input['trip_duration_days']} days")
    print()
    
    # Test 1: Create detailed itineraries for all three destinations
    print("🗓️ STEP 1: Creating Detailed Itineraries...")
    print("-" * 40)
    
    itinerary_tool = ItineraryTool()
    itinerary_input = {
        "destinations": user_input["top_destinations"],
        "interests": user_input["interests"],
        "group_size": user_input["group_size"],
        "trip_pace": user_input["trip_pace"],
        "trip_duration_days": user_input["trip_duration_days"]
    }
    
    itinerary_result = itinerary_tool._call(json.dumps(itinerary_input))
    itineraries = json.loads(itinerary_result)
    
    for dest, itinerary in itineraries.items():
        print(f"\n📍 {dest.upper()} ITINERARY:")
        print(f"   Summary: {itinerary['itinerary_summary']}")
        print(f"   Total Activities: {itinerary['total_activities']}")
        
        for day_info in itinerary["daily_itinerary"][:2]:  # Show first 2 days
            day = day_info["day"]
            print(f"\n   Day {day}: ({day_info['total_duration_hours']} hours, ${day_info['daily_cost']} cost)")
            for activity in day_info["activities"]:
                print(f"     • {activity['name']} ({activity['duration']}h, ${activity['total_cost']})")
                print(f"       Type: {activity['type']} | {activity['group_notes']}")
    
    # Test 2: Get flight prices for all destinations
    print("\n\n✈️ STEP 2: Getting Flight Prices...")
    print("-" * 40)
    
    flight_tool = AmadeusFlightTool()
    flight_input = {
        "flight_groups": [
            {
                "departure_city": user_input["departure_city"],
                "passenger_count": user_input["group_size"],
                "destinations": user_input["top_destinations"],
                "departure_date": "2024-06-15",
                "return_date": "2024-06-22"
            }
        ]
    }
    
    flight_result = flight_tool._call(json.dumps(flight_input))
    flight_prices = json.loads(flight_result)
    
    for group, destinations in flight_prices.items():
        for dest, pricing in destinations.items():
            print(f"   {dest}: ${pricing.get('price_round_trip', 'N/A')} round trip")
    
    # Test 3: Get hotel prices for all destinations
    print("\n🏨 STEP 3: Getting Hotel Prices...")
    print("-" * 40)
    
    hotel_tool = HotelSearchTool()
    hotel_input = {
        "destinations": ["BCN", "CDG", "NRT"],  # Convert to airport codes
        "check_in": "2024-06-15",
        "check_out": "2024-06-22",
        "group_accommodation_style": "standard",
        "accommodation_details": [
            {"name": "User1", "email": "user1@example.com", "room_sharing": "any"},
            {"name": "User2", "email": "user2@example.com", "room_sharing": "any"},
            {"name": "User3", "email": "user3@example.com", "room_sharing": "any"},
            {"name": "User4", "email": "user4@example.com", "room_sharing": "any"}
        ]
    }
    
    hotel_result = hotel_tool._call(json.dumps(hotel_input))
    hotel_prices = json.loads(hotel_result)
    
    for dest, hotel_data in hotel_prices.items():
        if 'hotels' in hotel_data and hotel_data['hotels']:
            hotel_info = hotel_data["hotels"][0]  # First hotel option
            print(f"   {dest}: ${hotel_info.get('total_cost_per_night', 'N/A')}/night ({hotel_info.get('hotel_name', 'Unknown')})")
        else:
            print(f"   {dest}: No hotels found")
    
    # Test 4: Complete cost analysis
    print("\n💰 STEP 4: Complete Cost Analysis...")
    print("-" * 40)
    
    dest_codes = ["BCN", "CDG", "NRT"]
    dest_names = ["Barcelona", "Paris", "Tokyo"]
    
    for i, dest in enumerate(dest_names):
        dest_code = dest_codes[i]
        
        # Get flight cost from flight_groups structure
        flight_cost = 0
        for group, destinations in flight_prices.items():
            if dest_code in destinations:
                flight_cost = destinations[dest_code].get("total_price", 0)
                break
        
        # Get hotel cost
        hotel_cost = 0
        if dest_code in hotel_prices and 'hotels' in hotel_prices[dest_code]:
            hotels = hotel_prices[dest_code]['hotels']
            if hotels:
                hotel_cost = hotels[0].get('total_trip_cost', 0)
        
        # Get activity cost
        activity_cost = 0
        if dest in itineraries and 'daily_itinerary' in itineraries[dest]:
            activity_cost = sum(day.get("daily_cost", 0) for day in itineraries[dest]["daily_itinerary"])
        
        total_cost = flight_cost + hotel_cost + activity_cost
        
        print(f"\n   {dest} TOTAL COST:")
        print(f"     Flights: ${flight_cost:,}")
        print(f"     Hotels: ${hotel_cost:,}")
        print(f"     Activities: ${activity_cost:,}")
        print(f"     TOTAL: ${total_cost:,} for entire group")
        if user_input['group_size'] > 0:
            print(f"     Per Person: ${total_cost // user_input['group_size']:,}")
            
            # Budget fit analysis
            per_person_cost = total_cost // user_input['group_size']
            budget_fit = "✅ Within Budget" if per_person_cost <= user_input['budget_per_person'] else "❌ Over Budget"
            print(f"     Budget Fit: {budget_fit}")
    
    print("\n" + "=" * 60)
    print("🎯 SYSTEM ADVANTAGES:")
    print("=" * 60)
    
    print("\n✅ NO MORE GUESSWORK:")
    print("  • User provides exact destinations they want to visit")
    print("  • No AI destination 'recommendations' that miss the mark")
    
    print("\n✅ DETAILED PLANNING:")
    print("  • Day-by-day itineraries with specific activities")
    print("  • Activities prioritized based on stated interests")
    print("  • Group size considerations for reservations")
    
    print("\n✅ REAL COST DATA:")
    print("  • Actual flight prices with seasonal adjustments")
    print("  • Hotel pricing based on travel style preferences")
    print("  • Complete cost breakdowns per destination")
    
    print("\n✅ SMART CUSTOMIZATION:")
    print("  • Trip pace affects daily activity scheduling")
    print("  • Interest-based activity prioritization")
    print("  • Group-aware planning (reservations, costs)")
    
    print("\n🚀 RESULT: Users get exactly what they want - detailed plans for")
    print("    their chosen destinations with real pricing and smart scheduling!")

if __name__ == "__main__":
    asyncio.run(test_itinerary_system()) 