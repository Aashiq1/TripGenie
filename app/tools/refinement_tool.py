# tools/refinement_tools.py
"""
Tools specifically for the trip refinement chat agent.
These wrap existing services with a chat-friendly interface.
"""

import json
from typing import Dict, List
from langchain.tools import Tool

from app.services.amadeus_flights import get_flight_offers
from app.services.amadeus_hotels import get_hotel_offers
# DISABLED: Old Tavily-based activity search - will be replaced with new multi-API system
# from app.services.activity_search import ActivitySearchService


class FlightAlternativesTool:
    """
    Tool for finding alternative flights in refinement chat.
    Wraps the existing flight service with natural language parsing.
    """
    
    def __init__(self, current_itinerary: Dict, preferences: Dict):
        self.current_itinerary = current_itinerary
        self.preferences = preferences
        self.name = "search_alternative_flights"
        self.description = (
            "Search for alternative flight options based on natural language requests. "
            "Examples: 'cheaper flights', 'nonstop only', 'later departure', 'business class'"
        )
    
    def _call(self, query: str) -> str:
        """
        Parse natural language query and search for flights.
        """
        try:
            # Parse the query
            query_lower = query.lower()
            
            # Determine which departure city
            departure_city = None
            for city, flight in self.current_itinerary.get('flights', {}).items():
                if city.lower() in query_lower:
                    departure_city = city
                    break
            
            # Default to first city if not specified
            if not departure_city and self.preferences.get('flight_groups'):
                departure_city = self.preferences['flight_groups'][0]['departure_city']
            
            # Parse preferences from natural language
            travel_class = "ECONOMY"
            if "business" in query_lower:
                travel_class = "BUSINESS"
            elif "first" in query_lower:
                travel_class = "FIRST"
            elif "premium" in query_lower:
                travel_class = "PREMIUM_ECONOMY"
            
            nonstop_only = any(word in query_lower for word in ["nonstop", "direct", "no stops"])
            
            # Search flights using existing service
            results = get_flight_offers(
                departure_city=departure_city,
                destination=self.current_itinerary.get('destination', 'BCN'),
                departure_date=self.preferences['departure_date'],
                return_date=self.preferences['return_date'],
                num_adults=self.preferences.get('group_size', 1),
                travel_class=travel_class,
                nonstop_only=nonstop_only
            )
            
            # Format results in chat-friendly way
            if isinstance(results, list) and results:
                response = f"Found {len(results)} alternative flights from {departure_city}:\n\n"
                
                # Sort by price if "cheaper" was mentioned
                if "cheap" in query_lower:
                    results.sort(key=lambda x: x['price_per_person'])
                
                for i, flight in enumerate(results[:5], 1):
                    response += (
                        f"{i}. {flight['airline']} - ${flight['price_per_person']}/person\n"
                        f"   Departure: {flight['departure_time']}\n"
                        f"   Stops: {flight['stops']}"
                    )
                    if flight['stops'] == 0:
                        response += " (nonstop)"
                    response += f"\n   Duration: {flight['duration']}\n\n"
                
                # Add context about current flight
                current = self.current_itinerary['flights'].get(departure_city, {})
                if current:
                    response += f"Current flight: {current.get('airline', 'Unknown')} {current.get('flight_number', '')} - ${current.get('price', 0)}/person"
                
                return response
            else:
                return f"No alternative flights found from {departure_city} with those criteria."
                
        except Exception as e:
            return f"Error searching flights: {str(e)}"


class HotelAlternativesTool:
    """
    Tool for finding alternative hotels in refinement chat.
    """
    
    def __init__(self, current_itinerary: Dict, preferences: Dict):
        self.current_itinerary = current_itinerary
        self.preferences = preferences
        self.name = "search_alternative_hotels"
        self.description = (
            "Search for alternative hotel options based on natural language requests. "
            "Examples: 'luxury hotels', 'budget options', 'near the beach', 'with pool'"
        )
    
    def _call(self, query: str) -> str:
        """
        Parse natural language query and search for hotels.
        """
        try:
            query_lower = query.lower()
            
            # Determine accommodation style
            accommodation_style = "standard"
            if any(word in query_lower for word in ["luxury", "5 star", "five star", "upscale"]):
                accommodation_style = "luxury"
            elif any(word in query_lower for word in ["budget", "cheap", "affordable", "hostel"]):
                accommodation_style = "budget"
            
            # Search hotels using existing service
            results = get_hotel_offers(
                city_code=self.current_itinerary.get('destination', 'BCN'),
                check_in_date=self.preferences['departure_date'],
                check_out_date=self.preferences['return_date'],
                accommodation_preference=accommodation_style
            )
            
            if results:
                response = f"Found {len(results)} {accommodation_style} hotels:\n\n"
                
                for i, hotel in enumerate(results[:5], 1):
                    # Get price range
                    room_prices = [r['price_per_night'] for r in hotel['room_types_available'].values()]
                    min_price = min(room_prices) if room_prices else 0
                    max_price = max(room_prices) if room_prices else 0
                    
                    response += (
                        f"{i}. {hotel['hotel_name']} ({hotel['hotel_rating']}/5)\n"
                        f"   Price range: ${min_price}-${max_price}/night\n"
                        f"   {hotel['address']}\n"
                    )
                    
                    # Add features mentioned in query
                    if "pool" in query_lower:
                        response += "   Pool: Check with hotel\n"
                    if "beach" in query_lower:
                        response += "   Beach access: Check location\n"
                    
                    response += "\n"
                
                # Add current hotel context
                current = self.current_itinerary.get('hotel', {})
                if current:
                    response += f"Current hotel: {current.get('name', 'Unknown')} - ${current.get('price_per_night', 0)}/night"
                
                return response
            else:
                return f"No {accommodation_style} hotels found matching your criteria."
                
        except Exception as e:
            return f"Error searching hotels: {str(e)}"


class ActivityFinderTool:
    """
    Tool for finding activities to add to the itinerary.
    """
    
    def __init__(self, current_itinerary: Dict, preferences: Dict):
        self.current_itinerary = current_itinerary
        self.preferences = preferences
        self.name = "find_activities"
        self.description = (
            "Find activities to add to the itinerary based on natural language requests. "
            "Examples: 'cooking class', 'museum tours', 'beach activities', 'nightlife options'"
        )
    
    def _call(self, query: str) -> str:
        """
        Search for activities based on query.
        """
        try:
            query_lower = query.lower()
            
            # Extract interests from query
            interests = []
            interest_mapping = {
                "food": ["food", "cooking", "culinary", "restaurant", "dining"],
                "culture": ["museum", "art", "history", "culture", "heritage"],
                "adventure": ["adventure", "outdoor", "hiking", "sports", "active"],
                "nightlife": ["night", "club", "bar", "party", "evening"],
                "relaxing": ["spa", "beach", "relax", "wellness"],
                "shopping": ["shopping", "market", "boutique"]
            }
            
            for interest, keywords in interest_mapping.items():
                if any(keyword in query_lower for keyword in keywords):
                    interests.append(interest)
            
            if not interests:
                interests = ["general"]
            
            # Search using existing service
            # activity_search = ActivitySearchService()
            # results = activity_search.search_activities(
            #     destination=self.current_itinerary.get('destination', 'Barcelona'),
            #     interests=interests,
            #     travel_style=self.preferences.get('travel_style', 'standard'),
            #     num_days=1,  # Just search, not full itinerary
            #     trip_pace=self.preferences.get('trip_pace', 'balanced')
            # )
            
            # Extract all activities
            all_activities = []
            # for day_data in results.get('daily_itinerary', {}).values():
            #     if isinstance(day_data, dict) and 'activities' in day_data:
            #         all_activities.extend(day_data['activities'])
            
            # TEMPORARY: Activity search disabled during rebuild
            if all_activities:
                response = f"Found activities matching '{query}':\n\n"
                
                for i, activity in enumerate(all_activities[:5], 1):
                    response += f"{i}. {activity['name']}\n"
                    
                    if activity.get('description'):
                        response += f"   {activity['description'][:100]}...\n"
                    
                    if activity.get('duration'):
                        response += f"   Duration: {activity['duration']} hours\n"
                    
                    if activity.get('price_info'):
                        response += f"   Price: ${activity['price_info']['amount_usd']}/person\n"
                    
                    if activity.get('is_bookable'):
                        response += f"   Booking: Available on {activity.get('booking_platform', 'Direct')}\n"
                    
                    response += "\n"
                
                # Check if activity already exists
                current_activities = self.current_itinerary.get('activities', [])
                response += f"\nNote: You currently have {len(current_activities)} activities planned."
                
                return response
            else:
                return f"Activity search is temporarily disabled during system rebuild. Please check back soon for enhanced activity search with multiple booking platforms."
                
        except Exception as e:
            return f"Error searching activities: {str(e)}"


class CurrentItinerarySummaryTool:
    """
    Tool to show current itinerary summary.
    """
    
    def __init__(self, current_itinerary: Dict, preferences: Dict):
        self.current_itinerary = current_itinerary
        self.preferences = preferences
        self.name = "show_current_itinerary"
        self.description = "Show the current trip itinerary with all bookings and costs"
    
    def _call(self, query: str) -> str:
        """
        Return formatted current itinerary.
        """
        try:
            response = "=== CURRENT TRIP ITINERARY ===\n\n"
            
            # Destination and dates
            response += f"📍 Destination: {self.current_itinerary.get('destination', 'Unknown')}\n"
            response += f"📅 Dates: {self.preferences['departure_date']} to {self.preferences['return_date']}\n"
            response += f"👥 Group Size: {self.preferences.get('group_size', 1)} people\n\n"
            
            # Flights
            response += "✈️ FLIGHTS:\n"
            total_flight_cost = 0
            for city, flight in self.current_itinerary.get('flights', {}).items():
                cost = flight.get('price', 0)
                response += f"From {city}: {flight.get('airline', 'Unknown')} {flight.get('flight_number', '')} - ${cost}/person\n"
                total_flight_cost += cost
            
            # Hotel
            response += "\n🏨 HOTEL:\n"
            hotel = self.current_itinerary.get('hotel', {})
            if hotel:
                nights = self.preferences.get('trip_duration_days', 5)
                nightly_rate = hotel.get('price_per_night', 0)
                hotel_total = nightly_rate * nights
                response += f"{hotel.get('name', 'Unknown')}\n"
                response += f"Rate: ${nightly_rate}/night × {nights} nights = ${hotel_total}\n"
                response += f"Configuration: {hotel.get('room_configuration', 'Unknown')}\n"
            
            # Activities
            response += "\n🎯 ACTIVITIES:\n"
            activities = self.current_itinerary.get('activities', [])
            activity_total = 0
            
            if activities:
                days = {}
                for act in activities:
                    day = act.get('day', 1)
                    if day not in days:
                        days[day] = []
                    days[day].append(act)
                
                for day in sorted(days.keys()):
                    response += f"\nDay {day}:\n"
                    for act in days[day]:
                        price = act.get('price_per_person', 0)
                        activity_total += price
                        response += f"- {act.get('name', 'Unknown')} (${price}/person)\n"
            
            # Total costs
            response += "\n💰 ESTIMATED TOTAL PER PERSON:\n"
            response += f"Flights: ${total_flight_cost}\n"
            response += f"Hotel: ${hotel_total / self.preferences.get('group_size', 2):.0f} (if sharing)\n"
            response += f"Activities: ${activity_total}\n"
            response += f"Food (est): ${100 * self.preferences.get('trip_duration_days', 5)}\n"
            response += f"TOTAL: ${total_flight_cost + (hotel_total / 2) + activity_total + (100 * self.preferences.get('trip_duration_days', 5)):.0f}\n"
            
            return response
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"


# Factory function to create all refinement tools
def create_refinement_tools(current_itinerary: Dict, preferences: Dict) -> List[Tool]:
    """
    Create all refinement tools for the chat agent.
    
    Args:
        current_itinerary: Parsed current trip plan
        preferences: User preferences from planner
        
    Returns:
        List of LangChain Tool objects
    """
    tools = [
        FlightAlternativesTool(current_itinerary, preferences),
        HotelAlternativesTool(current_itinerary, preferences),
        ActivityFinderTool(current_itinerary, preferences),
        CurrentItinerarySummaryTool(current_itinerary, preferences)
    ]
    
    # Convert to LangChain Tools
    langchain_tools = []
    for tool in tools:
        langchain_tools.append(
            Tool(
                name=tool.name,
                description=tool.description,
                func=tool._call
            )
        )
    
    return langchain_tools