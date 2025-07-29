#!/usr/bin/env python3
"""
Debug Multi-Group Search Issue
We know single searches work, so let's test multi-group step by step
"""

import json
from app.tools.amadeus_flight_tool import AmadeusFlightTool
from app.services.amadeus_flights import get_flight_offers

def test_each_city_individually():
    """Test each departure city individually (we know LAX works)"""
    print("🏙️ Testing Each City Individually")
    print("=" * 40)
    
    cities = ["LAX", "JFK", "BOS"]
    results = {}
    
    for city in cities:
        print(f"\n📍 Testing {city} → MAD")
        
        result = get_flight_offers(
            departure_city=city,
            destination="MAD",
            departure_date="2025-07-15",
            return_date="2025-07-21",
            num_adults=1
        )
        
        if isinstance(result, list) and result:
            print(f"   ✅ SUCCESS: Found {len(result)} flights")
            price = result[0].get('total_price', 0)
            print(f"   💰 Cheapest: ${price}")
            results[city] = "SUCCESS"
        else:
            print(f"   ❌ FAILED: No flights")
            if isinstance(result, dict) and 'error' in result:
                print(f"   📝 Error: {result['error']}")
            results[city] = "FAILED"
    
    return results

def test_amadeus_flight_tool_single():
    """Test AmadeusFlightTool with single group"""
    print("\n🛠️ Testing AmadeusFlightTool - Single Group")
    print("=" * 40)
    
    tool = AmadeusFlightTool()
    
    # Test with just LAX (we know this works with direct API)
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
    
    print("   Testing: Single group (LAX only)")
    
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
                    print(f"   ✅ Tool SUCCESS: Found {len(mad_flights)} flights")
                    flights_found = True
                elif isinstance(mad_flights, dict) and "error" in mad_flights:
                    print(f"   ❌ Tool error: {mad_flights['error']}")
        
        if not flights_found:
            print("   ❌ Tool FAILED: No flights in result")
            print(f"   📄 Full result: {json.dumps(result, indent=2)}")
            
        return flights_found
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON decode error: {e}")
        print(f"   📄 Raw result: {result_str}")
        return False

def test_amadeus_flight_tool_multi():
    """Test AmadeusFlightTool with multiple groups (your exact scenario)"""
    print("\n👥 Testing AmadeusFlightTool - Multi Group (Your Exact Scenario)")
    print("=" * 40)
    
    tool = AmadeusFlightTool()
    
    # Your exact scenario: 3 cities
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
    
    print("   Testing: LAX, JFK, BOS → MAD (July 15-21)")
    
    result_str = tool._call(json.dumps(test_input))
    
    try:
        result = json.loads(result_str)
        
        print("\n📊 Multi-Group Results:")
        
        # Check search summary
        if "search_summary" in result:
            summary = result["search_summary"]
            print(f"   📈 Search Summary: {summary}")
        
        # Check for overall status
        if "flight_search_status" in result:
            status = result["flight_search_status"]
            print(f"   📋 Status: {status.get('status', 'Unknown')}")
            if "message" in status:
                print(f"   📝 Message: {status['message']}")
        
        # Check each group
        successful_groups = 0
        total_groups = 0
        group_details = {}
        
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
                    airline = cheapest.get('airline', 'Unknown')
                    print(f"   💰 Cheapest: ${price} on {airline}")
                    successful_groups += 1
                    group_details[group_key] = "SUCCESS"
                elif isinstance(mad_flights, dict) and "error" in mad_flights:
                    print(f"   ❌ Error: {mad_flights['error']}")
                    group_details[group_key] = f"ERROR: {mad_flights['error']}"
                else:
                    print(f"   ❌ No flights found")
                    group_details[group_key] = "NO_FLIGHTS"
            else:
                print(f"   ❌ No MAD data in response")
                group_details[group_key] = "NO_MAD_DATA"
        
        print(f"\n📊 FINAL MULTI-GROUP RESULT:")
        print(f"   Successful groups: {successful_groups}/{total_groups}")
        
        if successful_groups == 0:
            print(f"   🎯 THIS MATCHES YOUR APP'S BEHAVIOR!")
            print(f"   📝 0 successful groups = 0 total flight cost")
        
        return successful_groups, total_groups, group_details
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON decode error: {e}")
        print(f"   📄 Raw result: {result_str}")
        return 0, 0, {}

def diagnose_multigroup_failure(group_details):
    """Analyze what went wrong in multi-group search"""
    print("\n🔬 DIAGNOSIS")
    print("=" * 40)
    
    success_count = sum(1 for status in group_details.values() if status == "SUCCESS")
    
    if success_count == 0:
        print("🚨 ALL GROUPS FAILED")
        
        # Check failure patterns
        error_count = sum(1 for status in group_details.values() if "ERROR" in status)
        no_flights_count = sum(1 for status in group_details.values() if status == "NO_FLIGHTS")
        no_data_count = sum(1 for status in group_details.values() if status == "NO_MAD_DATA")
        
        print(f"   📊 Failure breakdown:")
        print(f"   • Errors: {error_count}")
        print(f"   • No flights found: {no_flights_count}")  
        print(f"   • No MAD data: {no_data_count}")
        
        if error_count > 0:
            print("\n💡 LIKELY ISSUE: API errors in multi-group requests")
            print("   🛠️ Solution: Add retry logic or rate limiting")
        elif no_flights_count > 0:
            print("\n💡 LIKELY ISSUE: Some routes don't exist (JFK/BOS → MAD)")
            print("   🛠️ Solution: Handle partial results gracefully")
        else:
            print("\n💡 LIKELY ISSUE: Tool logic error in multi-group processing")
    
    elif success_count < len(group_details):
        print(f"🟡 PARTIAL SUCCESS: {success_count}/{len(group_details)} groups worked")
        print("   📝 Your app might be expecting ALL groups to succeed")
        print("   🛠️ Solution: Accept partial results and continue planning")
    
    else:
        print("✅ ALL GROUPS SUCCEEDED - Issue must be elsewhere")

def main():
    print("🔍 Multi-Group Search Debug")
    print("Current Date: July 11, 2025")
    print("User Trip: July 15-21, 2025")
    print("=" * 50)
    
    # Test individual cities
    individual_results = test_each_city_individually()
    
    # Test single group through tool
    single_tool_works = test_amadeus_flight_tool_single()
    
    # Test multi-group through tool  
    successful_groups, total_groups, group_details = test_amadeus_flight_tool_multi()
    
    # Diagnose issues
    diagnose_multigroup_failure(group_details)
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    print(f"✅ Individual city searches: {list(individual_results.values())}")
    print(f"✅ Single group tool: {'WORKS' if single_tool_works else 'FAILS'}")
    print(f"✅ Multi-group tool: {successful_groups}/{total_groups} groups successful")
    
    print("\n🎯 ROOT CAUSE:")
    if all(status == "SUCCESS" for status in individual_results.values()) and not single_tool_works:
        print("   🔧 Issue in AmadeusFlightTool wrapper logic")
    elif single_tool_works and successful_groups == 0:
        print("   👥 Issue in multi-group processing logic")
    elif successful_groups < total_groups:
        print(f"   🛣️ Some routes don't work: {group_details}")
    else:
        print("   ❓ Issue must be in planner or agent logic")

if __name__ == "__main__":
    main() 