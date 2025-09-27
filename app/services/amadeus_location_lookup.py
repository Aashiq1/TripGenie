# app/services/amadeus_location_lookup.py
"""
Amadeus API location lookup service for converting city names to IATA codes.
This replaces hardcoded mappings with dynamic API-based lookups.
"""

from amadeus import Client, ResponseError
import os
import logging
from typing import Optional, Dict, List
from functools import lru_cache

# Set up logging
logger = logging.getLogger(__name__)

# Initialize the Amadeus API client
amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET"),
    hostname='test'  # Use test environment for development
)

@lru_cache(maxsize=128)
def lookup_iata_code(city_name: str) -> Optional[str]:
    """
    Look up IATA code for a city using Amadeus API.
    
    Args:
        city_name (str): City name (e.g., "Barcelona", "Madrid", "Paris")
        
    Returns:
        Optional[str]: IATA code if found (e.g., "BCN", "MAD", "CDG"), None if not found
    """
    try:
        logger.info(f"Looking up IATA code for city: {city_name}")
        
        # Search for airports in the city
        response = amadeus.reference_data.locations.get(
            keyword=city_name.strip(),
            subType='AIRPORT,CITY'
        )
        
        if not response.data:
            logger.warning(f"No locations found for: {city_name}")
            return None
            
        # Look for the best match
        for location in response.data:
            # Prefer AIRPORT type over CITY type for more specific results
            if location.get('subType') == 'AIRPORT':
                iata_code = location.get('iataCode')
                if iata_code:
                    logger.info(f"Found IATA code for {city_name}: {iata_code}")
                    return iata_code
        
        # If no airport found, try city-level results
        for location in response.data:
            if location.get('subType') == 'CITY':
                iata_code = location.get('iataCode')
                if iata_code:
                    logger.info(f"Found city IATA code for {city_name}: {iata_code}")
                    return iata_code
                    
        logger.warning(f"No IATA code found in results for: {city_name}")
        return None
        
    except ResponseError as e:
        logger.error(f"Amadeus API error looking up {city_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error looking up IATA code for {city_name}: {e}")
        return None

def get_airport_code_with_fallback(city_name: str) -> str:
    """
    Get IATA code for a city with fallback to hardcoded mapping.
    
    Args:
        city_name (str): City name
        
    Returns:
        str: IATA code if found, otherwise original city name
    """
    # First try dynamic lookup
    iata_code = lookup_iata_code(city_name)
    if iata_code:
        return iata_code
    
    # Fallback to hardcoded mapping for common cities
    city_to_airport_fallback = {
        "madrid": "MAD",
        "barcelona": "BCN", 
        "marrakech": "RAK",
        "marrakesh": "RAK",
        "palma de mallorca": "PMI",
        "palma": "PMI",
        "malaga": "AGP",
        "alicante": "ALC",
        "valencia": "VLC",
        "bilbao": "BIO",
        "seville": "SVQ",
        "sevilla": "SVQ",
        "granada": "GRX",
        "jerez de la frontera": "XRY",
        "jerez": "XRY",
        "paris": "CDG",
        "london": "LHR",
        "rome": "FCO",
        "amsterdam": "AMS",
        "berlin": "BER",
        "munich": "MUC",
        "zurich": "ZUR",
        "vienna": "VIE",
        "prague": "PRG",
        "lisbon": "LIS",
        "porto": "OPO"
    }
    
    city_lower = city_name.lower().strip()
    fallback_code = city_to_airport_fallback.get(city_lower)
    
    if fallback_code:
        logger.info(f"Using fallback IATA code for {city_name}: {fallback_code}")
        return fallback_code
    
    # If no mapping found, return original city name
    logger.warning(f"No IATA code found for {city_name}, returning original name")
    return city_name

@lru_cache(maxsize=128)
def iata_to_city_name(iata_code: str) -> str:
    """
    Convert IATA airport codes back to city names for activity search.
    
    Args:
        iata_code (str): IATA code (e.g., "MAD", "BCN")
        
    Returns:
        str: City name (e.g., "Madrid", "Barcelona")
    """
    # IATA code to city name mapping
    iata_to_city = {
        # Spain
        "MAD": "Madrid",
        "BCN": "Barcelona", 
        "RAK": "Marrakech",
        "PMI": "Palma de Mallorca",
        "AGP": "Malaga",
        "ALC": "Alicante",
        "VLC": "Valencia",
        "BIO": "Bilbao",
        "SVQ": "Seville",
        "GRX": "Granada",
        "XRY": "Jerez de la Frontera",
        
        # Major European cities
        "CDG": "Paris",
        "LHR": "London",
        "FCO": "Rome",
        "AMS": "Amsterdam",
        "BER": "Berlin",
        "MUC": "Munich",
        "ZUR": "Zurich",
        "VIE": "Vienna",
        "PRG": "Prague",
        "LIS": "Lisbon",
        "OPO": "Porto",
        
        # North America
        "LAX": "Los Angeles",
        "JFK": "New York",
        "BOS": "Boston",
        "MIA": "Miami",
        "CHI": "Chicago",
        "SFO": "San Francisco",
        "YYZ": "Toronto",
        "YVR": "Vancouver"
    }
    
    # Check if it's an IATA code
    iata_upper = iata_code.upper().strip()
    if iata_upper in iata_to_city:
        logger.info(f"Converting IATA code {iata_code} to city: {iata_to_city[iata_upper]}")
        return iata_to_city[iata_upper]
    
    # If not found or not an IATA code, return as is (already a city name)
    logger.info(f"No IATA conversion found for {iata_code}, using as city name")
    return iata_code

def bulk_lookup_iata_codes(city_names: List[str]) -> Dict[str, str]:
    """
    Look up IATA codes for multiple cities.
    
    Args:
        city_names (List[str]): List of city names
        
    Returns:
        Dict[str, str]: Mapping of city names to IATA codes
    """
    results = {}
    for city in city_names:
        results[city] = get_airport_code_with_fallback(city)
    return results