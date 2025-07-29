#!/usr/bin/env python3
"""
Quick test to validate date theory
Compare July 15-21 (user's dates) vs September dates
"""

from app.services.amadeus_flights import get_flight_offers

def quick_date_comparison():
    print("🔍 Quick Date Theory Validation")
    print("Current Date: July 11, 2025")
    print("=" * 40)
    
    # Test 1: User's actual dates (July 15-21, 2025)
    print("\n📅 Test 1: User's dates (July 15-21)")
    print("   4-10 days from now")
    
    result1 = get_flight_offers(
        departure_city="LAX",
        destination="MAD",
        departure_date="2025-07-15",
        return_date="2025-07-21",
        num_adults=1
    )
    
    if isinstance(result1, list) and result1:
        print(f"   ✅ SUCCESS: Found {len(result1)} flights")
        print(f"   💰 Price: ${result1[0].get('total_price', 'N/A')}")
        july_works = True
    else:
        print(f"   ❌ FAILED: No flights found")
        if isinstance(result1, dict) and 'error' in result1:
            print(f"   📝 Error: {result1['error']}")
        july_works = False
    
    # Test 2: September dates (like what worked before)
    print("\n📅 Test 2: September dates (like quick test)")
    print("   ~65 days from now")
    
    result2 = get_flight_offers(
        departure_city="LAX",
        destination="MAD",
        departure_date="2025-09-15",
        return_date="2025-09-22",
        num_adults=1
    )
    
    if isinstance(result2, list) and result2:
        print(f"   ✅ SUCCESS: Found {len(result2)} flights")
        print(f"   💰 Price: ${result2[0].get('total_price', 'N/A')}")
        september_works = True
    else:
        print(f"   ❌ FAILED: No flights found")
        if isinstance(result2, dict) and 'error' in result2:
            print(f"   📝 Error: {result2['error']}")
        september_works = False
    
    # Analysis
    print("\n" + "=" * 40)
    print("🎯 THEORY VALIDATION:")
    
    if not july_works and september_works:
        print("✅ THEORY CONFIRMED!")
        print("   📝 July dates (near-term): FAIL")
        print("   📝 September dates (long-term): SUCCESS")
        print("   🔍 Amadeus test env doesn't have near-term data")
        print("\n💡 SOLUTION:")
        print("   • Use production Amadeus API")
        print("   • Or test with future dates (2+ months out)")
        
    elif july_works and september_works:
        print("❓ THEORY INCORRECT")
        print("   📝 Both date ranges work")
        print("   🔍 Issue must be in multi-group logic")
        
    elif not july_works and not september_works:
        print("❓ THEORY INCORRECT") 
        print("   📝 No Madrid flights in test environment")
        print("   🔍 Route availability issue")
        
    else:  # july works, september doesn't
        print("❓ UNEXPECTED RESULT")
        print("   📝 Near-term works but long-term doesn't")

if __name__ == "__main__":
    quick_date_comparison() 