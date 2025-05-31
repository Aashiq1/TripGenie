import datetime
from typing import List, Dict
from app.models.group_inputs import UserInput
from collections import Counter

def to_date(date_str: str):
    return datetime.strptime(date_str, "%Y-%m-%d")

def prepare_ai_input(users: List[UserInput]) -> dict:
    if not users:
        return {}

    date_to_users = {}

    for user in users:
        for date_str in user.availability.dates:
            date = to_date(date_str)
            if date not in date_to_users:
                date_to_users[date] = set()
            date_to_users[date].add(user.email)

    all_users = {user.email for user in users}
    common_dates = [str(date) for date, u_set in date_to_users.items() if u_set == all_users]

    return {
        "common_dates": sorted(common_dates),
        "date_to_users_count": {str(date): len(users) for date, users in date_to_users.items()},
        "date_to_users": date_to_users  # Needed for get_best_ranges
    }


def get_best_ranges(date_to_users: Dict[datetime.date, set], users: List[UserInput]) -> List[dict]:
    all_dates = sorted(date_to_users.keys())
    min_trip = min(user.preferences.trip_duration for user in users)
    max_trip = max(user.preferences.trip_duration for user in users)

    best_ranges = []
    max_users = 0

    for window_size in range(min_trip, max_trip + 1):
        for start_idx in range(len(all_dates)):
            if start_idx + window_size > len(all_dates):
                continue
                
            window = all_dates[start_idx:start_idx + window_size]

            if any((window[i+1] - window[i]).days != 1 for i in range(len(window) - 1)):
                continue

            users_available = set.intersection(*[date_to_users[date] for date in window])

            if len(users_available) > max_users:
                max_users = len(users_available)
                best_ranges = [{"start_date": window[0], "end_date": window[-1], "users": list(users_available)}]
            elif len(users_available) == max_users:
                best_ranges.append({"start_date": window[0], "end_date": window[-1], "users": list(users_available)})

    return best_ranges

    

