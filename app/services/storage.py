"""
Simple file-based storage for user data and trip plans.
In production, this would be replaced with a proper database.
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from app.models.group_inputs import UserInput, TripGroup

# Storage directory
STORAGE_DIR = "data"
GROUPS_FILE = os.path.join(STORAGE_DIR, "groups.json")
TRIP_GROUPS_FILE = os.path.join(STORAGE_DIR, "trip_groups.json")
TRIP_PLANS_FILE = os.path.join(STORAGE_DIR, "trip_plans.json")

def ensure_storage_dir():
    """Ensure storage directory exists"""
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)

def load_groups() -> Dict[str, List[Dict]]:
    """Load all groups from storage"""
    ensure_storage_dir()
    if os.path.exists(GROUPS_FILE):
        try:
            with open(GROUPS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_groups(groups: Dict[str, List[Dict]]):
    """Save all groups to storage"""
    ensure_storage_dir()
    with open(GROUPS_FILE, 'w') as f:
        json.dump(groups, f, indent=2, default=str)

def add_user_to_group(user_data: UserInput, group_code: str) -> UserInput:
    """Add a user to a specific group"""
    groups = load_groups()
    
    # Initialize group if it doesn't exist
    if group_code not in groups:
        groups[group_code] = []
    
    # Convert UserInput to dict for storage
    user_dict = user_data.model_dump()
    user_dict['submitted_at'] = datetime.now().isoformat()
    user_dict['group_code'] = group_code
    
    # Check if user already exists in this group (by email)
    existing_user_index = None
    for i, existing_user in enumerate(groups[group_code]):
        if existing_user.get('email') == user_data.email:
            existing_user_index = i
            break
    
    if existing_user_index is not None:
        # Update existing user
        groups[group_code][existing_user_index] = user_dict
    else:
        # Add new user
        groups[group_code].append(user_dict)
    
    save_groups(groups)
    return user_data

def get_group_data(group_code: str) -> List[UserInput]:
    """Get all users in a specific group"""
    groups = load_groups()
    group_users = groups.get(group_code, [])
    
    # Convert back to UserInput objects with backward compatibility
    user_inputs = []
    for user_data in group_users:
        # Handle backward compatibility for missing fields
        if 'preferences' in user_data:
            prefs = user_data['preferences']
            # Add default values for missing fields
            if 'travel_style' not in prefs:
                prefs['travel_style'] = 'balanced'
            if 'pace' not in prefs:
                prefs['pace'] = 'balanced'
            if 'accommodation_preference' not in prefs:
                prefs['accommodation_preference'] = 'standard'
            if 'room_sharing' not in prefs:
                prefs['room_sharing'] = 'any'
        
        # Add default role if missing
        if 'role' not in user_data:
            user_data['role'] = 'member'
            
        user_inputs.append(UserInput(**user_data))
    
    return user_inputs

def get_all_users() -> List[UserInput]:
    """Get all users across all groups (for backward compatibility)"""
    groups = load_groups()
    all_users = []
    
    for group_users in groups.values():
        all_users.extend([UserInput(**user_data) for user_data in group_users])
    
    return all_users

def clear_group_data(group_code: str):
    """Clear data for a specific group"""
    groups = load_groups()
    if group_code in groups:
        del groups[group_code]
        save_groups(groups)

def load_trip_groups() -> Dict[str, dict]:
    """Load all trip groups from storage"""
    ensure_storage_dir()
    if os.path.exists(TRIP_GROUPS_FILE):
        try:
            with open(TRIP_GROUPS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_trip_groups(trip_groups: Dict[str, dict]):
    """Save all trip groups to storage"""
    ensure_storage_dir()
    with open(TRIP_GROUPS_FILE, 'w') as f:
        json.dump(trip_groups, f, indent=2)

def create_trip_group(trip_group: TripGroup) -> TripGroup:
    """Create a new trip group"""
    trip_groups = load_trip_groups()
    
    # Convert TripGroup to dict for storage
    trip_group_dict = trip_group.model_dump()
    
    # Store the trip group
    trip_groups[trip_group.group_code] = trip_group_dict
    
    save_trip_groups(trip_groups)
    return trip_group

def get_trip_group(group_code: str) -> Optional[TripGroup]:
    """Get a specific trip group"""
    trip_groups = load_trip_groups()
    group_data = trip_groups.get(group_code)
    
    if group_data:
        return TripGroup(**group_data)
    return None

def update_trip_group(trip_group: TripGroup) -> TripGroup:
    """Update an existing trip group"""
    trip_groups = load_trip_groups()
    
    # Convert TripGroup to dict for storage
    trip_group_dict = trip_group.model_dump()
    
    # Update the trip group
    trip_groups[trip_group.group_code] = trip_group_dict
    
    save_trip_groups(trip_groups)
    return trip_group

def load_trip_plans() -> Dict[str, dict]:
    """Load all trip plans from storage"""
    ensure_storage_dir()
    if os.path.exists(TRIP_PLANS_FILE):
        try:
            with open(TRIP_PLANS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_trip_plans(trip_plans: Dict[str, dict]):
    """Save all trip plans to storage"""
    ensure_storage_dir()
    with open(TRIP_PLANS_FILE, 'w') as f:
        json.dump(trip_plans, f, indent=2, default=str)

def save_trip_plan(group_code: str, trip_plan: dict):
    """Save a trip plan for a specific group"""
    trip_plans = load_trip_plans()
    trip_plans[group_code] = {
        **trip_plan,
        'saved_at': datetime.now().isoformat(),
        'group_code': group_code
    }
    save_trip_plans(trip_plans)

def get_trip_plan(group_code: str) -> Optional[dict]:
    """Get a trip plan for a specific group"""
    trip_plans = load_trip_plans()
    return trip_plans.get(group_code)

def clear_all_data():
    """Clear all data"""
    ensure_storage_dir()
    if os.path.exists(GROUPS_FILE):
        os.remove(GROUPS_FILE)
    if os.path.exists(TRIP_GROUPS_FILE):
        os.remove(TRIP_GROUPS_FILE)
    if os.path.exists(TRIP_PLANS_FILE):
        os.remove(TRIP_PLANS_FILE)
