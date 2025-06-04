import datetime
from typing import List, Dict
from app.models.group_inputs import UserInput
from collections import Counter

def to_date(date_str: str) -> datetime.date:
    """
    Converts a string in 'YYYY-MM-DD' format to a datetime.date object.

    Args:
        date_str (str): A date string.

    Returns:
        datetime.date: The corresponding date object.
    """
    return datetime.strptime(date_str, "%Y-%m-%d")


def prepare_ai_input(users: List[UserInput]) -> dict:
    """
    Prepares user availability data for trip planning.

    Organizes all user-submitted dates into a mapping of date → users available on that date.
    Also computes common dates where all users are available.

    Args:
        users (List[UserInput]): The list of user inputs.

    Returns:
        dict: Contains:
            - "common_dates": List of dates all users are available (as strings).
            - "date_to_users_count": Mapping of date to number of available users.
            - "date_to_users": Mapping of date to set of user emails (used internally).
    """
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
        "date_to_users": date_to_users  # Used by get_best_ranges
    }


def get_best_ranges(date_to_users: Dict[datetime.date, set], users: List[UserInput]) -> List[dict]:
    """
    Determines the best continuous date ranges that maximize group overlap.

    Searches for consecutive date windows (within min-max trip duration) where the highest number of users are available.

    Args:
        date_to_users (Dict[datetime.date, set]): Mapping of date to user emails.
        users (List[UserInput]): The list of all users.

    Returns:
        List[dict]: A list of the best trip date ranges, each with:
            - "start_date"
            - "end_date"
            - "users": list of emails available during that window
    """
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

            # Skip non-consecutive date ranges
            if any((window[i+1] - window[i]).days != 1 for i in range(len(window) - 1)):
                continue

            # Find users who are available for all dates in this window
            users_available = set.intersection(*[date_to_users[date] for date in window])

            if len(users_available) > max_users:
                max_users = len(users_available)
                best_ranges = [{
                    "start_date": window[0],
                    "end_date": window[-1],
                    "users": list(users_available)
                }]
            elif len(users_available) == max_users:
                best_ranges.append({
                    "start_date": window[0],
                    "end_date": window[-1],
                    "users": list(users_available)
                })

    return best_ranges


def get_group_preferences(users: List[UserInput]) -> dict:
    """
    Aggregates the group's overall travel preferences.

    Computes weighted vibes, interests, and calculates a group budget window
    based on the highest min and lowest max individual budgets.

    Args:
        users (List[UserInput]): The list of all user inputs.

    Returns:
        dict: Group profile with:
            - "vibes": weighted counts of preferred vibes
            - "interests": weighted counts of preferred interests
            - "budget_target": midpoint of the overlapping budget range
            - "budget_min": highest of all individual mins
            - "budget_max": lowest of all individual maxes
    """
    group_vibes = []
    group_interests = []
    min_budgets = []
    max_budgets = []

    for user in users:
        group_vibes.extend(user.preferences.vibe)
        group_interests.extend(user.preferences.interests)
        min_budgets.append(user.preferences.budget.min)
        max_budgets.append(user.preferences.budget.max)

    vibe_counts = Counter(group_vibes)
    interest_counts = Counter(group_interests)

    vibe_weights = {vibe: count for vibe, count in vibe_counts.items()}
    interest_weights = {interest: count for interest, count in interest_counts.items()}

    group_min = max(min_budgets)  # Can't go lower than anyone's minimum
    group_max = min(max_budgets)  # Can't go higher than anyone's maximum
    group_target = (group_min + group_max) // 2

    return {
        "vibes": vibe_weights,
        "interests": interest_weights,
        "budget_target": group_target,
        "budget_min": group_min,
        "budget_max": group_max
    }


