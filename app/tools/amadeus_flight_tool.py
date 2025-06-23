import json
from langchain.tools import Tool
from app.services.amadeus_flights import get_flight_offers

class AmadeusFlightTool:
    """
    A LangChain-compatible tool for retrieving live round-trip flight prices
    using the Amadeus API. Now handles grouped passengers and preferences.
    """

    def __init__(self):
        self.name = "flight_prices"
        self.description = (
            "Use this tool to get live round-trip flight prices using the Amadeus API. "
            "Provide a JSON input with the following keys: "
            "'flight_groups' (list of groups with departure_city, passenger_count, destinations, dates), "
            "'flight_preferences' (optional: travel_class and nonstop_preferred). "
            "Returns a price summary per destination for each group."
        )

    def _call(self, input_str: str) -> str:
        """
        Parses input JSON, fetches flight prices from Amadeus for GROUPS, and returns results.
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
                    results[group_key][dest] = offers
            
            return json.dumps(results, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})


def get_flight_price_tool() -> Tool:
    tool = AmadeusFlightTool()
    return Tool(
        name=tool.name,
        description=tool.description,
        func=tool._call
    )