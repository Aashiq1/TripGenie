# tools/hotel_tool.py
import json
from typing import List, Dict
from langchain.tools import Tool
from app.services.amadeus_hotels import (
    get_hotel_offers, 
    assign_rooms_smartly, 
    calculate_total_accommodation_cost,
    get_standard_room_types
)

class HotelSearchTool:
    """
    LangChain tool for searching hotels with group accommodation in mind.
    """
    
    def __init__(self):
        self.name = "hotel_search"
        self.description = (
            "Search for hotels and calculate group accommodation costs. "
            "Input JSON with: "
            "- destinations (list of city codes to search) "
            "- check_in (YYYY-MM-DD) "
            "- check_out (YYYY-MM-DD) "
            "- group_accommodation_style (budget/standard/luxury) "
            "- accommodation_details (list of users with room_sharing preferences) "
            "Returns hotels with room configurations and individual costs."
        )
    
    def _call(self, input_str: str) -> str:
        """
        Search hotels for each destination and calculate group costs.
        """
        try:
            data = json.loads(input_str)
            
            destinations = data.get("destinations", [])
            check_in = data.get("check_in")
            check_out = data.get("check_out")
            group_accommodation_style = data.get("group_accommodation_style", "standard")
            accommodation_details = data.get("accommodation_details", [])
            
            # Calculate nights
            from datetime import datetime
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
            num_nights = (check_out_date - check_in_date).days
            
            results = {}
            
            for destination in destinations:
                # Search hotels
                hotels = get_hotel_offers(
                    city_code=destination,
                    check_in_date=check_in,
                    check_out_date=check_out,
                    accommodation_preference=group_accommodation_style
                )
                
                if not hotels:
                    # Fallback to estimates if API fails
                    results[destination] = self._generate_fallback_estimate(
                        destination,
                        accommodation_details,
                        group_accommodation_style,
                        num_nights
                    )
                else:
                    # Process each hotel option
                    hotel_options = []
                    
                    for hotel in hotels[:5]:  # Top 5 hotels
                        # Convert room types to standard format
                        available_rooms = {}
                        
                        for room_key, room_data in hotel['room_types_available'].items():
                            room_type_name = self._standardize_room_name(
                                room_data['capacity'],
                                room_data['category']
                            )
                            available_rooms[room_type_name] = {
                                'capacity': room_data['capacity'],
                                'base_price': room_data.get('base_price_per_night', room_data.get('total_price_per_night', 100))
                            }
                        
                        # If no rooms found, use standard types
                        if not available_rooms:
                            available_rooms = get_standard_room_types()
                        
                        # Assign rooms for this hotel
                        room_assignment = assign_rooms_smartly(
                            accommodation_details,
                            available_rooms
                        )
                        
                        # Calculate total costs
                        total_costs = calculate_total_accommodation_cost(
                            room_assignment,
                            num_nights
                        )
                        
                        hotel_options.append({
                            'hotel_name': hotel['hotel_name'],
                            'hotel_rating': hotel['hotel_rating'],
                            'address': hotel['address'],
                            'room_configuration': room_assignment['summary'],
                            'total_cost_per_night': room_assignment['total_cost_per_night'],
                            'total_trip_cost': total_costs['total_group_cost'],
                            'individual_costs': [
                                {
                                    'name': details['name'],
                                    'email': occupant_id,  # Use the key as email/name
                                    'room_type': details['room_type'],
                                    'cost_per_night': details['cost_per_night'],
                                    'total_cost': details['total_cost'],
                                    'sharing_with': details['sharing_with']
                                }
                                for occupant_id, details in total_costs['individual_costs'].items()
                            ],
                            'nights': num_nights
                        })
                    
                    results[destination] = {
                        'hotels': hotel_options,
                        'search_parameters': {
                            'check_in': check_in,
                            'check_out': check_out,
                            'nights': num_nights,
                            'accommodation_style': group_accommodation_style,
                            'group_size': len(accommodation_details)
                        }
                    }
            
            return json.dumps(results, indent=2)
            
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _standardize_room_name(self, capacity: int, category: str) -> str:
        """Convert Amadeus room categories to standard names."""
        if capacity == 1:
            return "single"
        elif capacity == 2:
            return "double"
        elif capacity == 3:
            return "triple"
        elif capacity == 4:
            return "quad"
        elif capacity >= 5:
            return "family"
        else:
            return category.lower()
    
    def _generate_fallback_estimate(self, destination: str, accommodation_details: List[Dict], 
                                   style: str, num_nights: int) -> Dict:
        """Generate estimate if API fails."""
        # Price estimates by style
        base_prices = {
            "budget": {"single": 60, "double": 90, "triple": 120, "quad": 150},
            "standard": {"single": 100, "double": 150, "triple": 200, "quad": 250},
            "luxury": {"single": 200, "double": 300, "triple": 400, "quad": 500}
        }
        
        prices = base_prices.get(style, base_prices["standard"])
        
        # City-specific hotel suggestions
        city_hotels = {
            "MAD": {
                "budget": "Hotel Mayorazgo (City Center) or Similar",
                "standard": "Hotel Atlantico Madrid (Gran Via) or Similar", 
                "luxury": "Hotel Villa Real (Near Prado Museum) or Similar"
            },
            "BCN": {
                "budget": "Hotel Barcelona Center (Gothic Quarter) or Similar",
                "standard": "Hotel Midmost Barcelona (Eixample) or Similar",
                "luxury": "Hotel Casa Fuster (Passeig de Gracia) or Similar"
            }
        }
        
        # Get appropriate hotel name
        hotel_name = city_hotels.get(destination, {}).get(style, f"{style.title()} Hotels in {destination} City Center")
        
        # Use standard room types for estimation
        available_rooms = {
            "single": {"capacity": 1, "base_price": prices["single"]},
            "double": {"capacity": 2, "base_price": prices["double"]},
            "triple": {"capacity": 3, "base_price": prices["triple"]},
            "quad": {"capacity": 4, "base_price": prices["quad"]}
        }
        
        # Assign rooms
        room_assignment = assign_rooms_smartly(accommodation_details, available_rooms)
        total_costs = calculate_total_accommodation_cost(room_assignment, num_nights)
        
        return {
            'hotels': [{
                'hotel_name': hotel_name,
                'hotel_rating': '3-4 stars (estimated)',
                'address': f'{destination} City Center - Various locations available',
                'room_configuration': room_assignment['summary'],
                'total_cost_per_night': room_assignment['total_cost_per_night'],
                'total_trip_cost': total_costs['total_group_cost'],
                'individual_costs': [
                    {
                        'name': details['name'],
                        'email': occupant_id,  # Use the key as email/name
                        'room_type': details['room_type'],
                        'cost_per_night': details['cost_per_night'],
                        'total_cost': details['total_cost'],
                        'sharing_with': details['sharing_with']
                    }
                    for occupant_id, details in total_costs['individual_costs'].items()
                ],
                'nights': num_nights,
                '_fallback_data': True,
                '_note': 'Estimated pricing - Amadeus hotel API unavailable'
            }],
            'search_parameters': {
                'destination': destination,
                'accommodation_style': style,
                'group_size': len(accommodation_details),
                'api_status': 'fallback_estimate'
            }
        }


# Function to create the tool for LangChain
def get_hotel_search_tool() -> Tool:
    """Create a LangChain Tool instance."""
    tool = HotelSearchTool()
    return Tool(
        name=tool.name,
        description=tool.description,
        func=tool._call
    )