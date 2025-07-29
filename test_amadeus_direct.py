#!/usr/bin/env python3
"""
Direct Amadeus API Test Script
Run this to test your Amadeus credentials and see what data is available
"""

import os
from datetime import datetime, timedelta
from amadeus import Client, ResponseError

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_amadeus_connection():
    """Test if Amadeus API credentials work"""
    print("🔧 Testing Amadeus API Connection...")
    
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ ERROR: Missing Amadeus credentials!")
        print("   Make sure you have AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in your .env file")
        return None
    
    print(f"✅ Found credentials (ID: {client_id[:8]}...)")
    
    try:
        amadeus = Client(
            client_id=client_id,
            client_secret=client_secret,
            hostname='test'  # Using test environment
        )
        
        # Test a simple API call
        print("🔍 Testing API connection with airport lookup...")
        response = amadeus.reference_data.locations.get(
            keyword='MAD',
            subType='AIRPORT'
        )
        
        if response.data:
            print(f"✅ API Connection works! Found {len(response.data)} results for MAD")
            for airport in response.data[:3]:
                print(f"   {airport['iataCode']}: {airport['name']}")
        else:
            print("⚠️ API works but no airport data found")
            
        return amadeus
        
    except ResponseError as e:
        print(f"❌ API Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def test_popular_routes(amadeus):
    """Test some routes that usually work in Amadeus test environment"""
    print("\n🛫 Testing Popular Routes (These usually work in test env)...")
    
    # Calculate dates 2-3 months in future (test env sweet spot)
    departure_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=67)).strftime("%Y-%m-%d")
    
    # Routes that often work in test environment
    test_routes = [
        ("JFK", "LAX", "New York to Los Angeles"),
        ("LAX", "CDG", "Los Angeles to Paris"),
        ("JFK", "LHR", "New York to London"),
        ("LAX", "BCN", "Los Angeles to Barcelona"),
        ("JFK", "BCN", "New York to Barcelona"),
    ]
    
    working_routes = []
    
    for origin, dest, description in test_routes:
        print(f"\n📍 Testing: {description} ({origin} → {dest})")
        print(f"   Dates: {departure_date} to {return_date}")
        
        try:
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=dest,
                departureDate=departure_date,
                returnDate=return_date,
                adults=1,
                currencyCode="USD",
                max=5
            )
            
            if response.data:
                flight_count = len(response.data)
                cheapest = min(response.data, key=lambda x: float(x['price']['total']))
                price = cheapest['price']['total']
                airline = cheapest['validatingAirlineCodes'][0]
                
                print(f"   ✅ Found {flight_count} flights! Cheapest: ${price} on {airline}")
                working_routes.append((origin, dest, description, price))
            else:
                print(f"   ❌ No flights found")
                
        except ResponseError as e:
            print(f"   ❌ API Error: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return working_routes

def test_madrid_specifically(amadeus):
    """Test Madrid routes specifically"""
    print("\n🇪🇸 Testing Madrid (MAD) Routes Specifically...")
    
    departure_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=67)).strftime("%Y-%m-%d")
    
    # Common US cities to Madrid
    us_cities = ["LAX", "JFK", "BOS", "MIA", "ORD", "SFO"]
    
    madrid_results = []
    
    for city in us_cities:
        print(f"\n📍 Testing: {city} → MAD (Madrid)")
        
        try:
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode=city,
                destinationLocationCode="MAD",
                departureDate=departure_date,
                returnDate=return_date,
                adults=1,
                currencyCode="USD",
                max=5
            )
            
            if response.data:
                flight_count = len(response.data)
                cheapest = min(response.data, key=lambda x: float(x['price']['total']))
                price = cheapest['price']['total']
                airline = cheapest['validatingAirlineCodes'][0]
                
                print(f"   ✅ Found {flight_count} flights! Cheapest: ${price} on {airline}")
                madrid_results.append((city, price, airline))
            else:
                print(f"   ❌ No flights found")
                
        except ResponseError as e:
            print(f"   ❌ API Error: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return madrid_results

def test_different_dates(amadeus):
    """Test how date ranges affect results"""
    print("\n📅 Testing Different Date Ranges...")
    
    # Test different date ranges
    date_ranges = [
        (30, "1 month out"),
        (60, "2 months out"),
        (90, "3 months out"),
        (120, "4 months out"),
        (180, "6 months out"),
    ]
    
    for days_ahead, description in date_ranges:
        departure_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        return_date = (datetime.now() + timedelta(days=days_ahead + 7)).strftime("%Y-%m-%d")
        
        print(f"\n📅 Testing {description}: {departure_date}")
        
        try:
            response = amadeus.shopping.flight_offers_search.get(
                originLocationCode="LAX",
                destinationLocationCode="BCN",  # Barcelona usually works
                departureDate=departure_date,
                returnDate=return_date,
                adults=1,
                currencyCode="USD",
                max=3
            )
            
            if response.data:
                print(f"   ✅ Found {len(response.data)} flights")
            else:
                print(f"   ❌ No flights found")
                
        except ResponseError as e:
            print(f"   ❌ API Error: {e}")

def main():
    print("🚀 Amadeus API Direct Test")
    print("=" * 50)
    
    # Test connection
    amadeus = test_amadeus_connection()
    if not amadeus:
        print("\n❌ Cannot proceed without working API connection")
        return
    
    # Test popular routes
    working_routes = test_popular_routes(amadeus)
    
    # Test Madrid specifically
    madrid_results = test_madrid_specifically(amadeus)
    
    # Test different dates
    test_different_dates(amadeus)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    if working_routes:
        print(f"✅ Found {len(working_routes)} working routes:")
        for origin, dest, desc, price in working_routes:
            print(f"   • {desc}: ${price}")
    else:
        print("❌ No working routes found in test environment")
    
    if madrid_results:
        print(f"\n✅ Madrid flights available from {len(madrid_results)} cities:")
        for city, price, airline in madrid_results:
            print(f"   • {city}: ${price} on {airline}")
    else:
        print("\n❌ No Madrid flights found from tested US cities")
        print("   This is likely why your app returns 0 flights for Madrid")
    
    print("\n💡 RECOMMENDATIONS:")
    if not madrid_results:
        print("   • Madrid (MAD) is not available in Amadeus test environment")
        print("   • Try Barcelona (BCN) or Paris (CDG) instead")
        print("   • Use dates 2-3 months in the future")
        print("   • Consider upgrading to Amadeus production environment")
    
    if working_routes:
        print("   • Use these working routes for testing your app")
        print("   • Stick to dates 1-4 months in advance")

if __name__ == "__main__":
    main() 