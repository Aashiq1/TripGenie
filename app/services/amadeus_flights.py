from amadeus import Client, ResponseError
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Initialize the Amadeus API client with credentials from environment variables
# Using test environment for development (change to production when ready)
amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET"),
    hostname='test'  # Use test environment (change to 'production' for real pricing with production credentials)
)

def get_flight_offers(
    departure_city: str, 
    destination: str, 
    departure_date: str, 
    return_date: str,
    num_adults: int = 1,  # Default 1, but will be overridden by group size
    travel_class: str = "ECONOMY",  # Default economy
    nonstop_only: bool = False  # Default allow connections
):
    """
    Fetch round-trip flight offers from Amadeus for a GROUP.
    
    Args:
        departure_city (str): Origin IATA code (e.g. 'LAX').
        destination (str): Destination IATA code (e.g. 'JFK').
        departure_date (str): Departure date in YYYY-MM-DD.
        return_date (str): Return date in YYYY-MM-DD.
        num_adults (int): Number of adult passengers in this group
        travel_class (str): ECONOMY, PREMIUM_ECONOMY, BUSINESS, or FIRST
        nonstop_only (bool): Whether to search only nonstop flights

    Returns:
        List[Dict]: List of flight offers with airline, price, and duration.
    """
    logger.info(f"Searching flights: {departure_city} -> {destination}, {departure_date} to {return_date}, {num_adults} adults, {travel_class}, nonstop_only: {nonstop_only}")
    
    try:
        # Build search parameters
        search_params = {
            "originLocationCode": departure_city,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "returnDate": return_date,
            "adults": num_adults,  # NOW USES ACTUAL GROUP SIZE
            "currencyCode": "USD",
            "max": 10  # Get more options for groups
        }
        
        # Add optional parameters
        if nonstop_only:
            search_params["nonStop"] = True
            
        if travel_class != "ECONOMY":
            search_params["travelClass"] = travel_class
        
        logger.debug(f"Search parameters: {search_params}")
        
        response = amadeus.shopping.flight_offers_search.get(**search_params)
        
        logger.info(f"API Response received. Data length: {len(response.data) if response.data else 0}")
        
        # Handle empty results
        if not response.data:
            logger.warning(f"No flights found for route {departure_city} -> {destination}")
            return _get_no_flights_response(departure_city, destination, departure_date, return_date, nonstop_only)

        flight_offers = []
        seen_flights = set()  # Track unique flights to avoid duplicates
        
        for offer in response.data:
            try:
                flight_info = {
                    "destination": destination,
                    "price_per_person": float(offer['price']['total']) / num_adults,
                    "total_price": float(offer['price']['total']),
                    "currency": offer['price']['currency'],
                    "airline": offer['validatingAirlineCodes'][0],
                    "duration": offer['itineraries'][0]['duration'],
                    "num_passengers": num_adults,
                    "departure_time": offer['itineraries'][0]['segments'][0]['departure']['at'],
                    "arrival_time": offer['itineraries'][0]['segments'][-1]['arrival']['at'],
                    "stops": len(offer['itineraries'][0]['segments']) - 1,
                    "flight_number": _extract_flight_number(offer['itineraries'][0]['segments'][0]),
                    "airline_code": offer['validatingAirlineCodes'][0],
                    "origin": departure_city
                }
                
                # Create unique key for this flight
                flight_key = (
                    flight_info['airline'], 
                    flight_info['departure_time'], 
                    flight_info['arrival_time'],
                    flight_info['stops']
                )
                
                # Only add if we haven't seen this exact flight before
                if flight_key not in seen_flights:
                    flight_offers.append(flight_info)
                    seen_flights.add(flight_key)
                    
            except (KeyError, IndexError, TypeError) as e:
                logger.error(f"Error parsing flight offer: {e}")
                continue
        
        logger.info(f"Successfully parsed {len(flight_offers)} flight offers")
        return flight_offers

    except ResponseError as e:
        logger.error(f"Amadeus API error: {e}")
        error_msg = str(e)
        
        # Handle specific common errors
        if "Invalid airport/city code" in error_msg:
            return _get_invalid_airport_response(departure_city, destination)
        elif "No results found" in error_msg:
            return _get_no_flights_response(departure_city, destination, departure_date, return_date, nonstop_only)
        elif "[500]" in error_msg or "500" in error_msg:
            # Amadeus test environment is down - provide mock data so system can continue
            logger.warning(f"Amadeus 500 error - providing mock flight data for {departure_city} -> {destination}")
            return _get_mock_flight_data(departure_city, destination, departure_date, return_date, num_adults)
        else:
            return {"error": f"Flight search failed: {error_msg}", "suggestions": _get_general_suggestions()}
    
    except Exception as e:
        logger.error(f"Unexpected error in flight search: {e}")
        # For any other error, also provide mock data to keep system working
        if "500" in str(e):
            return _get_mock_flight_data(departure_city, destination, departure_date, return_date, num_adults)
        return {"error": f"Unexpected error: {str(e)}", "suggestions": _get_general_suggestions()}

def _extract_flight_number(segment):
    """Extract flight number from segment data."""
    try:
        carrier_code = segment.get('carrierCode', '')
        flight_number = segment.get('number', '')
        return f"{carrier_code}{flight_number}" if carrier_code and flight_number else "Unknown"
    except:
        return "Unknown"

def _get_no_flights_response(departure_city, destination, departure_date, return_date, nonstop_only):
    """Generate helpful response when no flights are found."""
    suggestions = [
        "Try different dates (±3 days)",
        "Consider nearby airports",
        "Allow connecting flights" if nonstop_only else "Try direct flights only",
        f"Search manually on Google Flights: https://www.google.com/flights?q={departure_city}+to+{destination}"
    ]
    
    return {
        "error": f"No flights found from {departure_city} to {destination} for {departure_date} - {return_date}",
        "route": f"{departure_city} -> {destination}",
        "dates_searched": f"{departure_date} to {return_date}",
        "search_type": "nonstop only" if nonstop_only else "all flights",
        "suggestions": suggestions,
        "alternative_search_urls": [
            f"https://www.google.com/flights?q={departure_city}+to+{destination}",
            f"https://www.kayak.com/flights/{departure_city}-{destination}/{departure_date}/{return_date}",
            f"https://www.expedia.com/Flights-Search?trip=roundtrip&leg1=from:{departure_city},to:{destination},departure:{departure_date}&leg2=from:{destination},to:{departure_city},departure:{return_date}"
        ]
    }

def _get_invalid_airport_response(departure_city, destination):
    """Generate response for invalid airport codes."""
    return {
        "error": f"Invalid airport code: {departure_city} or {destination}",
        "suggestions": [
            "Verify airport codes are correct IATA codes (3 letters)",
            f"Common codes: LAX (Los Angeles), JFK (New York), MAD (Madrid), BCN (Barcelona)",
            "Try using city names instead of airport codes"
        ]
    }

def _get_general_suggestions():
    """General suggestions for flight search issues."""
    return [
        "Check if departure and destination codes are valid IATA codes",
        "Try searching with different date ranges",
        "Consider alternative nearby airports",
        "Use external flight search engines as backup"
    ]

def _get_mock_flight_data(departure_city: str, destination: str, departure_date: str, return_date: str, num_adults: int):
    """
    Provide mock flight data when Amadeus API is down.
    This allows the system to continue working for testing/demo purposes.
    """
    import random
    from datetime import datetime
    
    # Mock airlines by route
    airlines_by_route = {
        ("LAX", "MAD"): [("Turkish Airlines", "TK", 1291), ("Lufthansa", "LH", 1150), ("Air France", "AF", 1220)],
        ("JFK", "MAD"): [("Air Canada", "AC", 775), ("Iberia", "IB", 850), ("Delta", "DL", 920)],
        ("BOS", "MAD"): [("TAP Portugal", "TP", 711), ("British Airways", "BA", 780), ("Virgin Atlantic", "VS", 825)],
        ("LAX", "BCN"): [("Lufthansa", "LH", 950), ("Air France", "AF", 1020), ("KLM", "KL", 980)],
        ("JFK", "BCN"): [("Delta", "DL", 720), ("American Airlines", "AA", 780), ("United", "UA", 750)],
        ("BOS", "BCN"): [("Iberia", "IB", 650), ("Swiss", "LX", 690), ("Lufthansa", "LH", 720)]
    }
    
    route_key = (departure_city, destination)
    if route_key in airlines_by_route:
        airline_options = airlines_by_route[route_key]
    else:
        # Default options for unknown routes
        airline_options = [("Delta", "DL", 800), ("United", "UA", 850), ("American Airlines", "AA", 780)]
    
    mock_flights = []
    
    for airline_name, airline_code, base_price in airline_options[:2]:  # Provide 2 options
        # Add some price variation
        price_variation = random.randint(-100, 200)
        total_price = (base_price + price_variation) * num_adults
        
        # Generate mock flight number
        flight_number = f"{airline_code}{random.randint(100, 999)}"
        
        mock_flights.append({
            "destination": destination,
            "price_per_person": total_price / num_adults,
            "total_price": total_price,
            "currency": "USD",
            "airline": airline_name,
            "airline_code": airline_code,
            "flight_number": flight_number,
            "duration": "PT8H30M",  # 8.5 hours typical for transatlantic
            "num_passengers": num_adults,
            "departure_time": f"{departure_date}T10:30:00",
            "arrival_time": f"{departure_date}T19:00:00",
            "stops": 0,
            "origin": departure_city,
            "_mock_data": True,  # Flag to indicate this is mock data
            "_note": "Mock data - Amadeus test environment unavailable"
        })
    
    return mock_flights
