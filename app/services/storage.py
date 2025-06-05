"""
Simple file-based storage for user data and trip plans.
In production, this would be replaced with a proper database.
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from app.models.group_inputs import UserInput

# Storage directory
STORAGE_DIR = "data"
GROUPS_FILE = os.path.join(STORAGE_DIR, "groups.json")

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
    
    # Convert back to UserInput objects
    return [UserInput(**user_data) for user_data in group_users]

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

def clear_all_data():
    """Clear all data"""
    ensure_storage_dir()
    if os.path.exists(GROUPS_FILE):
        os.remove(GROUPS_FILE)
