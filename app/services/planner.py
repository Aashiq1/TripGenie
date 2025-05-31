from app.models.group_inputs import UserInput
from app.services.ai_input import prepare_ai_input, get_best_ranges
from typing import List

def plan_trip(users: List[UserInput]) -> dict:
    trip_data = prepare_ai_input(users)
    best_ranges = get_best_ranges(trip_data["date_to_users"], users)

    return {
        "best_date_ranges": best_ranges,
        "date_to_users_count": trip_data["date_to_users_count"],
        "common_dates": trip_data["common_dates"]
    }
