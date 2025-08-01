# app/services/hotels.py

from amadeus import Client, ResponseError
import os
from typing import List, Dict, Optional
from datetime import datetime

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

# Initialize the Amadeus API client
amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET"),
    hostname='test'  # Use test environment endpoints for test credentials
)

def get_hotel_offers(
    city_code: str,
    check_in_date: str, 
    check_out_date: str,
    accommodation_preference: str = "standard"
) -> List[Dict]:
    """
    Fetch hotel offers from Amadeus for a city.
    
    Args:
        city_code (str): IATA city code (e.g., 'BCN' for Barcelona)
        check_in_date (str): Check-in date in YYYY-MM-DD
        check_out_date (str): Check-out date in YYYY-MM-DD
        accommodation_preference (str): "budget", "standard", or "luxury"
    
    Returns:
        List[Dict]: List of hotel offers with details
    """
    try:
        # Step 1: Get hotels in the city
        hotels_response = amadeus.reference_data.locations.hotels.by_city.get(
            cityCode=city_code
        )
        
        if not hotels_response.data:
            return []
        
        # Map accommodation preference to ratings
        rating_map = {
            "budget": [1, 2, 3],
            "standard": [3, 4],
            "luxury": [4, 5]
        }
        
        # Filter hotels by rating preference
        target_ratings = rating_map.get(accommodation_preference, [3, 4])
        filtered_hotels = []
        
        for hotel in hotels_response.data[:20]:  # Check first 20 hotels
            hotel_rating = int(hotel.get('rating', 0))
            if hotel_rating in target_ratings or hotel_rating == 0:
                filtered_hotels.append(hotel['hotelId'])
        
        if not filtered_hotels:
            # If no hotels match criteria, use first 10
            filtered_hotels = [h['hotelId'] for h in hotels_response.data[:10]]
        
        # Step 2: Search for offers at these hotels - TRY INDIVIDUALLY
        # Calculate number of nights
        check_in = datetime.strptime(check_in_date, '%Y-%m-%d')
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d')
        num_nights = (check_out - check_in).days
        
        hotels = []
        successful_searches = 0
        max_hotels_to_try = min(15, len(filtered_hotels))  # Try up to 15 hotels
        
        for hotel_id in filtered_hotels[:max_hotels_to_try]:
            try:
                # Search one hotel at a time to handle availability issues
                offers_response = amadeus.shopping.hotel_offers_search.get(
                    hotelIds=[hotel_id],  # Search one hotel at a time
                    checkInDate=check_in_date,
                    checkOutDate=check_out_date,
                    adults=1,  # Search for base price
                    roomQuantity=1,
                    currency='USD'
                )
                
                # If we get here, this hotel has availability
                for hotel_data in offers_response.data:
                    hotel_info = hotel_data['hotel']
                    
                    # Parse available room types from all offers
                    room_types_available = {}
                    
                    for offer in hotel_data.get('offers', []):
                        try:
                            room = offer['room']
                            bed_info = room.get('description', {}).get('text', '')
                            
                            # Extract basic room info
                            category = room.get('typeEstimated', {}).get('category', 'STANDARD_ROOM')
                            beds = room.get('typeEstimated', {}).get('beds', 2)
                            
                            # Estimate capacity
                            capacity = estimate_room_capacity(beds, bed_info, category)
                            
                            # Get price info
                            price_info = offer.get('price', {})
                            base_price = float(price_info.get('base', 0))
                            total_price = float(price_info.get('total', base_price))
                            
                            # Create room type key
                            room_key = f"{category}_{capacity}pax"
                            
                            if room_key not in room_types_available:
                                room_types_available[room_key] = {
                                    'capacity': capacity,
                                    'category': category,
                                    'base_price_per_night': base_price,
                                    'total_price_per_night': total_price,
                                    'bed_info': bed_info,
                                    'available_rooms': 1
                                }
                        except (KeyError, TypeError, ValueError) as e:
                            print(f"Error parsing hotel offer: {e}")
                            # Continue with next offer
                            continue
                
                    hotels.append({
                        'hotel_id': hotel_info['hotelId'],
                        'hotel_name': hotel_info['name'],
                        'hotel_rating': hotel_info.get('rating', 'Unrated'),
                        'latitude': hotel_info.get('latitude'),
                        'longitude': hotel_info.get('longitude'),
                        'address': hotel_info.get('address', {}).get('lines', ['Address not available'])[0],
                        'room_types_available': room_types_available,
                        'accommodation_type': accommodation_preference,
                        'num_nights': num_nights
                    })
                    
                    successful_searches += 1
                    
                    # Stop after finding 5 good hotels
                    if successful_searches >= 5:
                        break
                        
            except ResponseError as e:
                if "NO ROOMS AVAILABLE" in str(e):
                    print(f"No rooms available at hotel {hotel_id}, trying next hotel...")
                    continue  # Try next hotel
                else:
                    print(f"Hotel search error for {hotel_id}: {e}")
                    continue  # Try next hotel
            except Exception as e:
                print(f"Error searching hotel {hotel_id}: {e}")
                continue  # Try next hotel
        
        if not hotels:
            print(f"No hotels with availability found in {city_code}")
        else:
            print(f"Found {len(hotels)} hotels with availability in {city_code}")
            
        return hotels
        
    except ResponseError as e:
        print(f"Amadeus API error: {e}")
        return []
    except Exception as e:
        print(f"Error searching hotels: {e}")
        return []


def estimate_room_capacity(beds: int, bed_type: str, category: str) -> int:
    """
    Estimate room capacity based on Amadeus data.
    """
    # Handle special categories first
    if 'FAMILY' in category.upper():
        return max(4, beds)  # Family rooms usually 4-6 people
    elif 'SUITE' in category.upper() and beds >= 2:
        return beds + 1  # Suites often have sofa beds
    elif 'TRIPLE' in category.upper():
        return 3
    elif 'QUAD' in category.upper():
        return 4
    
    # Otherwise base on bed count and type
    if bed_type == 'DOUBLE':
        return beds * 2  # Double beds sleep 2
    elif bed_type == 'SINGLE':
        return beds  # Single beds sleep 1
    else:
        # Conservative estimate
        return max(beds, 2 if beds == 1 else beds)


def get_standard_room_types():
    """
    Return standard room types for fallback/estimation.
    """
    return {
        "single": {"capacity": 1, "base_price": 100},
        "double": {"capacity": 2, "base_price": 150},
        "triple": {"capacity": 3, "base_price": 200},
        "quad": {"capacity": 4, "base_price": 250},
        "family": {"capacity": 6, "base_price": 350}
    }


def assign_rooms_smartly(users: List[Dict], available_room_types: Dict[str, Dict]) -> Dict:
    """
    Smart room assignment with FAIR COST DISTRIBUTION:
    1. Give private rooms to those who want them
    2. For sharing users, ensure fair cost even when forced into different room types
    """
    
    # Step 1: Separate users by preference
    want_private = [u for u in users if u.get('room_sharing') == 'private']
    willing_to_share = [u for u in users if u.get('room_sharing') in ['share', 'any']]
    
    room_assignments = []
    total_cost = 0
    
    # Convert available room types to list sorted by capacity (descending)
    room_options = []
    for room_type, details in available_room_types.items():
        room_options.append({
            'type': room_type,
            'capacity': details['capacity'],
            'price': details.get('base_price', details.get('price_per_night', 100))
        })
    room_options.sort(key=lambda x: x['capacity'], reverse=True)
    
    # Step 2: Assign private rooms
    single_room_price = next((r['price'] for r in room_options if r['capacity'] == 1), 100)
    
    for user in want_private:
        room_assignments.append({
            'room_type': 'single',
            'occupants': [user.get('email', user.get('name', 'Unknown'))],
            'occupant_names': [user.get('name', 'Unknown')],
            'cost_per_person': single_room_price,
            'total_room_cost': single_room_price
        })
        total_cost += single_room_price
    
    # Step 3: FAIR SHARED ROOM ASSIGNMENT
    sharing_users = willing_to_share.copy()
    sharing_assignments = []
    sharing_total_cost = 0
    
    while len(sharing_users) > 0:
        assigned = False
        
        # Try each room type from largest to smallest
        for room_option in room_options:
            capacity = room_option['capacity']
            
            # Skip single rooms in this phase
            if capacity == 1:
                continue
            
            # If we have enough people for this room
            if len(sharing_users) >= capacity:
                # Assign people to this room
                occupants = []
                occupant_names = []
                
                for _ in range(capacity):
                    user = sharing_users.pop(0)
                    occupants.append(user.get('email', user.get('name', 'Unknown')))
                    occupant_names.append(user.get('name', 'Unknown'))
                
                sharing_assignments.append({
                    'room_type': room_option['type'],
                    'occupants': occupants,
                    'occupant_names': occupant_names,
                    'total_room_cost': room_option['price'],
                    'capacity': capacity
                })
                
                sharing_total_cost += room_option['price']
                assigned = True
                break
        
        # If we couldn't assign to any multi-person room, use singles
        if not assigned and len(sharing_users) > 0:
            user = sharing_users.pop(0)
            sharing_assignments.append({
                'room_type': 'single',
                'occupants': [user.get('email', user.get('name', 'Unknown'))],
                'occupant_names': [user.get('name', 'Unknown')],
                'total_room_cost': single_room_price,
                'capacity': 1
            })
            sharing_total_cost += single_room_price
    
    # Step 4: FAIR COST DISTRIBUTION for sharing users
    total_sharing_users = len(willing_to_share)
    if total_sharing_users > 0:
        fair_cost_per_person = sharing_total_cost / total_sharing_users
        
        # Apply fair cost to all sharing assignments
        for assignment in sharing_assignments:
            num_occupants = len(assignment['occupants'])
            assignment['cost_per_person'] = fair_cost_per_person
            # Note: total room cost stays the same for hotel billing
        
        room_assignments.extend(sharing_assignments)
        total_cost += sharing_total_cost
    
    return {
        'assignments': room_assignments,
        'total_cost_per_night': total_cost,
        'summary': generate_room_summary(room_assignments),
        'cost_breakdown': generate_cost_breakdown(room_assignments)
    }


def generate_room_summary(assignments: List[Dict]) -> str:
    """Generate human-readable summary of room assignments."""
    room_counts = {}
    for assignment in assignments:
        room_type = assignment['room_type']
        room_counts[room_type] = room_counts.get(room_type, 0) + 1
    
    summary_parts = []
    for room_type, count in sorted(room_counts.items()):
        if count == 1:
            summary_parts.append(f"1 {room_type}")
        else:
            summary_parts.append(f"{count} {room_type}s")
    
    return ", ".join(summary_parts)


def generate_cost_breakdown(assignments: List[Dict]) -> List[Dict]:
    """Generate detailed cost breakdown per person."""
    breakdown = []
    
    for assignment in assignments:
        for i, occupant_id in enumerate(assignment['occupants']):
            breakdown.append({
                'user_email': occupant_id,  # Could be email or name
                'user_name': assignment['occupant_names'][i],
                'room_type': assignment['room_type'],
                'sharing_with': len(assignment['occupants']) - 1,
                'cost_per_night': assignment['cost_per_person']
            })
    
    return breakdown


def calculate_total_accommodation_cost(
    room_assignments: Dict,
    num_nights: int
) -> Dict:
    """
    Calculate total accommodation costs for the trip.
    """
    cost_per_night = room_assignments['total_cost_per_night']
    total_cost = cost_per_night * num_nights
    
    # Calculate individual totals
    individual_totals = {}
    for person in room_assignments['cost_breakdown']:
        occupant_id = person['user_email']  # Could be email or name
        individual_totals[occupant_id] = {
            'name': person['user_name'],
            'room_type': person['room_type'],
            'cost_per_night': person['cost_per_night'],
            'total_cost': person['cost_per_night'] * num_nights,
            'sharing_with': person['sharing_with']
        }
    
    return {
        'total_group_cost': total_cost,
        'cost_per_night': cost_per_night,
        'num_nights': num_nights,
        'individual_costs': individual_totals,
        'room_configuration': room_assignments['summary']
    }