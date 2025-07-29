import json
from langchain.tools import Tool
from app.services.amadeus_flights import get_flight_offers

class AmadeusFlightTool:
    """
    LangChain tool for fetching round-trip flight prices and schedules 
    using the Amadeus API. Now handles grouped passengers and preferences.
    """

    name = "flight_prices"
    description = (
        "Use this tool to get live round-trip flight prices using the Amadeus API. "
        "Provide flight groups with departure cities, destinations, dates, and preferences. "
        "Returns detailed flight information including prices, airlines, and schedules. "
        "Handles errors gracefully with helpful suggestions when flights aren't found."
    )

    def _call(self, input_str: str) -> str:
        """
        Parses input JSON, fetches flight prices from Amadeus for GROUPS, and returns results.
        Now includes better error handling and suggestions when flights aren't available.
        """
        try:
            input_data = json.loads(input_str)
            
            # Extract flight preferences if provided
            flight_prefs = input_data.get("flight_preferences", {})
            travel_class = flight_prefs.get("travel_class", "economy").upper()
            nonstop_only = flight_prefs.get("nonstop_preferred", False)
            
            # Convert travel class to Amadeus format
            class_mapping = {
                "ECONOMY": "ECONOMY",
                "BUSINESS": "BUSINESS", 
                "FIRST": "FIRST",
                "PREMIUM": "PREMIUM_ECONOMY"
            }
            amadeus_class = class_mapping.get(travel_class, "ECONOMY")
            
            # Get flight groups
            flight_groups = input_data.get("flight_groups", [])
            
            # If old format (backward compatibility), convert it
            if not flight_groups and "departure_city" in input_data:
                flight_groups = [{
                    "departure_city": input_data["departure_city"],
                    "passenger_count": 1,
                    "destinations": input_data["destinations"],
                    "departure_date": input_data["departure_date"],
                    "return_date": input_data["return_date"]
                }]
            
            results = {}
            all_errors = []
            successful_searches = 0
            total_searches = 0
            
            for group in flight_groups:
                from_city = group["departure_city"]
                passenger_count = group["passenger_count"]
                destinations = group["destinations"]
                depart_date = group["departure_date"]
                return_date = group["return_date"]
                
                # Create a key that shows airport and passenger count
                group_key = f"{from_city}_x{passenger_count}"
                results[group_key] = {}
                
                for dest in destinations:
                    total_searches += 1
                    
                    # Call with actual group size and preferences
                    offers = get_flight_offers(
                        from_city, 
                        dest, 
                        depart_date, 
                        return_date,
                        num_adults=passenger_count,  # ACTUAL GROUP SIZE
                        travel_class=amadeus_class,   # FROM PREFERENCES
                        nonstop_only=nonstop_only    # FROM PREFERENCES
                    )
                    
                    # Check if this is an error response
                    if isinstance(offers, dict) and "error" in offers:
                        results[group_key][dest] = offers
                        all_errors.append(f"{from_city} -> {dest}: {offers.get('error', 'Unknown error')}")
                    else:
                        results[group_key][dest] = offers
                        if offers:  # If we got actual flight data
                            successful_searches += 1
            
            # Add summary information for the agent
            search_summary = {
                "total_routes_searched": total_searches,
                "successful_routes": successful_searches,
                "failed_routes": total_searches - successful_searches,
                "success_rate": f"{(successful_searches/total_searches)*100:.1f}%" if total_searches > 0 else "0%"
            }
            
            # If no flights found at all, provide comprehensive guidance
            if successful_searches == 0:
                error_summary = {
                    "status": "NO_FLIGHTS_FOUND",
                    "message": "Unable to find flights for any of the requested routes.",
                    "search_summary": search_summary,
                    "common_issues": [
                        "Amadeus test environment has limited route data",
                        "Madrid (MAD) routes may not be available in test data",
                        "Future dates (2025) may not have published schedules",
                        "Some departure cities may not have direct service to destination"
                    ],
                    "recommendations": [
                        "Try alternative destinations (Barcelona-BCN, Paris-CDG, London-LHR)",
                        "Use dates within 6 months for better availability",
                        "Consider major hub airports for departures",
                        "Switch to production Amadeus environment for real data"
                    ],
                    "alternative_search_options": [
                        "Google Flights (https://www.google.com/flights)",
                        "Kayak (https://www.kayak.com)",
                        "Expedia (https://www.expedia.com)"
                    ]
                }
                results["flight_search_status"] = error_summary
            
            # Add individual error details if any
            if all_errors:
                results["errors_encountered"] = all_errors
            
            results["search_summary"] = search_summary
            
            return json.dumps(results, indent=2)

        except Exception as e:
            error_response = {
                "error": f"Tool execution failed: {str(e)}",
                "status": "TOOL_ERROR",
                "suggestions": [
                    "Check input JSON format",
                    "Verify all required fields are present",
                    "Ensure dates are in YYYY-MM-DD format",
                    "Confirm airport codes are valid IATA codes"
                ]
            }
            return json.dumps(error_response, indent=2)

# Example usage for testing
if __name__ == "__main__":
    tool = AmadeusFlightTool()
    
    # Test case 1: Search that will likely fail (Madrid from multiple cities, future date)
    print("=== Testing Madrid Search (Likely to Fail) ===")
    test_input_madrid = {
        "flight_groups": [
            {
                "departure_city": "LAX",
                "passenger_count": 1,
                "destinations": ["MAD"],
                "departure_date": "2025-07-15",
                "return_date": "2025-07-21"
            },
            {
                "departure_city": "JFK",
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
    
    result_madrid = tool._call(json.dumps(test_input_madrid, indent=2))
    print("Madrid Search Result:")
    print(result_madrid)
    
    print("\n" + "="*60 + "\n")
    
    # Test case 2: Search with potentially better success (Barcelona, closer dates)
    print("=== Testing Barcelona Search (Better Chance) ===")
    from datetime import datetime, timedelta
    future_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=97)).strftime("%Y-%m-%d")
    
    test_input_bcn = {
        "flight_groups": [
            {
                "departure_city": "LAX",
                "passenger_count": 1,
                "destinations": ["BCN"],
                "departure_date": future_date,
                "return_date": return_date
            }
        ],
        "flight_preferences": {
            "travel_class": "economy",
            "nonstop_preferred": False
        }
    }
    
    result_bcn = tool._call(json.dumps(test_input_bcn, indent=2))
    print("Barcelona Search Result:")
    print(result_bcn)