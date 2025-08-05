import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.models.auth import User, UserCreate, UserLogin, UserTrip

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")  # Change in production
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "your-refresh-secret-key-here")  # Separate key for refresh tokens
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour access tokens
REFRESH_TOKEN_EXPIRE_DAYS = 30   # Long-lived refresh tokens

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

def create_access_token(user_id: str) -> str:
    """Create a JWT access token with expiration"""
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token with expiration"""
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh"
    }
    return jwt.encode(payload, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

def create_token_pair(user_id: str) -> dict:
    """Create both access and refresh tokens"""
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
    }

def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """Verify a token and return user_id if valid"""
    try:
        secret_key = SECRET_KEY if token_type == "access" else REFRESH_SECRET_KEY
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        
        user_id: str = payload.get("sub")
        token_type_claim: str = payload.get("type")
        
        if user_id is None or token_type_claim != token_type:
            return None
            
        return user_id
    except JWTError:
        return None

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
            joinedAt=datetime.fromisoformat(trip["joinedAt"]),
            destination=trip.get("destination"),
            departureDate=trip.get("departureDate")
        )
        for trip in user_trips
    ]

def add_user_to_trip(user_id: str, group_code: str, role: str = "member", destination: str = None, departure_date: str = None):
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
    
    # Try to get destination info from trip group data if not provided
    if not destination:
        try:
            from app.services import storage
            trip_group = storage.get_trip_group(group_code)
            if trip_group and trip_group.destination:
                destination = trip_group.destination
                # departure_date is not stored in TripGroup model, leave as None for now
                departure_date = None
        except:
            pass

    # Add trip
    trips[user_id].append({
        "groupCode": group_code,
        "tripStatus": "planning",
        "memberCount": member_count,
        "role": role,
        "joinedAt": datetime.now().isoformat(),
        "destination": destination,
        "departureDate": departure_date
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

def update_existing_user_trips_with_destinations():
    """Update existing user trips to populate missing destination information"""
    try:
        from app.services import storage
        trips = load_user_trips()
        updated = False
        
        for user_id, user_trips in trips.items():
            for trip in user_trips:
                # Check if destination is missing
                if not trip.get("destination"):
                    try:
                        trip_group = storage.get_trip_group(trip["groupCode"])
                        if trip_group and trip_group.destination:
                            trip["destination"] = trip_group.destination
                            updated = True
                    except Exception as e:
                        print(f"Failed to update destination for trip {trip['groupCode']}: {e}")
        
        if updated:
            save_user_trips(trips)
            print("Successfully updated existing user trips with destination information")
        else:
            print("No user trips needed destination updates")
    except Exception as e:
        print(f"Failed to update existing user trips: {e}") 