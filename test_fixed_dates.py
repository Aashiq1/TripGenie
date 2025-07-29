#!/usr/bin/env python3
"""
Test TripGenie with realistic dates (2-3 months out)
This should work if date range is the issue
"""

import json
from datetime import datetime, timedelta
from app.tools.amadeus_flight_tool import AmadeusFlightTool

def test_tripgenie_with_good_dates():
    print("🧪 Testing TripGenie with realistic dates")
    print("-" * 40)
    
    # Use dates 2-3 months out (sweet spot for test environment)
    departure_date = (datetime.now() + timedelta(days=75)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=82)).strftime("%Y-%m-%d")
    
    print(f"Using dates: {departure_date} to {return_date}")
    print("(Instead of your original 2025-07-15 to 2025-07-21)")
    
    # Test with your exact same user setup but realistic dates
    test_input = {
        "flight_groups": [
            {
                "departure_city": "LAX",
                "passenger_count": 1,
                "destinations": ["MAD"],  # Madrid - same as your original
                "departure_date": departure_date,
                "return_date": return_date,
                "passengers": ["royal11004@gmail.com"],
                "passenger_names": ["User 1"]
            },
            {
                "departure_city": "JFK", 
                "passenger_count": 1,
                "destinations": ["MAD"],
                "departure_date": departure_date,
                "return_date": return_date,
                "passengers": ["rayabarapu.a@northeastern.edu"],
                "passenger_names": ["User 2"]
            },
            {
                "departure_city": "BOS",
                "passenger_count": 1, 
                "destinations": ["MAD"],
                "departure_date": departure_date,
                "return_date": return_date,
                "passengers": ["aashiq.raya@gmail.com"],
                "passenger_names": ["User 3"]
            }
        ],
        "flight_preferences": {
            "travel_class": "economy",
            "nonstop_preferred": False
        }
    }
    
    tool = AmadeusFlightTool()
    result_str = tool._call(json.dumps(test_input, indent=2))
    
    try:
        result = json.loads(result_str)
        
        print("\n📊 Results:")
        
        # Check search summary
        if "search_summary" in result:
            summary = result["search_summary"]
            print(f"✅ Search Summary: {summary}")
        
        # Count successful flights
        successful_groups = 0
        total_cost = 0
        
        for group_key, group_data in result.items():
            if group_key in ["flight_search_status", "errors_encountered", "search_summary"]:
                continue
                
            print(f"\n🛫 Group: {group_key}")
            
            if "MAD" in group_data:
                mad_flights = group_data["MAD"]
                if isinstance(mad_flights, list) and mad_flights:
                    print(f"   ✅ Found {len(mad_flights)} Madrid flights!")
                    cheapest = min(mad_flights, key=lambda x: x.get('total_price', float('inf')))
                    price = cheapest.get('total_price', 0)
                    airline = cheapest.get('airline', 'Unknown')
                    print(f"   💰 Cheapest: ${price} on {airline}")
                    successful_groups += 1
                    total_cost += price
                elif isinstance(mad_flights, dict) and "error" in mad_flights:
                    print(f"   ❌ Error: {mad_flights['error']}")
                else:
                    print(f"   ❌ No flights found")
            else:
                print(f"   ❌ No Madrid data in response")
        
        print(f"\n🎯 FINAL RESULT:")
        print(f"   Successful flight groups: {successful_groups}/3")
        print(f"   Total flight cost: ${total_cost}")
        
        if successful_groups > 0:
            print(f"   🎉 SUCCESS! This would fix your TripGenie app!")
            print(f"   👉 The issue is your original dates were too far out (2025-07-15)")
        else:
            print(f"   😞 Still no flights found - issue might be elsewhere")
            
        return successful_groups > 0
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Raw result: {result_str}")
        return False

if __name__ == "__main__":
    test_tripgenie_with_good_dates() 