# Updated planner.py with proper booking link integration

from app.models.group_inputs import UserInput
from app.services.ai_input import prepare_ai_input, get_best_ranges, get_group_preferences
from app.services.langchain_travel_agent import travel_agent
from app.services.agent_parser import AgentResponseParser  # NEW: parse itinerary for alignment
from app.services.booking_integration import get_all_booking_links  # NEW IMPORT
from app.services.amadeus_flights import get_flight_offers, get_cheapest_date_candidates_for_window  # NEW: Use Amadeus as source of truth for flights + calendar narrowing
from app.services.amadeus_location_lookup import get_airport_code_with_fallback  # NEW IMPORT FOR DYNAMIC IATA LOOKUP
from app.tools.amadeus_flight_tool import AmadeusFlightTool  # NEW IMPORT FOR COST CHECKING
from app.tools.amadeus_hotel_tool import HotelSearchTool  # NEW: Hotel recommendations (recommended + alternates)
from typing import List, Dict, Any
import json
import re
from datetime import datetime

# === HELPER FUNCTIONS ===

def build_flight_requests_from_airports(airport_groups: Dict[str, List], destination: str, departure_date: str, return_date: str) -> List[Dict]:
    """Convert airport groups from ai_input into flight request format."""
    flight_groups = []
    
    # Convert city name to airport code for flight search using dynamic Amadeus lookup
    airport_destination = get_airport_code_with_fallback(destination)
    
    for airport, users_info in airport_groups.items():
        flight_groups.append({
            "departure_city": airport,
            "passenger_count": len(users_info),
            "destinations": [airport_destination],  # Use airport code for flights (keeping array format for flight tool compatibility)
            "departure_date": departure_date,
            "return_date": return_date,
            "passengers": [user["email"] for user in users_info],
            "passenger_names": [user["name"] for user in users_info]
        })
    
    return flight_groups

async def calculate_date_range_cost(date_range: Dict, airport_groups: Dict, destination: str, flight_preferences: Dict) -> Dict:
    """
    Calculate preliminary total cost for a specific date range.
    Returns cost breakdown and total cost for comparison.
    """
    departure_date = date_range["start_date"].strftime("%Y-%m-%d")
    return_date = date_range["end_date"].strftime("%Y-%m-%d")
    
    try:
        # Build flight groups for this date range
        flight_groups = build_flight_requests_from_airports(
            airport_groups, destination, departure_date, return_date
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
            
            # Process results for the destination
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

async def find_cheapest_date_range(best_ranges: List[Dict], airport_groups: Dict, destination: str, flight_preferences: Dict) -> Dict:
    """
    Test multiple date ranges and return the one with lowest total cost.
    """
    if not best_ranges:
        return None
    
    print(f"\n💰 Evaluating date ranges to find cheapest...")

    # === NEW: Narrow candidate windows using calendar within each availability window ===
    try:
        from datetime import datetime as _dt
        # Resolve destination to IATA code
        dest_airport = get_airport_code_with_fallback(destination)

        # Build a mapping from (dep, ret) to aggregated price across origins
        window_price_map: Dict[tuple, float] = {}
        window_coverage_map: Dict[tuple, int] = {}

        # Flight preference mapping
        travel_class = ("BUSINESS" if flight_preferences.get("travel_class") == "business" else "ECONOMY")
        nonstop_only = bool(flight_preferences.get("nonstop_preferred", False))

        for r in best_ranges:
            window_start = r["start_date"]
            window_end = r["end_date"]
            duration_days = r["duration"]
            for origin_airport, users_info in airport_groups.items():
                group_size = len(users_info)
                candidates = get_cheapest_date_candidates_for_window(
                    departure_city=origin_airport,
                    destination=dest_airport,
                    window_start=window_start,
                    window_end=window_end,
                    trip_duration_days=duration_days,
                    num_adults=group_size,
                    travel_class=travel_class,
                    nonstop_only=nonstop_only,
                    max_candidates=3
                )
                for c in candidates:
                    key = (c["departure_date"], c["return_date"])
                    window_price_map[key] = window_price_map.get(key, 0.0) + float(c.get("min_total_price", 0.0))
                    window_coverage_map[key] = window_coverage_map.get(key, 0) + 1

        # Rank keys by coverage across origins, then by aggregated price
        scored_keys = sorted(
            window_price_map.keys(),
            key=lambda k: (-window_coverage_map.get(k, 0), window_price_map.get(k, float("inf")))
        )

        # Convert keys back to date_range objects limited to availability
        ranges_to_test: List[Dict] = []
        for k in scored_keys:
            dep = _dt.strptime(k[0], "%Y-%m-%d").date()
            ret = _dt.strptime(k[1], "%Y-%m-%d").date()
            duration = (ret - dep).days + 1
            # Ensure it fits within at least one availability window
            fits = False
            for r in best_ranges:
                if dep >= r["start_date"] and ret <= r["end_date"]:
                    fits = True
                    break
            if not fits:
                continue
            ranges_to_test.append({
                "start_date": dep,
                "end_date": ret,
                "duration": duration,
                # preserve structure fields if needed by downstream
                "users": r.get("users", []),
                "user_count": r.get("user_count", 0),
                "missing_users": r.get("missing_users", []),
                "airport_breakdown": r.get("airport_breakdown", {}),
                "coverage_percent": r.get("coverage_percent", 0)
            })
            if len(ranges_to_test) >= 3:
                break

        if not ranges_to_test:
            ranges_to_test = best_ranges[:1]
        print(f"  📉 Narrowed to {len(ranges_to_test)} candidate window(s) using calendar pricing")
    except Exception as _e:
        # Safe fallback
        ranges_to_test = best_ranges[:1]
        print("  ⚠️ Calendar narrowing unavailable; testing default window only")
    cost_results = []
    
    for i, date_range in enumerate(ranges_to_test):
        print(f"  📅 Testing range {i+1}: {date_range['start_date'].strftime('%Y-%m-%d')} to {date_range['end_date'].strftime('%Y-%m-%d')}")
        
        cost_result = await calculate_date_range_cost(date_range, airport_groups, destination, flight_preferences)
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
    
    if not trip_group or not trip_group.destination:
        return {"error": f"No destination found for group {group_code}. Trip creator must set destination first."}
    
    destination = trip_group.destination
    
    # ===== USE PRE-AGGREGATED DATA FROM AI_INPUT =====
    
    # Extract consensus values (already calculated by ai_input.py)
    travel_styles = group_profile.get("travel_styles", {})
    primary_travel_style = max(travel_styles, key=travel_styles.get) if travel_styles else "balanced"
    
    paces = group_profile.get("paces", {})
    primary_pace_raw = max(paces, key=paces.get) if paces else "balanced"
    # Map group pace (chill/balanced/fast) to activity engine pace (relaxed/balanced/packed)
    pace_map = {"chill": "relaxed", "balanced": "balanced", "fast": "packed"}
    primary_pace = pace_map.get(str(primary_pace_raw).lower(), "balanced")

    # Normalize interests to canonical categories used by the activity system
    def _normalize_interests(interest_counts: Dict[str, int]) -> List[str]:
        synonyms_to_category = {
            "food": "Food & Cuisine", "restaurant": "Food & Cuisine", "restaurants": "Food & Cuisine",
            "cuisine": "Food & Cuisine", "dining": "Food & Cuisine",
            "museum": "Museums & Art", "museums": "Museums & Art", "art": "Museums & Art", "art museum": "Museums & Art",
            "hiking": "Nature & Hiking", "hike": "Nature & Hiking", "outdoors": "Nature & Hiking", "nature": "Nature & Hiking",
            "architecture": "Architecture", "historic": "History", "history": "History",
            "shopping": "Shopping", "market": "Local Markets", "markets": "Local Markets", "local markets": "Local Markets",
            "photography": "Photography", "beach": "Beaches", "beaches": "Beaches",
            "nightlife": "Nightlife", "bars": "Nightlife", "bar": "Nightlife",
            "adventure": "Adventure Sports", "sports": "Adventure Sports",
            "sightseeing": "sightseeing"
        }

        sorted_interests = sorted(interest_counts.items(), key=lambda kv: kv[1], reverse=True)
        mapped: List[str] = []
        seen = set()
        for raw_name, _count in sorted_interests:
            key = raw_name.strip().lower()
            category = synonyms_to_category.get(key)
            if category is None:
                if "museum" in key or "art" in key:
                    category = "Museums & Art"
                elif "hiking" in key or "trail" in key or "park" in key:
                    category = "Nature & Hiking"
                elif "food" in key or "restaurant" in key or "cuisine" in key:
                    category = "Food & Cuisine"
                elif "market" in key:
                    category = "Local Markets"
                elif "photo" in key:
                    category = "Photography"
                elif "beach" in key or "coast" in key:
                    category = "Beaches"
                elif "night" in key or "club" in key or "bar" in key:
                    category = "Nightlife"
                elif "architec" in key:
                    category = "Architecture"
                elif "shop" in key:
                    category = "Shopping"
                elif "adventure" in key or "climb" in key:
                    category = "Adventure Sports"
            if category and category not in seen:
                seen.add(category)
                mapped.append(category)
        if not mapped:
            mapped = ["Museums & Art", "Food & Cuisine", "Nature & Hiking"]
        return mapped[:7]

    interests = _normalize_interests(group_profile.get("interests", {}))
    
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
        destination, 
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
        destination, 
        departure_date, 
        return_date
    )

    # ===== NEW: FETCH FLIGHTS FROM AMADEUS AS SOURCE-OF-TRUTH =====
    # For each departure city, fetch offers and select the cheapest
    amadeus_flights_by_city: Dict[str, Dict[str, Any]] = {}
    
    def _duration_to_minutes(duration_iso: str) -> int:
        """Convert ISO-8601 duration (e.g., 'PT10H25M') to minutes."""
        if not isinstance(duration_iso, str):
            return 0
        hours = 0
        minutes = 0
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", duration_iso)
        if match:
            if match.group(1):
                hours = int(match.group(1))
            if match.group(2):
                minutes = int(match.group(2))
        return hours * 60 + minutes

    def _score_offer(offer: Dict[str, Any], prefs: Dict[str, Any]) -> tuple:
        """Lower tuple is better. Prioritize nonstop if preferred, then shortest duration, then price."""
        stops = int(offer.get("stops", 0) or 0)
        duration_minutes = _duration_to_minutes(offer.get("duration", ""))
        price = float(offer.get("total_price", float("inf")))
        nonstop_preferred = bool(prefs.get("nonstop_preferred", False))
        
        # If nonstop preferred, heavily penalize stops
        stop_penalty = stops if not nonstop_preferred else (0 if stops == 0 else 10 + stops)
        return (stop_penalty, duration_minutes if duration_minutes > 0 else 10_000_000, price)
    for group in flight_groups:
        try:
            from_city = group["departure_city"]
            passenger_count = group["passenger_count"]
            # We pass the airport code destination used earlier by build_flight_requests_from_airports
            dest_airport = group["destinations"][0]
            offers = get_flight_offers(
                departure_city=from_city,
                destination=dest_airport,
                departure_date=departure_date,
                return_date=return_date,
                num_adults=passenger_count,
                travel_class=("BUSINESS" if flight_preferences["travel_class"] == "business" else "ECONOMY"),
                nonstop_only=flight_preferences.get("nonstop_preferred", False)
            )

            if isinstance(offers, list) and len(offers) > 0:
                # Select best offer according to preferences (nonstop preference → duration → price)
                best_offer = min(offers, key=lambda x: _score_offer(x, flight_preferences))
                # Attach dates and flags for clarity downstream
                amadeus_flights_by_city[from_city] = {
                    **best_offer,
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "subject_to_availability": True,
                    "source": "amadeus"
                }
        except Exception as _e:
            # Continue even if a particular city fails; booking links layer will add search links
            continue

    def _align_itinerary_with_arrivals(agent_text: str, flights_by_city: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Parse itinerary and adjust Day 1 based on arrival time window.
        Returns a dict like {"daily_itinerary": {...}} suitable for frontend.
        """
        try:
            parser = AgentResponseParser()
            parsed = parser.extract_activity_data(agent_text) or {}
            daily = parsed.get("daily_itinerary", {})
            if not daily:
                return parsed

            # Collect arrival times
            arrival_times: List[datetime] = []
            for _city, info in flights_by_city.items():
                at = info.get("arrival_time")
                if isinstance(at, str):
                    try:
                        arrival_times.append(datetime.fromisoformat(at.replace("Z", "+00:00")))
                    except Exception:
                        pass

            if not arrival_times:
                return parsed

            earliest = min(arrival_times)
            latest = max(arrival_times)
            spread_hours = (latest - earliest).total_seconds() / 3600.0

            # Policy: if latest arrival after 17:00 local-ish OR spread > 6h, don't schedule day 1
            latest_hour = latest.hour
            if spread_hours > 6 or latest_hour >= 17:
                # Find day_1
                # Normalize keys like 'day_1'
                day1_key = None
                for k in daily.keys():
                    if isinstance(k, str) and k.lower().startswith("day_"):
                        try:
                            if int(k.split("_", 1)[1]) == 1:
                                day1_key = k
                                break
                        except Exception:
                            continue
                if day1_key and isinstance(daily.get(day1_key), dict):
                    # Replace with arrival-only note
                    daily[day1_key]["activities"] = []
                    daily[day1_key]["day_label"] = daily[day1_key].get("day_label", "Day 1") + " (Arrival Day)"
                    daily[day1_key]["note"] = "Group arrivals are spread; no scheduled activities. Rest and check-in."

            return {"daily_itinerary": daily}
        except Exception:
            return {}

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
        "top_destinations": [destination],  # Keep original destination for activities (array format for compatibility)
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
        print(f"  📍 Destination: {destination}")
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
                "preferences_used": user_preferences,
                # Prefer these flights over anything parsed from the agent text
                "flights_override": amadeus_flights_by_city
            })

            # NEW: Produce hotel recommendations using HotelSearchTool
            try:
                import json as _json
                hotel_tool = HotelSearchTool()
                # Use destination airport code already resolved by flight_groups conversion
                dest_airport_code = get_airport_code_with_fallback(destination)
                hotel_input = {
                    "destinations": [dest_airport_code],
                    "check_in": departure_date,
                    "check_out": return_date,
                    "group_accommodation_style": primary_accommodation_style,
                    "accommodation_details": accommodation_details
                }
                hotel_output_raw = hotel_tool._call(_json.dumps(hotel_input))
                hotel_output = _json.loads(hotel_output_raw)
                # Extract recommendations for the destination code
                hotel_block = None
                if isinstance(hotel_output, dict):
                    hotel_block = hotel_output.get(dest_airport_code) or hotel_output.get(destination) or hotel_output
                hotel_recommendations = None
                if isinstance(hotel_block, dict):
                    rec = hotel_block.get("recommended")
                    alts = hotel_block.get("alternates", [])
                    all_hotels = hotel_block.get("hotels", [])
                    if rec or alts or all_hotels:
                        hotel_recommendations = {
                            "recommended": rec,
                            "alternates": alts,
                            "all": all_hotels
                        }
            except Exception as _e:
                hotel_recommendations = None

            # Align itinerary to arrivals and surface structured itinerary for frontend
            aligned_itinerary = _align_itinerary_with_arrivals(
                agent_result["agent_response"],
                amadeus_flights_by_city
            )
            
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
                "cost_optimization": cheapest_date_result,  # NEW: Include cost optimization data
                # Surface the flight selections and disclaimers in the plan result for API/UI
                "flights": {
                    "source": "amadeus",
                    "subject_to_availability": True,
                    "by_departure_city": amadeus_flights_by_city
                },
                # NEW: Surface hotel recommendations for UI (recommended + alternates)
                **({"hotel_recommendations": hotel_recommendations} if hotel_recommendations else {}),
                # Provide aligned itinerary so the UI can avoid day-1 scheduling when arrivals are late or spread
                **(aligned_itinerary if aligned_itinerary else {})
            }
        else:
            result = {"error": agent_result.get("error", "Unknown failure")}

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        result = {"error": str(e)}

    return result