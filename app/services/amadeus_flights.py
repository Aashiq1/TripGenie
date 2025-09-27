from amadeus import Client, ResponseError
import os
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
import time

# Set up logging
logger = logging.getLogger(__name__)

# Initialize the Amadeus API client with credentials from environment variables
# Using test environment for development (change to production when ready)
amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET"),
    hostname='test'  # Use test environment (change to 'production' for real pricing with production credentials)
)

# === Simple in-memory TTL cache for flight offers ===
_OFFERS_CACHE: Dict[str, Any] = {}
_OFFERS_CACHE_TTL_SECONDS = 10 * 60  # 10 minutes


def _cache_key(
    departure_city: str,
    destination: str,
    departure_date: str,
    return_date: str,
    num_adults: int,
    travel_class: str,
    nonstop_only: bool,
) -> str:
    return f"{departure_city}|{destination}|{departure_date}|{return_date}|{num_adults}|{travel_class}|nonstop={nonstop_only}"


def _cache_get(key: str):
    item = _OFFERS_CACHE.get(key)
    if not item:
        return None
    ts = item.get("ts", 0)
    if time.time() - ts > _OFFERS_CACHE_TTL_SECONDS:
        try:
            del _OFFERS_CACHE[key]
        except Exception:
            pass
        return None
    return item.get("data")


def _cache_set(key: str, data: Any):
    _OFFERS_CACHE[key] = {"ts": time.time(), "data": data}

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
    # Cache lookup
    key = _cache_key(departure_city, destination, departure_date, return_date, num_adults, travel_class, nonstop_only)
    cached = _cache_get(key)
    if cached is not None:
        logger.debug("Returning cached flight offers")
        return cached
    
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
        
        # Request a broader set of offers for better pricing coverage
        search_params["max"] = 20
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
                    # Normalize inconsistent payloads and avoid division issues
                    "price_per_person": float(offer['price']['total']) / max(1, int(num_adults or 1)),
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
        _cache_set(key, flight_offers)
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
            data = _get_mock_flight_data(departure_city, destination, departure_date, return_date, num_adults)
            _cache_set(key, data)
            return data
        return {"error": f"Unexpected error: {str(e)}", "suggestions": _get_general_suggestions()}


def _month_bounds(month_str: str) -> tuple[date, date]:
    """Return the first and last date of a month given 'YYYY-MM'."""
    start = datetime.strptime(month_str + "-01", "%Y-%m-%d").date()
    # Next month
    if start.month == 12:
        next_month = date(start.year + 1, 1, 1)
    else:
        next_month = date(start.year, start.month + 1, 1)
    end = next_month - timedelta(days=1)
    return start, end


def _dow_candidates(start: date, end: date) -> List[date]:
    """Heuristic: prefer Tue/Wed/Sat departures within the month; fallback to every 3 days."""
    candidates: List[date] = []
    cur = start
    preferred_dows = {1, 2, 5}  # Tue=1, Wed=2, Sat=5 (Python: Mon=0)
    while cur <= end:
        if cur.weekday() in preferred_dows:
            candidates.append(cur)
        cur += timedelta(days=1)
    # If too few, add every 3 days to ensure coverage
    if len(candidates) < 6:
        cur = start
        while cur <= end:
            if cur not in candidates:
                candidates.append(cur)
            cur += timedelta(days=3)
    return sorted(set(candidates))


def get_cheapest_date_candidates(
    departure_city: str,
    destination: str,
    month: str,
    trip_duration_days: int,
    num_adults: int = 1,
    travel_class: str = "ECONOMY",
    nonstop_only: bool = False,
    max_candidates: int = 3
) -> List[Dict[str, Any]]:
    """
    Return up to `max_candidates` cheapest (departure_date, return_date) windows within a month
    for a specific origin->destination and group size.

    Attempts to use Amadeus Flight Dates/Calendar if available; falls back to heuristic sampling
    using `get_flight_offers` on a limited set of departure dates.

    Returns list of dicts: [{"departure_date": "YYYY-MM-DD", "return_date": "YYYY-MM-DD", "min_total_price": float}]
    """
    logger.info(
        f"Finding cheapest date candidates for {departure_city}->{destination} in {month}, "
        f"duration={trip_duration_days} days, adults={num_adults}, class={travel_class}, nonstop={nonstop_only}"
    )

    # First try: use Amadeus calendar/flight-dates endpoint if present in SDK
    try:
        # Some SDKs expose shopping.flight_dates; guard dynamically to avoid crashes
        flight_dates_client = getattr(getattr(amadeus, "shopping", None), "flight_dates", None)
        if flight_dates_client is not None:
            # Many SDKs accept origin, destination, and (optionally) a month; if month unsupported, it may return a span.
            # We'll pass origin/destination and filter results to our month.
            response = flight_dates_client.get(
                origin=departure_city,
                destination=destination
            )
            data = getattr(response, "data", None)
            candidates: List[Dict[str, Any]] = []
            if isinstance(data, list):
                # Heuristic parse: expect items with departureDate, returnDate, or departureDate + price
                for item in data:
                    try:
                        dep = item.get("departureDate") or item.get("departure_date")
                        ret = item.get("returnDate") or item.get("return_date")
                        price = item.get("price", {}).get("total") if isinstance(item.get("price"), dict) else item.get("price")
                        if not dep:
                            continue
                        dep_dt = datetime.strptime(dep, "%Y-%m-%d").date()
                        # Synthesize return date if not provided
                        if ret:
                            ret_dt = datetime.strptime(ret, "%Y-%m-%d").date()
                        else:
                            ret_dt = dep_dt + timedelta(days=trip_duration_days - 1)
                        # Filter to the requested month
                        month_start, month_end = _month_bounds(month)
                        if not (month_start <= dep_dt <= month_end and month_start <= ret_dt <= month_end):
                            continue
                        if price is None:
                            continue
                        candidates.append({
                            "departure_date": dep_dt.strftime("%Y-%m-%d"),
                            "return_date": ret_dt.strftime("%Y-%m-%d"),
                            "min_total_price": float(price)
                        })
                    except Exception:
                        continue
            if candidates:
                candidates.sort(key=lambda x: x["min_total_price"])
                return candidates[:max_candidates]
    except ResponseError as e:
        logger.warning(f"Flight dates endpoint not available or failed: {e}")
    except Exception as e:
        logger.warning(f"Flight dates calendar parse failed: {e}")

    # Fallback: heuristic sampling of departure dates within the month
    month_start, month_end = _month_bounds(month)
    dep_candidates = _dow_candidates(month_start, month_end)
    sampled_candidates: List[Dict[str, Any]] = []

    for dep_dt in dep_candidates:
        ret_dt = dep_dt + timedelta(days=trip_duration_days - 1)
        if ret_dt > month_end:
            continue
        try:
            offers = get_flight_offers(
                departure_city=departure_city,
                destination=destination,
                departure_date=dep_dt.strftime("%Y-%m-%d"),
                return_date=ret_dt.strftime("%Y-%m-%d"),
                num_adults=num_adults,
                travel_class=travel_class,
                nonstop_only=nonstop_only
            )
            if isinstance(offers, list) and offers:
                cheapest = min(offers, key=lambda x: x.get("total_price", float("inf")))
                sampled_candidates.append({
                    "departure_date": dep_dt.strftime("%Y-%m-%d"),
                    "return_date": ret_dt.strftime("%Y-%m-%d"),
                    "min_total_price": float(cheapest.get("total_price", float("inf")))
                })
        except Exception as e:
            logger.debug(f"Sampling offer failed for {dep_dt}: {e}")
            continue

    sampled_candidates.sort(key=lambda x: x["min_total_price"])
    return sampled_candidates[:max_candidates]


def get_cheapest_date_candidates_for_window(
    departure_city: str,
    destination: str,
    window_start: date,
    window_end: date,
    trip_duration_days: int,
    num_adults: int = 1,
    travel_class: str = "ECONOMY",
    nonstop_only: bool = False,
    max_candidates: int = 3
) -> List[Dict[str, Any]]:
    """
    Window-scoped version: returns up to `max_candidates` cheapest (departure, return) pairs fully inside
    [window_start, window_end], using flight-dates if available, else sampling within the window.
    """
    logger.info(
        f"Finding cheapest date candidates for window {window_start}..{window_end} {departure_city}->{destination}, duration={trip_duration_days}"
    )

    # Exact-fit shortcut: if window length equals duration exactly, return that single pair
    if (window_end - window_start).days + 1 == trip_duration_days:
        dep_str = window_start.strftime("%Y-%m-%d")
        ret_str = (window_start + timedelta(days=trip_duration_days - 1)).strftime("%Y-%m-%d")
        return [{"departure_date": dep_str, "return_date": ret_str, "min_total_price": float("inf")}]  # price will be computed later

    # Try calendar endpoint limited to ranges if supported by SDK
    try:
        flight_dates_client = getattr(getattr(amadeus, "shopping", None), "flight_dates", None)
        if flight_dates_client is not None:
            response = flight_dates_client.get(
                origin=departure_city,
                destination=destination,
                departureDate=f"{window_start.strftime('%Y-%m-%d')},{window_end.strftime('%Y-%m-%d')}"
            )
            data = getattr(response, "data", None)
            candidates: List[Dict[str, Any]] = []
            if isinstance(data, list):
                for item in data:
                    try:
                        dep = item.get("departureDate") or item.get("departure_date")
                        ret = item.get("returnDate") or item.get("return_date")
                        price = item.get("price", {}).get("total") if isinstance(item.get("price"), dict) else item.get("price")
                        if not dep:
                            continue
                        dep_dt = datetime.strptime(dep, "%Y-%m-%d").date()
                        # Synthesize return if not present
                        if ret:
                            ret_dt = datetime.strptime(ret, "%Y-%m-%d").date()
                        else:
                            ret_dt = dep_dt + timedelta(days=trip_duration_days - 1)
                        # Ensure pair sits fully inside window
                        if not (window_start <= dep_dt <= window_end and window_start <= ret_dt <= window_end):
                            continue
                        if price is None:
                            continue
                        candidates.append({
                            "departure_date": dep_dt.strftime("%Y-%m-%d"),
                            "return_date": ret_dt.strftime("%Y-%m-%d"),
                            "min_total_price": float(price)
                        })
                    except Exception:
                        continue
            if candidates:
                candidates.sort(key=lambda x: x["min_total_price"])
                return candidates[:max_candidates]
    except ResponseError as e:
        logger.warning(f"Flight dates window call failed: {e}")
    except Exception as e:
        logger.warning(f"Flight dates window parse failed: {e}")

    # Fallback: sample within the window
    sampled: List[Dict[str, Any]] = []
    cur = window_start
    # Prefer Tue/Wed/Sat; else every 2 days step to keep small
    preferred_dows = {1, 2, 5}
    dep_list: List[date] = []
    while cur <= window_end:
        if cur.weekday() in preferred_dows:
            dep_list.append(cur)
        cur += timedelta(days=1)
    if len(dep_list) < 4:
        cur = window_start
        while cur <= window_end:
            if cur not in dep_list:
                dep_list.append(cur)
            cur += timedelta(days=2)
    dep_list = sorted(set(dep_list))

    for dep_dt in dep_list:
        ret_dt = dep_dt + timedelta(days=trip_duration_days - 1)
        if ret_dt > window_end:
            continue
        try:
            offers = get_flight_offers(
                departure_city=departure_city,
                destination=destination,
                departure_date=dep_dt.strftime("%Y-%m-%d"),
                return_date=ret_dt.strftime("%Y-%m-%d"),
                num_adults=num_adults,
                travel_class=travel_class,
                nonstop_only=nonstop_only
            )
            if isinstance(offers, list) and offers:
                cheapest = min(offers, key=lambda x: x.get("total_price", float("inf")))
                sampled.append({
                    "departure_date": dep_dt.strftime("%Y-%m-%d"),
                    "return_date": ret_dt.strftime("%Y-%m-%d"),
                    "min_total_price": float(cheapest.get("total_price", float("inf")))
                })
        except Exception as e:
            logger.debug(f"Sampling window offer failed for {dep_dt}: {e}")
            continue

    sampled.sort(key=lambda x: x["min_total_price"])
    return sampled[:max_candidates]

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
