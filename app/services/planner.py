# Updated planner.py with proper booking link integration

from app.models.group_inputs import UserInput
from app.services.ai_input import prepare_ai_input, get_best_ranges, get_group_preferences
from app.services.langchain_travel_agent import travel_agent
from app.services.booking_integration import get_all_booking_links  # NEW IMPORT
from app.tools.amadeus_flight_tool import AmadeusFlightTool  # NEW IMPORT FOR COST CHECKING
from typing import List, Dict, Any
import json

# === HELPER FUNCTIONS ===

def build_flight_requests_from_airports(airport_groups: Dict[str, List], destinations: List[str], departure_date: str, return_date: str) -> List[Dict]:
    """Convert airport groups from ai_input into flight request format."""
    flight_groups = []
    
    for airport, users_info in airport_groups.items():
        flight_groups.append({
            "departure_city": airport,
            "passenger_count": len(users_info),
            "destinations": destinations,
            "departure_date": departure_date,
            "return_date": return_date,
            "passengers": [user["email"] for user in users_info],
            "passenger_names": [user["name"] for user in users_info]
        })
    
    return flight_groups

async def calculate_date_range_cost(date_range: Dict, airport_groups: Dict, destinations: List[str], flight_preferences: Dict) -> Dict:
    """
    Calculate preliminary total cost for a specific date range.
    Returns cost breakdown and total cost for comparison.
    """
    departure_date = date_range["start_date"].strftime("%Y-%m-%d")
    return_date = date_range["end_date"].strftime("%Y-%m-%d")
    
    try:
        # Build flight groups for this date range
        flight_groups = build_flight_requests_from_airports(
            airport_groups, destinations, departure_date, return_date
        )
        
        # Use flight tool to get preliminary prices
        flight_tool = AmadeusFlightTool()
        
        # Call flight tool once with all groups and destinations
        flight_input = {
            "flight_groups": flight_groups,
            "flight_preferences": flight_preferences
        }
        
        flight_response = flight_tool._call(json.dumps(flight_input))
        
        try:
            flight_data = json.loads(flight_response)
            total_flight_cost = 0
            flight_results = {}
            
            # Check if this is an error response
            if "flight_search_status" in flight_data:
                status = flight_data["flight_search_status"]
                if status.get("status") == "NO_FLIGHTS_FOUND":
                    print(f"  ❌ No flights found: {status.get('message', 'Unknown reason')}")
                    for destination in destinations:
                        flight_results[destination] = 999999  # Penalty cost
                        total_flight_cost += 999999
                    return {
                        "departure_date": departure_date,
                        "return_date": return_date,
                        "total_flight_cost": total_flight_cost,
                        "flight_breakdown": flight_results,
                        "date_range": date_range,
                        "valid": True,  # Still valid - user can book flights manually
                        "flight_search_successful": False,
                        "no_flights_reason": status.get('message', 'No flights found')
                    }
            
            # Process results by destination
            for destination in destinations:
                destination_cost = 0
                valid_flights_found = False
                
                # Sum costs for all departure cities to this destination
                for group_key, dest_flights in flight_data.items():
                    if group_key in ["flight_search_status", "errors_encountered", "search_summary"]:
                        continue  # Skip metadata
                        
                    if destination in dest_flights:
                        dest_data = dest_flights[destination]
                        
                        # Check if this is an error response
                        if isinstance(dest_data, dict) and "error" in dest_data:
                            print(f"  ⚠️ Flight search error for {group_key} -> {destination}: {dest_data.get('error', 'Unknown error')}")
                            continue
                        elif isinstance(dest_data, list) and dest_data:
                            # Take the cheapest flight option
                            cheapest = min(dest_data, key=lambda x: x.get('total_price', float('inf')))
                            if cheapest.get('total_price', 0) > 0:
                                destination_cost += cheapest.get('total_price', 0)
                                valid_flights_found = True
                
                if valid_flights_found and destination_cost > 0:
                    flight_results[destination] = destination_cost
                    total_flight_cost += destination_cost
                    print(f"  ✅ Found flights for {destination}: ${destination_cost}")
                else:
                    # No valid flights found - don't add penalty cost
                    flight_results[destination] = 0
                    print(f"  ❌ No valid flights found for {destination} - users can book manually")
                
        except (json.JSONDecodeError, KeyError) as e:
            # If flight data is invalid, set to 0 - users can book manually
            print(f"  ❌ Failed to parse flight data: {e}")
            for destination in destinations:
                flight_results[destination] = 0
        
        return {
            "departure_date": departure_date,
            "return_date": return_date,
            "total_flight_cost": total_flight_cost,
            "flight_breakdown": flight_results,
            "date_range": date_range,
            "valid": True,  # Always valid - let user proceed even without flight data
            "flight_search_successful": total_flight_cost < 500000  # Track if flights were found
        }
        
    except Exception as e:
        print(f"  ❌ Error calculating costs for date range: {e}")
        return {
            "departure_date": departure_date,
            "return_date": return_date,
            "total_flight_cost": 0,  # Set to 0 instead of penalty
            "flight_breakdown": {},
            "date_range": date_range,
            "valid": True,  # Still valid - user can proceed
            "flight_search_successful": False,
            "error": str(e)
        }

async def find_cheapest_date_range(best_ranges: List[Dict], airport_groups: Dict, destinations: List[str], flight_preferences: Dict) -> Dict:
    """
    Test multiple date ranges and return the one with lowest total cost.
    """
    if not best_ranges:
        return None
    
    print(f"\n💰 Testing {len(best_ranges)} date ranges to find cheapest...")
    
    # Test only 1 date range for cost (to avoid rate limits)
    ranges_to_test = best_ranges[:1]
    cost_results = []
    
    for i, date_range in enumerate(ranges_to_test):
        print(f"  📅 Testing range {i+1}: {date_range['start_date'].strftime('%Y-%m-%d')} to {date_range['end_date'].strftime('%Y-%m-%d')}")
        
        cost_result = await calculate_date_range_cost(date_range, airport_groups, destinations, flight_preferences)
        cost_results.append(cost_result)
        
        if cost_result["valid"]:
            print(f"     💸 Total flight cost: ${cost_result['total_flight_cost']}")
        else:
            print(f"     ❌ No valid flight prices found")
    
    # Find the cheapest valid option
    valid_results = [r for r in cost_results if r["valid"]]
    
    if valid_results:
        cheapest = min(valid_results, key=lambda x: x["total_flight_cost"])
        print(f"\n✅ Selected cheapest date range: {cheapest['departure_date']} to {cheapest['return_date']}")
        print(f"   💰 Total flight cost: ${cheapest['total_flight_cost']}")
        return cheapest
    else:
        # If no valid prices found, fall back to first range
        print(f"\n⚠️ No valid flight prices found, using first available range")
        fallback = best_ranges[0]
        return {
            "departure_date": fallback["start_date"].strftime("%Y-%m-%d"),
            "return_date": fallback["end_date"].strftime("%Y-%m-%d"),
            "total_flight_cost": 0,
            "flight_breakdown": {},
            "date_range": fallback,
            "valid": True,  # Allow trip planning to proceed
            "flight_search_successful": False
        }

# === MAIN PLANNER ===

async def plan_trip(users: List[UserInput]) -> dict:
    # All data aggregation is handled by ai_input.py
    group_profile = get_group_preferences(users)
    trip_data = prepare_ai_input(users)
    best_ranges = get_best_ranges(trip_data["date_to_users"], users)

    if not best_ranges:
        return {"error": "No overlapping availability found."}

    # Check for critical conflicts (already detected by ai_input.py)
    if group_profile.get("conflicts"):
        print("⚠️ Group conflicts detected:")
        for conflict in group_profile["conflicts"]:
            print(f"  - {conflict}")

    # Get destinations from trip group
    from app.services import storage
    group_code = users[0].group_code if users and users[0].group_code else 'DEFAULT_GROUP'
    trip_group = storage.get_trip_group(group_code)
    
    if not trip_group or not trip_group.destinations:
        return {"error": f"No destinations found for group {group_code}. Trip creator must set destinations first."}
    
    top_destinations = trip_group.destinations
    
    # ===== USE PRE-AGGREGATED DATA FROM AI_INPUT =====
    
    # Extract consensus values (already calculated by ai_input.py)
    travel_styles = group_profile.get("travel_styles", {})
    primary_travel_style = max(travel_styles, key=travel_styles.get) if travel_styles else "balanced"
    
    paces = group_profile.get("paces", {})
    primary_pace = max(paces, key=paces.get) if paces else "balanced"
    
    interests = list(group_profile.get("interests", {}).keys())
    
    accommodation_styles = group_profile.get("accommodation_styles", {})
    primary_accommodation_style = max(accommodation_styles, key=accommodation_styles.get) if accommodation_styles else "standard"
    
    trip_duration = group_profile.get("trip_duration_range", {}).get("consensus_duration", 5)
    
    # Derive flight preferences from consensus travel style
    # Note: Nonstop preference disabled to improve availability for international routes
    flight_preferences = {
        "travel_class": "business" if primary_travel_style == "luxury" else "economy",
        "nonstop_preferred": False  # Allow connections for better international availability
    }

    # ===== NEW: FIND CHEAPEST DATE RANGE =====
    cheapest_date_result = await find_cheapest_date_range(
        best_ranges, 
        group_profile["airport_groups"], 
        top_destinations, 
        flight_preferences
    )
    
    if not cheapest_date_result:
        return {"error": "Unable to determine optimal travel dates."}
    
    departure_date = cheapest_date_result["departure_date"]
    return_date = cheapest_date_result["return_date"]
    selected_date_range = cheapest_date_result["date_range"]

    # Convert airport groups to flight requests using optimized dates
    flight_groups = build_flight_requests_from_airports(
        group_profile["airport_groups"], 
        top_destinations, 
        departure_date, 
        return_date
    )

    # Build accommodation details from user profiles (individual data needed for room assignments)
    accommodation_details = []
    for user_profile in group_profile["user_profiles"]:
        accommodation_details.append({
            "email": user_profile["email"],
            "name": user_profile["name"],
            "room_sharing": user_profile.get("room_sharing", "any")
        })

    # Build final preferences object using pre-aggregated data
    user_preferences = {
        "top_destinations": top_destinations,
        "group_size": group_profile["group_size"],
        
        # GROUP PREFERENCES (all pre-aggregated by ai_input.py)
        "travel_style": primary_travel_style,
        "trip_pace": primary_pace,
        "interests": interests,
        "budgets": {
            "budget_min": group_profile["budget_min"],
            "budget_max": group_profile["budget_max"],
            "budget_target": group_profile["budget_target"]
        },
        "group_accommodation_style": primary_accommodation_style,
        
        # FLIGHT DATA
        "flight_groups": flight_groups,
        "flight_preferences": flight_preferences,
        
        # INDIVIDUAL DATA (for room assignments)
        "accommodation_details": accommodation_details,
        
        # TRIP DETAILS
        "trip_duration_days": trip_duration,
        "departure_date": departure_date,
        "return_date": return_date,
        
        # ADDITIONAL CONTEXT
        "conflicts": group_profile.get("conflicts", []),
        "group_profile": group_profile,  # Include full profile for agent context
        "cost_optimization": cheapest_date_result  # Include cost data
    }

    try:
        print("🧳 Trip Planning Summary:")
        print(f"  📍 Destinations: {', '.join(top_destinations)}")
        print(f"  👥 Group size: {group_profile['group_size']} people")
        print(f"  📅 Optimized dates: {departure_date} to {return_date} ({trip_duration} days)")
        print(f"  ✈️ Departure airports: {list(group_profile['airport_groups'].keys())}")
        print(f"  💰 Budget: ${group_profile['budget_min']}-${group_profile['budget_max']}/person")
        print(f"  🏨 Accommodation: {primary_accommodation_style}")
        print(f"  ✈️ Flight class: {flight_preferences['travel_class']}")
        if cheapest_date_result["valid"]:
            print(f"  💸 Estimated flight cost: ${cheapest_date_result['total_flight_cost']} total")
        
        print("\n🤖 Calling AI agent...")
        agent_result = await travel_agent.plan_trip(user_preferences)

        if agent_result.get("success"):
            # NEW: Extract booking links from agent response
            print("\n🔗 Extracting booking links...")
            booking_links = await get_all_booking_links({
                "agent_response": agent_result["agent_response"],
                "preferences_used": user_preferences
            })
            
            # Log booking results
            if booking_links.get('success'):
                summary = booking_links.get('summary', {})
                print(f"✅ Found booking links:")
                print(f"   - Flights: {summary.get('flights', {}).get('total_links', 0)} links for {summary.get('flights', {}).get('total_routes', 0)} routes")
                print(f"   - Hotel: {summary.get('hotel', {}).get('total_links', 0)} links")
                print(f"   - Activities: {summary.get('activities', {}).get('total_links', 0)} links for {summary.get('activities', {}).get('activities_with_booking', 0)} activities")
            else:
                print(f"⚠️ Failed to extract booking links: {booking_links.get('error', 'Unknown error')}")
            
            result = {
                "system": "LangChain Agent with Tools",
                "agent_response": agent_result["agent_response"],
                "preferences_used": user_preferences,
                "date_range": selected_date_range,  # Use the optimized date range
                "group_profile": group_profile,
                "booking_links": booking_links,  # NEW: Include booking links
                "ready_for_email": booking_links.get('success', False),  # NEW: Email ready flag
                "cost_optimization": cheapest_date_result  # NEW: Include cost optimization data
            }
        else:
            result = {"error": agent_result.get("error", "Unknown failure")}

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        result = {"error": str(e)}

    return result