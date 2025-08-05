# app/tools/activity_planning_tool.py
"""
LangChain tool for planning activities using Google Places API and future APIs.
Distributes activities across trip days intelligently.
"""

import json
from typing import Dict, List, Any
from app.services.activity_providers import ActivityAggregator


class ActivityPlanningTool:
    """
    Tool for creating a complete activity itinerary using real APIs.
    Integrates Google Places and can be extended for GetYourGuide, Viator, etc.
    """
    
    def __init__(self):
        self.name = "plan_activities"
        self.description = (
            "Create a day-by-day activity itinerary for a destination using real APIs. "
            "Input should be JSON with: destination, interests, trip_duration_days, travel_style, trip_pace, budget_per_person. "
            "Returns structured daily itinerary with real activities, timing, and costs. "
            "Intelligently distributes activities based on group interests priority and trip pace preferences. "
            "Uses Google Places API with future support for GetYourGuide and Viator."
        )
        self.activity_aggregator = ActivityAggregator()
    
    def _call(self, input_str: str) -> str:
        """
        Plan activities for the trip using real API data.
        
        Args:
            input_str: JSON string with destination, interests, trip_duration_days, travel_style, budget_per_person
            
        Returns:
            Formatted string with day-by-day activity plan
        """
        try:
            input_data = json.loads(input_str)
            
            destination = input_data.get("destination")
            interests = input_data.get("interests", [])
            trip_duration = int(input_data.get("trip_duration_days", 5))
            travel_style = input_data.get("travel_style", "balanced")
            trip_pace = input_data.get("trip_pace", "balanced")
            budget_per_person = input_data.get("budget_per_person", 1000)
            
            if not destination:
                return "Error: Destination is required for activity planning."
            
            if not interests:
                interests = ["Food & Cuisine", "Museums & Art"]  # Default interests
            
            # Get activities from all providers (currently Google Places, future: GetYourGuide, Viator)
            activities = self.activity_aggregator.get_combined_activities(
                destination=destination,
                interests=interests,
                travel_style=travel_style,
                max_per_provider=20
            )
            
            if not activities:
                return f"Error: No activities found for {destination}. Try different interests or destination."
            
            # Plan daily itinerary
            daily_itinerary = self._distribute_activities_across_days(
                activities, trip_duration, budget_per_person, trip_pace, interests
            )
            
            # Format response
            return self._format_itinerary_response(daily_itinerary, destination, trip_duration)
            
        except json.JSONDecodeError:
            return "Error: Input must be valid JSON with destination, interests, trip_duration_days, travel_style, trip_pace, budget_per_person"
        except Exception as e:
            return f"Error planning activities: {str(e)}"
    
    def _distribute_activities_across_days(self, activities: List[Dict], trip_duration: int, budget_per_person: int, trip_pace: str, interests: List[str]) -> Dict[int, List[Dict]]:
        """
        Intelligently distribute activities across trip days based on group preferences.
        
        Args:
            activities: List of activity dictionaries from Google Places
            trip_duration: Number of days for the trip
            budget_per_person: Budget per person for activities
            trip_pace: Group pace preference (relaxed/balanced/packed)
            interests: Group interests in priority order
            
        Returns:
            Dictionary mapping day numbers to lists of activities
        """
        daily_itinerary = {}
        
        # Calculate budget allocation
        activity_budget_total = budget_per_person * 0.3  # 30% of budget for activities
        budget_per_day = activity_budget_total / trip_duration
        
        # Categorize activities by type for better distribution
        activity_categories = {
            "cultural": [],
            "dining": [],
            "outdoor": [],
            "shopping": [],
            "historical": [],
            "nightlife": [],
            "sightseeing": []
        }
        
        for activity in activities:
            category = activity.get("activity_type", "sightseeing")
            activity_categories[category].append(activity)
        
        # Determine activities per day based on trip pace
        pace_config = {
            "relaxed": {"min_activities": 1, "max_activities": 2, "buffer_time": 2.0},
            "balanced": {"min_activities": 2, "max_activities": 3, "buffer_time": 1.0},
            "packed": {"min_activities": 3, "max_activities": 4, "buffer_time": 0.5}
        }
        config = pace_config.get(trip_pace, pace_config["balanced"])
        
        # Map interests to activity types for prioritization
        interest_to_activity_type = {
            "Food & Cuisine": "dining",
            "Museums & Art": "cultural", 
            "Nature & Hiking": "outdoor",
            "Architecture": "historical",
            "Shopping": "shopping",
            "Local Markets": "shopping",
            "History": "historical",
            "Photography": "sightseeing",
            "Beaches": "outdoor",
            "Nightlife": "nightlife"
        }
        
        # Create priority list based on group interests
        priority_activity_types = []
        for interest in interests:
            activity_type = interest_to_activity_type.get(interest, "sightseeing")
            if activity_type not in priority_activity_types:
                priority_activity_types.append(activity_type)
        
        # Add remaining types for variety
        all_types = ["cultural", "dining", "outdoor", "shopping", "historical", "nightlife", "sightseeing"]
        for activity_type in all_types:
            if activity_type not in priority_activity_types:
                priority_activity_types.append(activity_type)
        
        # Distribute activities across days
        for day in range(1, trip_duration + 1):
            daily_activities = []
            day_budget_remaining = budget_per_day
            
            # Adjust preferred types based on day and pace
            if day == 1:
                # Day 1: Start easier, prioritize group interests
                preferred_types = priority_activity_types[:3] + ["dining"]
            elif day == trip_duration:
                # Last day: Shopping and lighter activities 
                preferred_types = ["shopping", "dining"] + priority_activity_types[:2]
            else:
                # Middle days: Focus on priority interests
                preferred_types = priority_activity_types
            
            # Remove duplicates while preserving order
            seen = set()
            preferred_types = [x for x in preferred_types if not (x in seen or seen.add(x))]
            
            activities_added = 0
            max_activities_per_day = config["max_activities"]
            min_activities_per_day = config["min_activities"]
            
            for activity_type in preferred_types:
                if activities_added >= max_activities_per_day:
                    break
                    
                available_activities = activity_categories.get(activity_type, [])
                
                for activity in available_activities:
                    if activities_added >= max_activities_per_day:
                        break
                    
                    # Check if activity fits budget
                    activity_cost = self._estimate_activity_cost(activity)
                    
                    if activity_cost <= day_budget_remaining:
                        # Add time slots for the day
                        time_slot = self._assign_time_slot(activities_added, activity, config["buffer_time"])
                        activity_with_time = {
                            **activity,
                            "scheduled_time": time_slot,
                            "estimated_cost": activity_cost,
                            "day": day
                        }
                        
                        daily_activities.append(activity_with_time)
                        day_budget_remaining -= activity_cost
                        activities_added += 1
                        
                        # Remove from available to avoid duplicates
                        activity_categories[activity_type].remove(activity)
            
            # Ensure minimum activities per day based on pace
            if activities_added < min_activities_per_day:
                all_remaining = []
                for cat_activities in activity_categories.values():
                    all_remaining.extend(cat_activities)
                
                needed_activities = min_activities_per_day - activities_added
                for activity in all_remaining[:needed_activities]:
                    time_slot = self._assign_time_slot(len(daily_activities), activity, config["buffer_time"])
                    activity_cost = self._estimate_activity_cost(activity)
                    
                    activity_with_time = {
                        **activity,
                        "scheduled_time": time_slot,
                        "estimated_cost": activity_cost,
                        "day": day
                    }
                    daily_activities.append(activity_with_time)
                    
                    # Remove from categories
                    for cat_list in activity_categories.values():
                        if activity in cat_list:
                            cat_list.remove(activity)
                            break
            
            daily_itinerary[day] = daily_activities
        
        return daily_itinerary
    
    def _estimate_activity_cost(self, activity: Dict) -> float:
        """Estimate activity cost based on price level."""
        if activity.get("is_free", False):
            return 0.0
        
        price_level = activity.get("price_info", {}).get("price_level", "$")
        
        # Cost mapping based on price level
        cost_mapping = {
            "Free": 0,
            "$": 15,      # Budget activities
            "$$": 35,     # Moderate activities  
            "$$$": 75,    # Expensive activities
            "$$$$": 150   # Very expensive activities
        }
        
        return cost_mapping.get(price_level, 25)  # Default to moderate cost
    
    def _assign_time_slot(self, activity_index: int, activity: Dict, buffer_time: float = 1.0) -> str:
        """Assign appropriate time slot based on activity type, index, and pace."""
        activity_type = activity.get("activity_type", "sightseeing")
        
        # Base time slots adjusted for pace (buffer_time affects spacing)
        if activity_type == "dining":
            if activity_index == 0:
                return "12:00 PM"  # Lunch
            else:
                return "7:00 PM"   # Dinner
        elif activity_type == "nightlife":
            return "9:00 PM"
        elif activity_type == "outdoor":
            return "9:00 AM"   # Best time for outdoor activities
        else:
            # Cultural, shopping, sightseeing - adjust timing based on pace
            if buffer_time >= 2.0:  # Relaxed pace
                time_slots = ["10:00 AM", "3:00 PM"]
            elif buffer_time <= 0.5:  # Packed pace  
                time_slots = ["9:00 AM", "12:00 PM", "3:00 PM", "6:00 PM"]
            else:  # Balanced pace
                time_slots = ["10:00 AM", "2:00 PM", "4:00 PM"]
            
            return time_slots[min(activity_index, len(time_slots)-1)]
    
    def _format_itinerary_response(self, daily_itinerary: Dict[int, List[Dict]], destination: str, trip_duration: int) -> str:
        """Format the itinerary into a readable string response."""
        response = f"\n**ACTIVITY ITINERARY FOR {destination.upper()}**\n"
        response += f"Duration: {trip_duration} days | Source: Google Places API\n\n"
        
        total_estimated_cost = 0
        
        for day, activities in daily_itinerary.items():
            response += f"**Day {day}:**\n"
            
            day_cost = 0
            for activity in activities:
                cost = activity.get("estimated_cost", 0)
                day_cost += cost
                total_estimated_cost += cost
                
                response += f"• {activity['scheduled_time']} - **{activity['name']}**\n"
                response += f"  📍 {activity['location']['address']}\n"
                response += f"  💰 ${cost:.0f} per person"
                
                if activity.get("rating"):
                    response += f" | ⭐ {activity['rating']}"
                
                if activity.get("duration"):
                    response += f" | ⏱️ {activity['duration']}h"
                
                response += f"\n  📝 {activity.get('description', 'Activity description')}\n"
                
                if activity.get("website"):
                    response += f"  🌐 {activity['website']}\n"
                
                response += "\n"
            
            response += f"**Day {day} Total: ${day_cost:.0f} per person**\n\n"
        
        response += f"**TOTAL ACTIVITY COST: ${total_estimated_cost:.0f} per person**\n\n"
        
        # Add provider information
        provider_counts = {}
        for day_activities in daily_itinerary.values():
            for activity in day_activities:
                provider = activity.get("provider", "Unknown")
                provider_counts[provider] = provider_counts.get(provider, 0) + 1
        
        response += "**ACTIVITY SOURCES:**\n"
        for provider, count in provider_counts.items():
            response += f"• {provider}: {count} activities\n"
        
        response += "\n**FUTURE INTEGRATIONS:** GetYourGuide, Viator APIs coming soon for bookable tours and experiences\n\n"
        
        return response