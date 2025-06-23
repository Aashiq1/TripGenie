# tools/itinerary_tool.py
"""LangChain tool for generating activity itineraries with booking links."""

import json
from typing import Dict, List, Optional
from langchain.tools import Tool
from app.services.activity_search import ActivitySearchService
from app.services.tavily_client import TavilyClient

class ItineraryTool:
    """
    LangChain tool for generating daily itineraries with real activities and booking links.
    """
    
    def __init__(self):
        self.name = "itinerary_generator"
        self.description = (
            "Generate daily activity itineraries with booking links for a destination. "
            "Input JSON with: "
            "- destination: city name (e.g., 'Barcelona') "
            "- interests: list of interests (e.g., ['food', 'culture', 'adventure']) "
            "- travel_style: 'budget', 'standard', or 'luxury' "
            "- num_days: number of days (e.g., 5) "
            "- trip_pace: 'chill', 'balanced', or 'fast' "
            "Returns day-by-day activities with descriptions, durations, and direct booking links where available."
        )
        
        # Initialize services
        self.tavily_client = TavilyClient()
        self.activity_service = ActivitySearchService(self.tavily_client)
    
    def _call(self, input_str: str) -> str:
        """
        Generate itinerary based on destination and preferences.
        
        Args:
            input_str: JSON string with search parameters
            
        Returns:
            JSON string with daily itinerary including booking links
        """
        try:
            # Parse input
            data = json.loads(input_str)
            
            destination = data.get("destination")
            interests = data.get("interests", ["culture", "food"])
            travel_style = data.get("travel_style", "standard")
            num_days = data.get("num_days", 5)
            trip_pace = data.get("trip_pace", "balanced")
            
            # Validate inputs
            if not destination:
                return json.dumps({
                    "error": "Destination is required",
                    "example_input": {
                        "destination": "Barcelona",
                        "interests": ["food", "culture"],
                        "travel_style": "standard",
                        "num_days": 5,
                        "trip_pace": "balanced"
                    }
                })
            
            # Search for activities using Tavily
            search_results = self.activity_service.search_activities(
                destination=destination,
                interests=interests,
                travel_style=travel_style,
                num_days=num_days,
                trip_pace=trip_pace
            )
            
            # Format the response for the agent
            formatted_response = self._format_itinerary_response(
                search_results,
                destination,
                num_days
            )
            
            return json.dumps(formatted_response, indent=2)
            
        except json.JSONDecodeError:
            return json.dumps({
                "error": "Invalid JSON input",
                "example_input": {
                    "destination": "Barcelona",
                    "interests": ["food", "culture"],
                    "travel_style": "standard",
                    "num_days": 5,
                    "trip_pace": "balanced"
                }
            })
        except Exception as e:
            # If Tavily fails, return a basic itinerary
            return json.dumps({
                "error": f"Search failed: {str(e)}",
                "fallback_itinerary": self._generate_fallback_itinerary(
                    data.get("destination", "Unknown"),
                    data.get("num_days", 5),
                    data.get("interests", ["culture", "food"])
                )
            })
    
    def _format_itinerary_response(self, 
                                  search_results: Dict, 
                                  destination: str,
                                  num_days: int) -> Dict:
        """
        Format the search results into a structured itinerary response with costs.
        """
        daily_itinerary = search_results.get("daily_itinerary", {})
        all_bookable_links = search_results.get("all_bookable_links", [])
        trip_totals = daily_itinerary.pop("trip_totals", {})  # Extract totals
        
        # Format each day
        formatted_days = {}
        total_bookable_activities = 0
        
        for day_key, day_data in daily_itinerary.items():
            activities = day_data.get("activities", [])
            
            formatted_activities = []
            for activity in activities:
                formatted_activity = {
                    "name": activity.get("name"),
                    "description": activity.get("description"),
                    "duration_hours": activity.get("duration", 2),
                    "interest_category": activity.get("interest"),
                    "booking_available": activity.get("is_bookable", False)
                }
                
                # Add pricing information
                if activity.get("price_info"):
                    formatted_activity["price"] = {
                        "display": activity["price_info"]["price_string"],
                        "amount_usd": activity["price_info"]["amount_usd"],
                        "per_person": activity["price_info"].get("per_person", True)
                    }
                
                # Add booking information if available
                if activity.get("is_bookable"):
                    formatted_activity["booking_info"] = {
                        "platform": activity.get("booking_platform"),
                        "booking_url": activity.get("booking_url")
                    }
                    total_bookable_activities += 1
                
                formatted_activities.append(formatted_activity)
            
            formatted_days[day_key] = {
                "day_number": int(day_key.split("_")[1]),
                "activities": formatted_activities,
                "total_duration_hours": day_data.get("total_duration", 8),
                "bookable_activities": day_data.get("bookable_count", 0),
                "estimated_cost_usd": day_data.get("day_cost_usd", 0),
                "cost_summary": day_data.get("day_cost_summary", {})
            }
        
        # Create comprehensive cost summary
        activity_costs = trip_totals.get("total_activity_cost_usd", 0)
        
        cost_summary = {
            "activity_total_usd": activity_costs,
            "average_per_day_usd": trip_totals.get("average_per_day", 0),
            "estimated_food_per_day": 100,  # Standard estimate
            "estimated_food_total": 100 * num_days,
            "activities_plus_food": activity_costs + (100 * num_days),
            "cost_breakdown_by_category": trip_totals.get("cost_breakdown", {}),
            "budget_notes": [
                f"Activity costs: ${activity_costs} for {num_days} days",
                f"Estimated food/meals: ${100 * num_days} (${100}/day)",
                f"Total (excluding accommodation): ${activity_costs + (100 * num_days)}"
            ]
        }
        
        # Create summary
        summary = {
            "destination": destination,
            "total_days": num_days,
            "total_activities": search_results.get("total_activities_found", 0),
            "bookable_activities": total_bookable_activities,
            "booking_platforms_found": list(set(
                link["platform"] for link in all_bookable_links
            ))
        }
        
        return {
            "status": "success",
            "summary": summary,
            "cost_summary": cost_summary,
            "daily_itinerary": formatted_days,
            "booking_links": self._categorize_booking_links(all_bookable_links),
            "search_metadata": {
                "powered_by": "Tavily real-time search",
                "note": "Prices shown where available. Some activities may require on-site payment."
            }
        }
    
    def _categorize_booking_links(self, booking_links: List[Dict]) -> Dict:
        """
        Categorize booking links by platform for easy access.
        
        Args:
            booking_links: List of all booking links
            
        Returns:
            Links organized by platform
        """
        categorized = {}
        
        for link in booking_links:
            platform = link.get("platform", "Unknown")
            if platform not in categorized:
                categorized[platform] = []
            
            categorized[platform].append({
                "activity": link.get("activity"),
                "url": link.get("url"),
                "price": link.get("price_info")
            })
        
        return categorized
    
    def _generate_fallback_itinerary(self, 
                                    destination: str, 
                                    num_days: int, 
                                    interests: List[str]) -> Dict:
        """
        Generate a basic fallback itinerary if search fails.
        
        Args:
            destination: Destination city
            num_days: Number of days
            interests: List of interests
            
        Returns:
            Basic itinerary structure
        """
        daily_plan = {}
        
        # Generic activities based on interests
        generic_activities = {
            "culture": [
                "Explore the historic city center",
                "Visit the main museum",
                "Tour historical landmarks",
                "Discover local architecture"
            ],
            "food": [
                "Take a food walking tour",
                "Visit the central market",
                "Try local restaurant recommendations",
                "Join a cooking class"
            ],
            "adventure": [
                "Outdoor excursion near the city",
                "Active tour or hike",
                "Water sports or activities",
                "Bike tour of the area"
            ],
            "nightlife": [
                "Explore entertainment districts",
                "Experience local nightlife",
                "Attend a show or performance",
                "Visit popular evening venues"
            ],
            "relaxing": [
                "Spa or wellness experience",
                "Leisurely park visit",
                "Beach or waterfront time",
                "Casual cafe exploration"
            ],
            "shopping": [
                "Visit main shopping areas",
                "Explore local markets",
                "Boutique shopping tour",
                "Souvenir hunting"
            ]
        }
        
        for day in range(1, min(num_days + 1, 8)):  # Cap at 7 days
            activities = []
            
            # Pick activities based on interests
            for interest in interests[:3]:  # Max 3 activities per day
                if interest in generic_activities:
                    activity_list = generic_activities[interest]
                    if activity_list:
                        activity = activity_list[(day - 1) % len(activity_list)]
                        activities.append({
                            "name": f"{activity} in {destination}",
                            "description": f"Recommended {interest} activity",
                            "duration_hours": 2.5,
                            "interest_category": interest,
                            "booking_available": False,
                            "note": "Search failed - generic suggestion"
                        })
            
            daily_plan[f"day_{day}"] = {
                "day_number": day,
                "activities": activities,
                "total_duration_hours": len(activities) * 2.5,
                "bookable_activities": 0
            }
        
        return {
            "status": "fallback",
            "note": "Unable to search for specific activities - showing generic suggestions",
            "daily_itinerary": daily_plan,
            "summary": {
                "destination": destination,
                "total_days": num_days,
                "search_failed": True
            }
        }


# Function to create the tool for LangChain
def get_itinerary_tool() -> Tool:
    """Create a LangChain Tool instance for itinerary generation."""
    tool = ItineraryTool()
    return Tool(
        name=tool.name,
        description=tool.description,
        func=tool._call
    )