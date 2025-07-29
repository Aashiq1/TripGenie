#!/usr/bin/env python3
"""
Debug July 2025 Flight Search
Test the exact dates the user needs vs longer-term dates
Current date: July 11, 2025
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

from app.tools.amadeus_flight_tool import AmadeusFlightTool
from app.services.amadeus_flights import get_flight_offers

load_dotenv()

def test_exact_user_dates():
    """Test the user's exact dates: July 15-21, 2025 (4-10 days from now)"""
    print("📅 Testing User's EXACT Dates (July 15-21, 2025)")
    print("-" * 50)
    print("   Today: July 11, 2025")
    print("   Departure: July 15, 2025 (4 days from now)")
    print("   Return: July 21, 2025 (10 days from now)")
    
    # Test direct API first
    print("\n🔧 Step 1: Direct Amadeus API...")
    result = get_flight_offers(
        departure_city="LAX",
        destination="MAD", 
        departure_date="2025-07-15",
        return_date="2025-07-21",
        num_adults=1,
        travel_class="ECONOMY",
        nonstop_only=False
    )
    
    if isinstance(result, list) and result:
        print(f"   ✅ Direct API works! Found {len(result)} flights")
        print(f"   Cheapest: ${result[0].get('total_price', 'N/A')}")
    elif isinstance(result, dict) and 'error' in result:
        print(f"   ❌ Direct API error: {result['error']}")
    else:
        print(f"   ❌ Direct API: No flights found")
    
    # Test with flight tool
    print("\n🛠️ Step 2: AmadeusFlightTool...")
    tool = AmadeusFlightTool()
    
    test_input = {
        "flight_groups": [
            {
                "departure_city": "LAX",
                "passenger_count": 1,
                "destinations": ["MAD"],
                "departure_date": "2025-07-15",
                "return_date": "2025-07-21"
            }
        ],
        "flight_preferences": {
            "travel_class": "economy",
            "nonstop_preferred": False
        }
    }
    
    result_str = tool._call(json.dumps(test_input))
    try:
        result = json.loads(result_str)
        
        flights_found = False
        for group_key, group_data in result.items():
            if group_key in ["flight_search_status", "errors_encountered", "search_summary"]:
                continue
                
            if "MAD" in group_data:
                mad_flights = group_data["MAD"]
                if isinstance(mad_flights, list) and mad_flights:
                    print(f"   ✅ Tool works! Found {len(mad_flights)} Madrid flights")
                    flights_found = True
                elif isinstance(mad_flights, dict) and "error" in mad_flights:
                    print(f"   ❌ Tool error: {mad_flights['error']}")
        
        if not flights_found:
            print("   ❌ No flights in tool result")
            
        return flights_found
        
    except json.JSONDecodeError as e:
        print(f"   ❌ Tool JSON error: {e}")
        return False

def test_longer_term_dates():
    """Test dates further out (like what worked in quick test)"""
    print("\n📅 Testing Longer-Term Dates (September 2025)")
    print("-" * 50)
    
    # Calculate dates similar to what worked in quick test
    # (60-70 days from July 11, 2025 = September 2025)
    departure_date = "2025-09-15"  # ~65 days from July 11
    return_date = "2025-09-22"     # ~72 days from July 11
    
    print(f"   Departure: {departure_date} (~65 days from now)")
    print(f"   Return: {return_date} (~72 days from now)")
    
    # Test direct API
    print("\n🔧 Direct Amadeus API...")
    result = get_flight_offers(
        departure_city="LAX",
        destination="MAD", 
        departure_date=departure_date,
        return_date=return_date,
        num_adults=1,
        travel_class="ECONOMY",
        nonstop_only=False
    )
    
    if isinstance(result, list) and result:
        print(f"   ✅ Direct API works! Found {len(result)} flights")
        print(f"   Cheapest: ${result[0].get('total_price', 'N/A')}")
        return True
    elif isinstance(result, dict) and 'error' in result:
        print(f"   ❌ Direct API error: {result['error']}")
        return False
    else:
        print(f"   ❌ Direct API: No flights found")
        return False

def test_multi_group_july():
    """Test multi-group search with July dates (user's exact scenario)"""
    print("\n👥 Testing Multi-Group July Dates (User's Exact Scenario)")
    print("-" * 50)
    
    tool = AmadeusFlightTool()
    
    # User's exact scenario: 3 cities, July 15-21, 2025
    test_input = {
        "flight_groups": [
            {
                "departure_city": "LAX",
                "passenger_count": 1,
                "destinations": ["MAD"],
                "departure_date": "2025-07-15",
                "return_date": "2025-07-21",
                "passengers": ["royal11004@gmail.com"],
                "passenger_names": ["User 1"]
            },
            {
                "departure_city": "JFK", 
                "passenger_count": 1,
                "destinations": ["MAD"],
                "departure_date": "2025-07-15",
                "return_date": "2025-07-21",
                "passengers": ["rayabarapu.a@northeastern.edu"],
                "passenger_names": ["User 2"]
            },
            {
                "departure_city": "BOS",
                "passenger_count": 1, 
                "destinations": ["MAD"],
                "departure_date": "2025-07-15",
                "return_date": "2025-07-21",
                "passengers": ["aashiq.raya@gmail.com"],
                "passenger_names": ["User 3"]
            }
        ],
        "flight_preferences": {
            "travel_class": "economy",
            "nonstop_preferred": False
        }
    }
    
    print("   Testing: LAX, JFK, BOS → MAD on July 15-21, 2025")
    
    result_str = tool._call(json.dumps(test_input))
    
    try:
        result = json.loads(result_str)
        
        # Check each group
        successful_groups = 0
        total_groups = 0
        
        for group_key, group_data in result.items():
            if group_key in ["flight_search_status", "errors_encountered", "search_summary"]:
                continue
                
            total_groups += 1
            print(f"\n🛫 Group: {group_key}")
            
            if "MAD" in group_data:
                mad_flights = group_data["MAD"]
                if isinstance(mad_flights, list) and mad_flights:
                    print(f"   ✅ Found {len(mad_flights)} flights")
                    cheapest = min(mad_flights, key=lambda x: x.get('total_price', float('inf')))
                    price = cheapest.get('total_price', 0)
                    print(f"   💰 Cheapest: ${price}")
                    successful_groups += 1
                elif isinstance(mad_flights, dict) and "error" in mad_flights:
                    print(f"   ❌ Error: {mad_flights['error']}")
                else:
                    print(f"   ❌ No flights found")
            else:
                print(f"   ❌ No MAD data")
        
        print(f"\n📊 Result: {successful_groups}/{total_groups} groups found flights")
        
        if successful_groups == 0:
            print("   🎯 This matches your app's behavior - 0 total flights!")
        
        return successful_groups > 0
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON error: {e}")
        return False

def test_date_comparison():
    """Compare multiple date ranges to see what works"""
    print("\n📊 Date Range Comparison Test")
    print("-" * 50)
    
    date_ranges = [
        ("2025-07-15", "2025-07-21", "User's dates (4-10 days out)"),
        ("2025-07-25", "2025-08-01", "2-3 weeks out"),
        ("2025-08-15", "2025-08-22", "1 month out"),
        ("2025-09-15", "2025-09-22", "2 months out"),
        ("2025-10-15", "2025-10-22", "3 months out"),
    ]
    
    working_ranges = []
    
    for departure, return_date, description in date_ranges:
        print(f"\n📅 Testing: {description}")
        print(f"   Dates: {departure} to {return_date}")
        
        result = get_flight_offers(
            departure_city="LAX",
            destination="MAD", 
            departure_date=departure,
            return_date=return_date,
            num_adults=1,
            travel_class="ECONOMY",
            nonstop_only=False
        )
        
        if isinstance(result, list) and result:
            print(f"   ✅ Found {len(result)} flights")
            working_ranges.append((departure, description))
        else:
            print(f"   ❌ No flights found")
    
    return working_ranges

def main():
    print("🕐 TripGenie July 2025 Debug")
    print("Current Date: July 11, 2025")
    print("=" * 60)
    
    # Test user's exact dates
    july_works = test_exact_user_dates()
    
    # Test longer term dates
    september_works = test_longer_term_dates()
    
    # Test multi-group scenario
    multi_july_works = test_multi_group_july()
    
    # Compare date ranges
    working_ranges = test_date_comparison()
    
    # Analysis
    print("\n" + "=" * 60)
    print("🔍 ANALYSIS")
    print("=" * 60)
    
    print(f"✅ July 15-21 (user dates): {'WORKS' if july_works else 'FAILS'}")
    print(f"✅ September dates: {'WORKS' if september_works else 'FAILS'}")  
    print(f"✅ Multi-group July: {'WORKS' if multi_july_works else 'FAILS'}")
    
    if working_ranges:
        print(f"\n📅 Working date ranges:")
        for date, desc in working_ranges:
            print(f"   • {desc}")
    
    print(f"\n💡 CONCLUSION:")
    if not july_works and september_works:
        print("   🎯 ISSUE: Amadeus test environment doesn't have near-term data!")
        print("   📝 July 15-21 is too close (4-10 days out)")
        print("   📝 September dates work better (2+ months out)")
        print("   🛠️ Solution: Use production Amadeus or test with future dates")
    elif july_works and not multi_july_works:
        print("   🎯 ISSUE: Single searches work, multi-group searches fail!")
        print("   📝 LAX→MAD works alone but fails in group")
        print("   🛠️ Solution: Fix multi-group search logic")
    elif not july_works and not september_works:
        print("   🎯 ISSUE: Madrid routes not available in test environment")
        print("   🛠️ Solution: Try different destinations or production API")
    else:
        print("   ✅ All tests work - issue must be elsewhere in app")

if __name__ == "__main__":
    main() 