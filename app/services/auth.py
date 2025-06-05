import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.models.auth import User, UserCreate, UserLogin, UserTrip

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Storage
STORAGE_DIR = "data"
USERS_FILE = os.path.join(STORAGE_DIR, "users.json")
TRIPS_FILE = os.path.join(STORAGE_DIR, "user_trips.json")

def ensure_storage_dir():
    """Ensure storage directory exists"""
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)

def load_users() -> Dict[str, Dict]:
    """Load all users from storage"""
    ensure_storage_dir()
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_users(users: Dict[str, Dict]):
    """Save all users to storage"""
    ensure_storage_dir()
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def load_user_trips() -> Dict[str, List[Dict]]:
    """Load all user trips from storage"""
    ensure_storage_dir()
    if os.path.exists(TRIPS_FILE):
        try:
            with open(TRIPS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_user_trips(trips: Dict[str, List[Dict]]):
    """Save all user trips to storage"""
    ensure_storage_dir()
    with open(TRIPS_FILE, 'w') as f:
        json.dump(trips, f, indent=2)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get a user by their ID"""
    users = load_users()
    return users.get(user_id)

def get_user_by_email(email: str) -> Optional[Dict]:
    """Get a user by their email"""
    users = load_users()
    for user_id, user in users.items():
        if user.get('email') == email:
            return {**user, 'id': user_id}
    return None

def create_user(email: str, password_hash: str, name: str) -> Dict:
    """Create a new user"""
    users = load_users()
    
    # Check if user already exists
    for user in users.values():
        if user.get('email') == email:
            raise ValueError("User with this email already exists")
    
    # Generate user ID (in production, use a proper ID generator)
    user_id = f"user_{len(users) + 1}"
    
    # Create user
    user = {
        'email': email,
        'password_hash': password_hash,
        'name': name,
        'created_at': datetime.now().isoformat()
    }
    
    users[user_id] = user
    save_users(users)
    
    return {**user, 'id': user_id}

def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate a user"""
    users = load_users()
    for user_id, user_data in users.items():
        if user_data["email"] == email and verify_password(password, user_data["password"]):
            return User(
                id=user_id,
                email=user_data["email"],
                fullName=user_data["fullName"],
                createdAt=datetime.fromisoformat(user_data["createdAt"])
            )
    return None

def get_user_trips(user_id: str) -> List[UserTrip]:
    """Get all trips for a user"""
    trips = load_user_trips()
    
    # Try both UUID and string formats
    user_trips = trips.get(user_id, [])
    if not user_trips:
        # If no trips found with UUID, try with string format
        # This handles backward compatibility
        user_trips = trips.get(f"user_{user_id}", [])
    
    return [
        UserTrip(
            groupCode=trip["groupCode"],
            tripStatus=trip["tripStatus"],
            memberCount=trip["memberCount"],
            role=trip["role"],
            joinedAt=datetime.fromisoformat(trip["joinedAt"])
        )
        for trip in user_trips
    ]

def add_user_to_trip(user_id: str, group_code: str, role: str = "member"):
    """Add a user to a trip"""
    trips = load_user_trips()
    
    # Always use UUID format for new entries
    if user_id not in trips:
        trips[user_id] = []
    
    # Check if user is already in this trip
    for trip in trips[user_id]:
        if trip["groupCode"] == group_code:
            return  # User already in trip
    
    # Get the actual member count from group data
    try:
        from app.services import storage
        group_data = storage.get_group_data(group_code)
        member_count = len(group_data) if group_data else 1
    except:
        # Fallback to 1 if we can't get group data
        member_count = 1
    
    # Add trip
    trips[user_id].append({
        "groupCode": group_code,
        "tripStatus": "planning",
        "memberCount": member_count,
        "role": role,
        "joinedAt": datetime.now().isoformat()
    })
    
    # Update member count for all existing users in this trip
    for uid, user_trips in trips.items():
        for trip in user_trips:
            if trip["groupCode"] == group_code:
                trip["memberCount"] = member_count
    
    save_user_trips(trips)

def update_all_trip_member_counts():
    """Update member counts for all existing trips"""
    try:
        from app.services import storage
        trips = load_user_trips()
        
        # Get all unique group codes
        group_codes = set()
        for user_trips in trips.values():
            for trip in user_trips:
                group_codes.add(trip["groupCode"])
        
        # Update member count for each group
        for group_code in group_codes:
            try:
                group_data = storage.get_group_data(group_code)
                member_count = len(group_data) if group_data else 1
                
                # Update all users' trips for this group
                for user_trips in trips.values():
                    for trip in user_trips:
                        if trip["groupCode"] == group_code:
                            trip["memberCount"] = member_count
            except Exception as e:
                print(f"Failed to update member count for group {group_code}: {e}")
                
        save_user_trips(trips)
        print("Successfully updated all trip member counts")
    except Exception as e:
        print(f"Failed to update trip member counts: {e}") 