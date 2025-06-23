from amadeus import Client, ResponseError
import os

# Initialize the Amadeus API client with credentials from environment variables
amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET")
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
            
        response = amadeus.shopping.flight_offers_search.get(**search_params)

        return [
            {
                "destination": destination,
                "price_per_person": float(offer['price']['total']) / num_adults,
                "total_price": float(offer['price']['total']),
                "currency": offer['price']['currency'],
                "airline": offer['validatingAirlineCodes'][0],
                "duration": offer['itineraries'][0]['duration'],
                "num_passengers": num_adults,
                "departure_time": offer['itineraries'][0]['segments'][0]['departure']['at'],
                "arrival_time": offer['itineraries'][0]['segments'][-1]['arrival']['at'],
                "stops": len(offer['itineraries'][0]['segments']) - 1
            }
            for offer in response.data
        ]

    except ResponseError as e:
        return {"error": str(e)}
