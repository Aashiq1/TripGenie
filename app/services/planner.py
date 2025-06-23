# Updated planner.py with proper booking link integration

from app.models.group_inputs import UserInput
from app.services.ai_input import prepare_ai_input, get_best_ranges, get_group_preferences
from app.services.langchain_travel_agent import travel_agent
from app.services.booking_integration import get_all_booking_links  # NEW IMPORT
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

    # Use the first valid range
    departure_date = best_ranges[0]["start_date"].strftime("%Y-%m-%d")
    return_date = best_ranges[0]["end_date"].strftime("%Y-%m-%d")

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
    flight_preferences = {
        "travel_class": "business" if primary_travel_style == "luxury" else "economy",
        "nonstop_preferred": primary_travel_style != "budget"
    }

    # Convert airport groups to flight requests
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
        "group_profile": group_profile  # Include full profile for agent context
    }

    try:
        print("🧳 Trip Planning Summary:")
        print(f"  📍 Destinations: {', '.join(top_destinations)}")
        print(f"  👥 Group size: {group_profile['group_size']} people")
        print(f"  📅 Dates: {departure_date} to {return_date} ({trip_duration} days)")
        print(f"  ✈️ Departure airports: {list(group_profile['airport_groups'].keys())}")
        print(f"  💰 Budget: ${group_profile['budget_min']}-${group_profile['budget_max']}/person")
        print(f"  🏨 Accommodation: {primary_accommodation_style}")
        print(f"  ✈️ Flight class: {flight_preferences['travel_class']}")
        
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
                "date_range": best_ranges[0],
                "group_profile": group_profile,
                "booking_links": booking_links,  # NEW: Include booking links
                "ready_for_email": booking_links.get('success', False)  # NEW: Email ready flag
            }
        else:
            result = {"error": agent_result.get("error", "Unknown failure")}

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        result = {"error": str(e)}

    return result