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
        Create itinerary for destinations based on user interests and group size.
        
        Input format (JSON):
        {
            "destinations": ["MAD", "BCN"],
            "interests": ["food", "nightlife", "culture"],
            "group_size": 3,
            "trip_duration_days": 5,
            "travel_style": "standard",
            "trip_pace": "balanced",
            "budget_per_person": 1200,
            "departure_date": "2025-07-14"
        }
        """
        try:
            input_data = json.loads(input_str)
            
            destinations = input_data.get("destinations", [])
            interests = input_data.get("interests", [])
            group_size = input_data.get("group_size", 2)
            trip_duration = input_data.get("trip_duration_days", 5)
            travel_style = input_data.get("travel_style", "standard")
            trip_pace = input_data.get("trip_pace", "balanced")
            budget_per_person = input_data.get("budget_per_person", 1000)
            departure_date = input_data.get("departure_date")  # NEW: Get departure date
            
            if not destinations:
                return json.dumps({"error": "No destinations provided"})
            
            # Process each destination
            results = {}
            
            for destination in destinations:
                # Search for activities using enhanced search with departure date
                search_results = self.activity_service.search_activities(
                    destination=destination,
                    interests=interests,
                    travel_style=travel_style,
                    num_days=trip_duration,
                    trip_pace=trip_pace,
                    departure_date=departure_date  # NEW: Pass departure date for smart assignment
                )
                
                # Format the response
                formatted_result = self._format_itinerary_response(
                    search_results, 
                    destination, 
                    trip_duration
                )
                
                results[destination] = formatted_result
            
            return json.dumps(results, indent=2)
            
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON input"})
        except Exception as e:
            return json.dumps({"error": f"Failed to create itinerary: {str(e)}"})
    
    def _format_itinerary_response(self, 
                                  search_results: Dict, 
                                  destination: str,
                                  num_days: int) -> Dict:
        """Format search results into a comprehensive itinerary response."""
        daily_itinerary = search_results.get("daily_itinerary", {})
        trip_totals = daily_itinerary.pop("trip_totals", {})
        trip_context = search_results.get("trip_context", {})  # NEW: Get trip context
        
        # Format daily activities
        formatted_days = {}
        all_bookable_links = []
        total_bookable_activities = 0
        
        for day_key, day_data in daily_itinerary.items():
            if not isinstance(day_data, dict):
                continue
                
            activities = day_data.get("activities", [])
            formatted_activities = []
            
            for activity in activities:
                formatted_activity = {
                    "name": activity.get("name"),
                    "description": activity.get("description"),
                    "duration_hours": activity.get("duration", 2),
                    "interest_category": activity.get("interest"),
                    "activity_type": activity.get("activity_type"),
                    "booking_available": activity.get("is_bookable", False)
                }
                
                # Add pricing information with disclaimers
                if activity.get("price_info"):
                    price_info = activity["price_info"]
                    formatted_activity["price"] = {
                        "display": price_info["price_string"],
                        "amount_usd": price_info["amount_usd"],
                        "per_person": price_info.get("per_person", True),
                        "confidence": price_info.get("confidence", "medium"),
                        "disclaimer": "Estimated price from web search - may not reflect current rates"
                    }
                else:
                    formatted_activity["price"] = {
                        "display": "See booking platform",
                        "amount_usd": None,
                        "per_person": True,
                        "confidence": "none",
                        "disclaimer": "Current pricing available on booking platform"
                    }
                
                # Add booking information if available
                if activity.get("is_bookable"):
                    formatted_activity["booking_info"] = {
                        "platform": activity.get("booking_platform"),
                        "booking_url": activity.get("booking_url"),
                        "note": "Click to check current availability and pricing"
                    }
                    
                    # Track for summary
                    all_bookable_links.append({
                        "activity": activity["name"],
                        "platform": activity["booking_platform"],
                        "url": activity["booking_url"],
                        "day": day_data.get("day_number", int(day_key.split("_")[1]))
                    })
                    total_bookable_activities += 1
                
                formatted_activities.append(formatted_activity)
            
            # Enhanced day formatting with smart assignment info
            day_number = int(day_key.split("_")[1])
            formatted_days[day_key] = {
                "day_number": day_number,
                "day_label": day_data.get("date", f"Day {day_number}"),  # NEW: Include day label
                "weekday": day_data.get("weekday", ""),  # NEW: Include weekday
                "is_weekend": day_data.get("is_weekend", False),  # NEW: Weekend indicator
                "day_theme": day_data.get("day_theme", "exploration"),  # NEW: Day theme
                "activities": formatted_activities,
                "total_duration_hours": day_data.get("total_duration", 8),
                "bookable_activities": day_data.get("bookable_count", 0),
                "estimated_cost_notes": [
                    "Prices shown are estimates from web search",
                    "Click booking links for current pricing and availability",
                    "Actual costs may vary by date and season"
                ]
            }
        
        # Create comprehensive cost summary with disclaimers
        activity_costs = trip_totals.get("total_activity_cost_usd", 0)
        
        cost_summary = {
            "pricing_disclaimer": "⚠️ IMPORTANT: All prices are estimates from web search and may not be current",
            "pricing_notes": [
                "Prices extracted from web content are for reference only",
                "Actual pricing may vary significantly by date, season, and availability", 
                "Some activities may offer group discounts or package deals",
                "Always check booking platforms for current rates before purchasing"
            ],
            "estimated_activity_total_usd": activity_costs if activity_costs > 0 else None,
            "estimated_food_per_day": 50,  # More conservative estimate
            "total_bookable_activities": total_bookable_activities,
            "budget_recommendations": [
                f"Budget ${max(100, activity_costs * 1.3):.0f} for activities (30% buffer)" if activity_costs > 0 else "Budget $150-300 for activities depending on choices",
                f"Budget ${50 * num_days} for food ({num_days} days at $50/day)",
                "Consider purchasing tickets in advance for popular attractions",
                "Look for combo tickets and city passes for savings"
            ]
        }
        
        # Enhanced summary with smart assignment info
        summary = {
            "destination": destination,
            "total_days": num_days,
            "total_activities": search_results.get("total_activities_found", 0),
            "bookable_activities": total_bookable_activities,
            "booking_platforms_found": list(set(
                link["platform"] for link in all_bookable_links if link.get("platform")
            )),
            "quality_notes": [
                f"Found {total_bookable_activities} activities with direct booking available",
                "Activities selected based on group interests and travel style",
                "All activities are from verified booking platforms"
            ],
            # NEW: Smart assignment summary
            "smart_features": {
                "day_specific_assignment": trip_totals.get("smart_assignment_used", False),
                "weekend_optimized": trip_totals.get("nightlife_optimized", False),
                "weekend_days": trip_totals.get("weekend_days", []),
                "context_aware_search": True
            }
        }
        
        return {
            "daily_itinerary": formatted_days,
            "cost_summary": cost_summary,
            "summary": summary,
            "booking_links": all_bookable_links
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