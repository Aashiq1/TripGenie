import datetime
from typing import List, Dict, Set, Tuple
from app.models.group_inputs import UserInput
from collections import Counter, defaultdict

def to_date(date_str: str) -> datetime.date:
    """Converts a string in 'YYYY-MM-DD' format to a datetime.date object."""
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

def prepare_ai_input(users: List[UserInput]) -> dict:
    """
    Enhanced version that includes more context about the group.
    """
    if not users:
        return {}

    date_to_users = {}
    airport_to_users = defaultdict(list)
    
    # Collect both date and airport information
    for user in users:
        # Date availability
        for date_str in user.availability.dates:
            date = to_date(date_str)
            if date not in date_to_users:
                date_to_users[date] = set()
            date_to_users[date].add(user.email)
        
        # Airport grouping
        if user.preferences.departure_airports:
            primary_airport = user.preferences.departure_airports[0]
            airport_to_users[primary_airport].append(user.email)

    all_users = {user.email for user in users}
    common_dates = [str(date) for date, u_set in date_to_users.items() if u_set == all_users]
    
    # NEW: Add partial availability info
    partial_dates = []
    for date, available_users in date_to_users.items():
        if len(available_users) >= len(all_users) * 0.8:  # 80% threshold
            partial_dates.append({
                "date": str(date),
                "available_count": len(available_users),
                "missing_users": list(all_users - available_users)
            })

    return {
        "common_dates": sorted(common_dates),
        "date_to_users_count": {str(date): len(users) for date, users in date_to_users.items()},
        "date_to_users": date_to_users,
        "airport_groups": dict(airport_to_users),  # NEW
        "partial_availability": partial_dates[:10],  # NEW: Top 10 dates with good availability
        "total_users": len(users)
    }

def get_best_ranges(date_to_users: Dict[datetime.date, set], users: List[UserInput]) -> List[dict]:
    """
    Enhanced to include more context about each range.
    """
    all_dates = sorted(date_to_users.keys())
    min_trip = min(user.preferences.trip_duration for user in users)
    max_trip = max(user.preferences.trip_duration for user in users)
    
    # Build user lookup for enhanced info
    user_lookup = {user.email: user for user in users}

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

            if len(users_available) >= max_users * 0.9:  # Allow 90% threshold
                # NEW: Group available users by airport
                airport_groups = defaultdict(list)
                for email in users_available:
                    if email in user_lookup:
                        user = user_lookup[email]
                        if user.preferences.departure_airports:
                            airport = user.preferences.departure_airports[0]
                            airport_groups[airport].append(email)
                
                range_info = {
                    "start_date": window[0],
                    "end_date": window[-1],
                    "duration": window_size,
                    "users": list(users_available),
                    "user_count": len(users_available),
                    "missing_users": list(set(user.email for user in users) - users_available),
                    "airport_breakdown": dict(airport_groups),  # NEW
                    "coverage_percent": (len(users_available) / len(users)) * 100  # NEW
                }
                
                if len(users_available) > max_users:
                    max_users = len(users_available)
                    best_ranges = [range_info]
                elif len(users_available) == max_users:
                    best_ranges.append(range_info)

    return best_ranges

def get_group_preferences(users: List[UserInput]) -> dict:
    """
    Enhanced version with individual tracking and conflict detection.
    """
    # [Previous collections remain the same...]
    group_vibes = []
    group_interests = []
    min_budgets = []
    max_budgets = []
    travel_styles = []
    paces = []
    accommodation_preferences = []  # ADD THIS
    additional_info = []
    
    # NEW: Track individual details
    user_profiles = []
    airport_groups = defaultdict(list)
    trip_durations = []
    
    for user in users:
        group_vibes.extend(user.preferences.vibe)
        group_interests.extend(user.preferences.interests)
        min_budgets.append(user.preferences.budget.min)
        max_budgets.append(user.preferences.budget.max)
        travel_styles.append(user.preferences.travel_style)
        paces.append(user.preferences.pace)
        trip_durations.append(user.preferences.trip_duration)
        
        # ADD THIS: Collect accommodation preferences
        if hasattr(user.preferences, 'accommodation_preference'):
            accommodation_preferences.append(user.preferences.accommodation_preference)
        
        # NEW: Group by airport
        if user.preferences.departure_airports:
            primary_airport = user.preferences.departure_airports[0]
            airport_groups[primary_airport].append({
                "name": user.name,
                "email": user.email,
                "budget": f"${user.preferences.budget.min}-${user.preferences.budget.max}"
            })
        
        # UPDATED: Keep individual profiles with accommodation info
        user_profiles.append({
            "name": user.name,
            "email": user.email,
            "departure_airport": user.preferences.departure_airports[0] if user.preferences.departure_airports else "Unknown",
            "budget_min": user.preferences.budget.min,
            "budget_max": user.preferences.budget.max,
            "travel_style": user.preferences.travel_style,
            "trip_duration": user.preferences.trip_duration,
            "accommodation_preference": getattr(user.preferences, 'accommodation_preference', 'standard'),  # ADD THIS
            "room_sharing": getattr(user.preferences, 'room_sharing', 'any')  # ADD THIS
        })
        
        if hasattr(user.preferences, 'additional_info') and user.preferences.additional_info:
            additional_info.append({
                "user": user.name,
                "email": user.email,
                "info": user.preferences.additional_info
            })

    # Calculations
    vibe_counts = Counter(group_vibes)
    interest_counts = Counter(group_interests)
    style_counts = Counter(travel_styles)
    pace_counts = Counter(paces)
    accommodation_counts = Counter(accommodation_preferences) if accommodation_preferences else Counter(["standard"])  # ADD THIS

    group_min = max(min_budgets)
    group_max = min(max_budgets)
    group_target = (group_min + group_max) // 2

    # NEW: Detect conflicts
    conflicts = []
    if group_min > group_max:
        conflicts.append(f"CRITICAL: Budget ranges don't overlap! Min ${group_min} > Max ${group_max}")
    
    if max(trip_durations) - min(trip_durations) > 3:
        conflicts.append(f"WARNING: Trip duration preferences vary by {max(trip_durations) - min(trip_durations)} days")
    
    if "luxury" in style_counts and "budget" in style_counts:
        conflicts.append("WARNING: Group has conflicting travel styles (luxury vs budget)")
    
    # ADD THIS: Check accommodation conflicts
    if "luxury" in accommodation_counts and "budget" in accommodation_counts:
        conflicts.append("WARNING: Group has conflicting accommodation preferences (luxury vs budget)")

    # Calculate consensus duration
    avg_duration = sum(trip_durations) / len(trip_durations) if trip_durations else 5
    consensus_duration = round(avg_duration)

    return {
        # Original data
        "vibes": dict(vibe_counts),
        "interests": dict(interest_counts),
        "budget_target": group_target,
        "budget_min": group_min,
        "budget_max": group_max,
        "travel_styles": dict(style_counts),
        "accommodation_styles": dict(accommodation_counts),  # ADD THIS
        "paces": dict(pace_counts),
        "additional_info": additional_info,
        
        # NEW: Enhanced data
        "user_profiles": user_profiles,
        "airport_groups": dict(airport_groups),
        "trip_duration_range": {
            "min": min(trip_durations),
            "max": max(trip_durations),
            "average": sum(trip_durations) / len(trip_durations),
            "consensus_duration": consensus_duration  # ADD THIS
        },
        "group_size": len(users),
        "conflicts": conflicts,
        "budget_compatible": group_min <= group_max
    }

def analyze_group_compatibility(group_prefs: dict) -> List[str]:
    warnings = []
        
    # Budget compatibility
    if not group_prefs["budget_compatible"]:
        warnings.append(f"⚠️ BUDGET MISMATCH: No overlap between all members' budgets!")
        
    # Duration mismatch
    duration_info = group_prefs["trip_duration_range"]
    if duration_info["max"] - duration_info["min"] > 3:
        warnings.append(f"⚠️ DURATION CONFLICT: Members want trips ranging from {duration_info['min']} to {duration_info['max']} days")
        
    # Airport diversity
    if len(group_prefs["airport_groups"]) > 3:
        warnings.append(f"⚠️ COORDINATION CHALLENGE: Group flying from {len(group_prefs['airport_groups'])} different airports")
        
    # Travel style conflict
    styles = group_prefs["travel_styles"]
    if "luxury" in styles and "budget" in styles:
        warnings.append("⚠️ STYLE MISMATCH: Some want luxury travel, others want budget")
        
    return warnings