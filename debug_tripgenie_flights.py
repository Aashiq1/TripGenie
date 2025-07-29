#!/usr/bin/env python3
"""
Debug TripGenie Flight Search
Trace through the exact same logic your app uses to find the issue
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import your app's flight logic
from app.tools.amadeus_flight_tool import AmadeusFlightTool
from app.services.amadeus_flights import get_flight_offers

load_dotenv()

def test_direct_amadeus():
    """Test Amadeus service directly"""
    print("🔧 Step 1: Testing Amadeus service directly...")
    
    # Use dates that work (2-3 months out)
    departure_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=67)).strftime("%Y-%m-%d")
    
    print(f"   Dates: {departure_date} to {return_date}")
    
    result = get_flight_offers(
        departure_city="LAX",
        destination="MAD", 
        departure_date=departure_date,
        return_date=return_date,
        num_adults=1,
        travel_class="ECONOMY",
        nonstop_only=False
    )
    
    print(f"   Result type: {type(result)}")
    if isinstance(result, list) and result:
        print(f"   ✅ Found {len(result)} flights!")
        print(f"   Cheapest: ${result[0].get('total_price', 'N/A')}")
        return True
    elif isinstance(result, dict) and 'error' in result:
        print(f"   ❌ Error: {result['error']}")
        return False
    else:
        print(f"   ❌ Unexpected result: {result}")
        return False

def test_flight_tool():
    """Test the AmadeusFlightTool wrapper"""
    print("\n🛠️ Step 2: Testing AmadeusFlightTool...")
    
    tool = AmadeusFlightTool()
    
    # Use good dates
    departure_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=67)).strftime("%Y-%m-%d")
    
    test_input = {
        "flight_groups": [
            {
                "departure_city": "LAX",
                "passenger_count": 1,
                "destinations": ["MAD"],
                "departure_date": departure_date,
                "return_date": return_date
            }
        ],
        "flight_preferences": {
            "travel_class": "economy",
            "nonstop_preferred": False
        }
    }
    
    print(f"   Input: {json.dumps(test_input, indent=2)}")
    
    result_str = tool._call(json.dumps(test_input))
    
    try:
        result = json.loads(result_str)
        print(f"   ✅ Tool executed successfully")
        
        # Check for flight data
        for group_key, group_data in result.items():
            if group_key in ["flight_search_status", "errors_encountered", "search_summary"]:
                continue
                
            if "MAD" in group_data:
                mad_flights = group_data["MAD"]
                if isinstance(mad_flights, list) and mad_flights:
                    print(f"   ✅ Found {len(mad_flights)} Madrid flights in group {group_key}")
                    return True
                elif isinstance(mad_flights, dict) and "error" in mad_flights:
                    print(f"   ❌ Madrid search error: {mad_flights['error']}")
                    return False
        
        print(f"   ❌ No Madrid flights found in tool result")
        print(f"   Full result: {json.dumps(result, indent=2)}")
        return False
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON decode error: {e}")
        print(f"   Raw result: {result_str}")
        return False

def test_original_dates():
    """Test with the original problematic dates"""
    print("\n📅 Step 3: Testing with original dates (2025-07-15)...")
    
    tool = AmadeusFlightTool()
    
    # Use the EXACT dates from your original request
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
    
    print(f"   Testing exact original dates: 2025-07-15 to 2025-07-21")
    
    result_str = tool._call(json.dumps(test_input))
    
    try:
        result = json.loads(result_str)
        
        # Check search summary
        if "search_summary" in result:
            summary = result["search_summary"]
            print(f"   Search Summary: {summary}")
        
        # Check flight search status
        if "flight_search_status" in result:
            status = result["flight_search_status"]
            print(f"   Status: {status.get('status', 'Unknown')}")
            print(f"   Message: {status.get('message', 'No message')}")
        
        # Look for actual flight data
        flights_found = False
        for group_key, group_data in result.items():
            if group_key in ["flight_search_status", "errors_encountered", "search_summary"]:
                continue
                
            if "MAD" in group_data:
                mad_flights = group_data["MAD"]
                if isinstance(mad_flights, list) and mad_flights:
                    print(f"   ✅ Found {len(mad_flights)} Madrid flights with original dates!")
                    flights_found = True
                elif isinstance(mad_flights, dict) and "error" in mad_flights:
                    print(f"   ❌ Error with original dates: {mad_flights['error']}")
        
        if not flights_found:
            print(f"   ❌ No flights found with original dates")
            print(f"   → This explains your app's behavior!")
            
        return flights_found
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON decode error: {e}")
        return False

def test_multi_group():
    """Test with multiple departure cities like your original request"""
    print("\n👥 Step 4: Testing multi-group scenario...")
    
    tool = AmadeusFlightTool()
    
    # Use good dates but multiple cities (like your original request)
    departure_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=67)).strftime("%Y-%m-%d")
    
    test_input = {
        "flight_groups": [
            {
                "departure_city": "LAX",
                "passenger_count": 1,
                "destinations": ["MAD"],
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
    
    print(f"   Testing 3 departure cities: LAX, JFK, BOS → MAD")
    
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
            if "MAD" in group_data:
                mad_flights = group_data["MAD"]
                if isinstance(mad_flights, list) and mad_flights:
                    print(f"   ✅ {group_key}: Found {len(mad_flights)} flights")
                    successful_groups += 1
                else:
                    print(f"   ❌ {group_key}: No flights found")
        
        print(f"   Result: {successful_groups}/{total_groups} groups found flights")
        
        if successful_groups == 0:
            print(f"   → This might be why your app shows 0 total flights!")
            
        return successful_groups > 0
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON decode error: {e}")
        return False

def main():
    print("🔍 TripGenie Flight Search Debug")
    print("=" * 50)
    
    # Test each step
    step1_ok = test_direct_amadeus()
    step2_ok = test_flight_tool() 
    step3_ok = test_original_dates()
    step4_ok = test_multi_group()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DEBUG SUMMARY")
    print("=" * 50)
    
    print(f"✅ Direct Amadeus API: {'PASS' if step1_ok else 'FAIL'}")
    print(f"✅ Flight Tool (good dates): {'PASS' if step2_ok else 'FAIL'}")
    print(f"✅ Original dates (2025-07-15): {'PASS' if step3_ok else 'FAIL'}")
    print(f"✅ Multi-group search: {'PASS' if step4_ok else 'FAIL'}")
    
    print("\n💡 DIAGNOSIS:")
    if not step3_ok:
        print("   🎯 FOUND THE ISSUE: Your original dates (2025-07-15) are too far out!")
        print("   → Amadeus test environment doesn't have data that far ahead")
        print("   → Use dates 2-3 months in the future instead")
    elif not step4_ok:
        print("   🎯 FOUND THE ISSUE: Multi-group search is failing!")
        print("   → Some departure cities don't have Madrid routes")
        print("   → App should handle partial failures better")
    else:
        print("   ✅ All tests pass - the issue might be elsewhere in your app")

if __name__ == "__main__":
    main() 