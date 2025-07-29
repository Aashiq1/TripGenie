#!/usr/bin/env python3
"""
Quick Amadeus Test - Just check if your credentials work
"""

import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv

load_dotenv()

def quick_test():
    print("🔧 Quick Amadeus API Test")
    print("-" * 30)
    
    # Check credentials
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ Missing credentials in .env file!")
        print("Add these lines to your .env file:")
        print("AMADEUS_CLIENT_ID=your_client_id")
        print("AMADEUS_CLIENT_SECRET=your_client_secret")
        return
    
    print(f"✅ Found credentials (Client ID: {client_id[:8]}...)")
    
    try:
        # Create client
        amadeus = Client(
            client_id=client_id,
            client_secret=client_secret,
            hostname='test'
        )
        
        # Test 1: Simple airport lookup
        print("\n🔍 Test 1: Airport lookup...")
        response = amadeus.reference_data.locations.get(keyword='LAX', subType='AIRPORT')
        if response.data:
            print(f"✅ Airport lookup works! Found: {response.data[0]['name']}")
        else:
            print("❌ Airport lookup failed")
            
        # Test 2: Simple flight search (route that usually works)
        print("\n✈️ Test 2: Flight search (LAX to JFK)...")
        from datetime import datetime, timedelta
        
        departure = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        return_date = (datetime.now() + timedelta(days=67)).strftime("%Y-%m-%d")
        
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode="LAX",
            destinationLocationCode="JFK",
            departureDate=departure,
            returnDate=return_date,
            adults=1,
            max=3
        )
        
        if response.data:
            print(f"✅ Flight search works! Found {len(response.data)} flights")
            cheapest = min(response.data, key=lambda x: float(x['price']['total']))
            print(f"   Cheapest: ${cheapest['price']['total']} ({cheapest['validatingAirlineCodes'][0]})")
        else:
            print("❌ No flights found (this is normal for test environment)")
            
        # Test 3: Madrid specifically
        print("\n🇪🇸 Test 3: Madrid flights (LAX to MAD)...")
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode="LAX",
            destinationLocationCode="MAD",
            departureDate=departure,
            returnDate=return_date,
            adults=1,
            max=3
        )
        
        if response.data:
            print(f"✅ Madrid flights available! Found {len(response.data)} options")
        else:
            print("❌ No Madrid flights found")
            print("   → This explains why your app returns 0 flights for Madrid")
            
    except ResponseError as e:
        print(f"❌ API Error: {e}")
        if "Invalid credentials" in str(e):
            print("   → Check your AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET")
        elif "Unauthorized" in str(e):
            print("   → Your credentials might be expired or inactive")
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("   → Check your internet connection")

if __name__ == "__main__":
    quick_test() 