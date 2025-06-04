from app.models.group_inputs import UserInput
from app.services.ai_input import prepare_ai_input, get_best_ranges, get_group_preferences
from app.services.destination_scoring import score_destination
from typing import List

# Hardcoded destination database (can be replaced with real API data later)
destinations = [
    {
        "name": "Sedona, AZ",
        "vibes": ["chill", "spiritual"],
        "interests": ["hiking", "nature", "food"],
        "cost_per_day": 350
    },
    {
        "name": "Austin, TX",
        "vibes": ["party", "chill"],
        "interests": ["nightlife", "food", "music"],
        "cost_per_day": 400
    },
    {
        "name": "Miami, FL",
        "vibes": ["beach", "luxury"],
        "interests": ["swimming", "nightlife", "shopping"],
        "cost_per_day": 450
    },
    {
        "name": "Lake Tahoe, CA",
        "vibes": ["adventurous", "chill"],
        "interests": ["hiking", "skiing", "nature"],
        "cost_per_day": 375
    },
    {
        "name": "New Orleans, LA",
        "vibes": ["party", "cultural"],
        "interests": ["music", "food", "history"],
        "cost_per_day": 320
    }
]

def plan_trip(users: List[UserInput]) -> dict:
    """
    Generates a trip plan based on user availability, preferences, and budgets.

    This function:
    - Builds a group profile of shared vibes, interests, and budget.
    - Finds the best possible date ranges with the highest user overlap.
    - Scores each destination against the group's profile and trip length.
    - Returns top 3 matching destinations for each date range.

    Args:
        users (List[UserInput]): List of user input data with preferences and availability.

    Returns:
        dict: A trip plan including:
            - "best_date_ranges": recommended travel windows with matching destinations
            - "date_to_users_count": availability counts per day
            - "common_dates": dates that all users can attend
            - "group_profile": shared group preferences and budget range
    """
    # Aggregate group preferences
    group_profile = get_group_preferences(users)

    # Prepare availability data and build mapping of date → users
    trip_data = prepare_ai_input(users)

    # Find best date windows based on overlap and trip length constraints
    best_ranges = get_best_ranges(trip_data["date_to_users"], users)

    for trip_range in best_ranges:
        # Convert date objects to strings for JSON serialization
        trip_range["start_date"] = trip_range["start_date"].strftime("%Y-%m-%d")
        trip_range["end_date"] = trip_range["end_date"].strftime("%Y-%m-%d")
        trip_range["user_count"] = len(trip_range["users"])
        
        # Calculate length of this proposed trip window
        from datetime import datetime
        start_date = datetime.strptime(trip_range["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(trip_range["end_date"], "%Y-%m-%d").date()
        trip_length = (end_date - start_date).days + 1

        # Score all destinations for this trip length and group preferences
        ranked = sorted(
            [
                {
                    "name": d["name"],
                    "score": score_destination(d, group_profile, trip_length)
                }
                for d in destinations
            ],
            key=lambda x: -x["score"]  # sort by descending score
        )

        # Attach top 3 destination recommendations to the trip window
        trip_range["destinations"] = ranked[:3]

    return {
        "best_date_ranges": best_ranges,
        "date_to_users_count": trip_data["date_to_users_count"],
        "common_dates": trip_data["common_dates"],
        "group_profile": group_profile
    }
