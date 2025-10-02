# tools/hotel_tool.py
import json
from typing import List, Dict
from langchain.tools import Tool
from app.services.amadeus_hotels import (
    get_hotel_offers, 
    assign_rooms_smartly, 
    calculate_total_accommodation_cost,
    get_standard_room_types,
    get_best_room_price_for_hotel,
    generate_candidate_packings
)
from app.services.google_places_service import GooglePlacesService
from app.services.amadeus_location_lookup import iata_to_city_name

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
                # Resolve city center anchor coordinates
                anchor_coords = None
                try:
                    city_name = iata_to_city_name(destination)
                    try:
                        places = GooglePlacesService()
                        anchor_coords = places._get_destination_coordinates(city_name)
                    except Exception:
                        anchor_coords = None
                except Exception:
                    anchor_coords = None

                # Search hotels (with anchor if available)
                hotels = get_hotel_offers(
                    city_code=destination,
                    check_in_date=check_in,
                    check_out_date=check_out,
                    accommodation_preference=group_accommodation_style,
                    anchor_coords=anchor_coords
                )
                
                if not hotels:
                    # Fallback to estimates if API fails
                    strict = str(os.getenv("HOTEL_STRICT", "")).strip().lower() in {"1", "true", "yes", "on"}
                    if strict:
                        results[destination] = {
                            'hotels': [],
                            'search_parameters': {
                                'destination': destination,
                                'accommodation_style': group_accommodation_style,
                                'group_size': len(accommodation_details),
                                'api_status': 'no_results_strict'
                            }
                        }
                        continue
                    results[destination] = self._generate_fallback_estimate(
                        destination,
                        accommodation_details,
                        group_accommodation_style,
                        num_nights
                    )
                else:
                    # Process each hotel option
                    hotel_options = []
                    hotel_pairs = []  # Keep (raw_hotel, option) to access distance/rating for scoring
                    
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
                        
                        # Calculate initial total costs
                        total_costs = calculate_total_accommodation_cost(room_assignment, num_nights)

                        # === Reprice after assignment using occupancy-aware per-room fetching ===
                        try:
                            hotel_id = hotel.get('hotel_id') or hotel.get('hotelId')
                            if hotel_id:
                                # Primary occupancy vector from assignment
                                vector: list[int] = []
                                for a in room_assignment.get('assignments', []):
                                    cap = int(a.get('capacity') or 0)
                                    if cap >= 1:
                                        vector.append(cap)
                                if not vector:
                                    vector = [len(accommodation_details) or 1]

                                # Try the assignment vector first; then a few candidate packings
                                vectors = [vector] + generate_candidate_packings(accommodation_details)

                                best_per_night_total = None
                                for occ in vectors:
                                    per_night_sum = 0.0
                                    feasible = True
                                    for adults in occ:
                                        price = get_best_room_price_for_hotel(hotel_id, check_in, check_out, adults=adults)
                                        if isinstance(price, (int, float)):
                                            per_night_sum += float(price)
                                        else:
                                            feasible = False
                                            break
                                    if feasible:
                                        if best_per_night_total is None or per_night_sum < best_per_night_total:
                                            best_per_night_total = per_night_sum

                                if isinstance(best_per_night_total, (int, float)):
                                    total_costs['total_group_cost'] = float(best_per_night_total) * float(num_nights)
                                    group_size_safe = max(len(accommodation_details), 1)
                                    fair_pp_per_night = float(best_per_night_total) / group_size_safe if best_per_night_total > 0 else 0.0
                                    for person in total_costs.get('individual_costs', {}).values():
                                        person['cost_per_night'] = fair_pp_per_night
                                        person['total_cost'] = fair_pp_per_night * float(num_nights)
                                    room_assignment['total_cost_per_night'] = float(best_per_night_total)
                        except Exception:
                            # If repricing fails, keep initial totals
                            pass
                        
                        # Build human-friendly room breakdown
                        room_counts: Dict[str, int] = {}
                        room_details: List[Dict] = []
                        for a in room_assignment.get('assignments', []):
                            rtype = (a.get('room_type') or 'unknown').lower()
                            room_counts[rtype] = room_counts.get(rtype, 0) + 1
                            room_details.append({
                                'room_type': rtype,
                                'capacity': a.get('capacity'),
                                'occupants': a.get('occupants'),
                                'occupant_names': a.get('occupant_names'),
                                'cost_per_person': a.get('cost_per_person'),
                                'total_room_cost': a.get('total_room_cost')
                            })

                        option_payload = {
                            'hotel_name': hotel['hotel_name'],
                            'hotel_rating': hotel['hotel_rating'],
                            'address': hotel['address'],
                            'room_configuration': room_assignment['summary'],
                            'room_assignments': room_assignment.get('assignments', []),
                            'room_breakdown': {
                                'counts': room_counts,
                                'details': room_details
                            },
                            'total_cost_per_night': room_assignment['total_cost_per_night'],
                            'total_trip_cost': total_costs['total_group_cost'],
                            'source': hotel.get('source', 'amadeus_live'),
                            'amadeus_env': hotel.get('amadeus_env', ''),
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
                        }
                        hotel_options.append(option_payload)
                        hotel_pairs.append((hotel, option_payload))
                    
                    # === Scoring to produce recommended + alternates ===
                    def _parse_rating(value) -> int:
                        try:
                            return int(value) if value not in (None, 'Unrated') else 0
                        except Exception:
                            return 0

                    group_size = max(len(accommodation_details), 1)
                    scored = []
                    for raw_hotel, opt in hotel_pairs:
                        total_cost = float(opt.get('total_trip_cost', 0) or 0)
                        nights_safe = max(num_nights, 1)
                        price_pppn = total_cost / (group_size * nights_safe) if total_cost > 0 else float('inf')
                        dist = raw_hotel.get('distance_km_to_anchor')
                        distance_km = float(dist) if isinstance(dist, (int, float)) else 50.0
                        rating_num = _parse_rating(raw_hotel.get('hotel_rating'))
                        # Simple value score: lower is better
                        w_price, w_dist, w_rating = 1.0, 0.5, 0.2
                        score = w_price * price_pppn + w_dist * distance_km + w_rating * (5 - rating_num)
                        scored.append({
                            **opt,
                            'distance_km_to_anchor': dist if isinstance(dist, (int, float)) else None,
                            'score': round(score, 2)
                        })

                    scored.sort(key=lambda x: x['score'])
                    recommended = scored[0] if scored else None
                    alternates = scored[1:3] if len(scored) > 1 else []

                    results[destination] = {
                        'hotels': hotel_options,
                        'recommended': recommended,
                        'alternates': alternates,
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