#!/usr/bin/env python3
"""
Test: New Itinerary-Focused System
Demonstrates the improved approach where users provide destinations and AI creates detailed itineraries
"""

import asyncio
import json
from app.services.langchain_travel_agent import ItineraryTool, FlightPriceTool, HotelPriceTool

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
    
    flight_tool = FlightPriceTool()
    flight_input = {
        "departure_city": user_input["departure_city"],
        "destinations": user_input["top_destinations"],
        "departure_date": "2024-06-15"
    }
    
    flight_result = flight_tool._call(json.dumps(flight_input))
    flight_prices = json.loads(flight_result)
    
    for dest, pricing in flight_prices.items():
        print(f"   {dest}: ${pricing['price_round_trip']} round trip")
    
    # Test 3: Get hotel prices for all destinations
    print("\n🏨 STEP 3: Getting Hotel Prices...")
    print("-" * 40)
    
    hotel_tool = HotelPriceTool()
    hotel_input = {
        "destinations": user_input["top_destinations"],
        "travel_style": user_input["travel_style"]
    }
    
    hotel_result = hotel_tool._call(json.dumps(hotel_input))
    hotel_prices = json.loads(hotel_result)
    
    for dest, hotels in hotel_prices.items():
        hotel_info = hotels["hotels"][0]  # First hotel option
        print(f"   {dest}: ${hotel_info['price_per_night']}/night ({hotel_info['name']})")
    
    # Test 4: Complete cost analysis
    print("\n💰 STEP 4: Complete Cost Analysis...")
    print("-" * 40)
    
    for dest in user_input["top_destinations"]:
        flight_cost = flight_prices[dest]["price_round_trip"] * user_input["group_size"]
        hotel_cost = hotel_prices[dest]["hotels"][0]["price_per_night"] * user_input["trip_duration_days"] * user_input["group_size"]
        activity_cost = sum(day["daily_cost"] for day in itineraries[dest]["daily_itinerary"])
        total_cost = flight_cost + hotel_cost + activity_cost
        
        print(f"\n   {dest} TOTAL COST:")
        print(f"     Flights: ${flight_cost:,} (${flight_prices[dest]['price_round_trip']} × {user_input['group_size']} people)")
        print(f"     Hotels: ${hotel_cost:,} (${hotel_prices[dest]['hotels'][0]['price_per_night']}/night × {user_input['trip_duration_days']} days × {user_input['group_size']} people)")
        print(f"     Activities: ${activity_cost:,}")
        print(f"     TOTAL: ${total_cost:,} for entire group")
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