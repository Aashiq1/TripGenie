from pydantic import BaseModel
from typing import List, Literal, Optional

class Availability(BaseModel):
    """
    Represents the set of dates a user is available for travel.

    Attributes:
        dates (List[str]): A list of available dates in 'YYYY-MM-DD' format.
    """
    dates: List[str]  # Format: YYYY-MM-DD

class Budget(BaseModel):
    """
    Represents the budget range a user is comfortable spending.

    Attributes:
        min (int): Minimum budget in USD.
        max (int): Maximum budget in USD.
    """
    min: int
    max: int

class Preferences(BaseModel):
    """
    Represents a user's travel preferences.

    Attributes:
        vibe (List[str]): Desired travel vibes such as relaxing, adventurous, party, or culture.
        interests (List[str]): Specific activities the user is interested in (e.g., hiking, food, museums).
        departure_airports (List[str]): List of airport codes the user can depart from.
        budget (Budget): The user's budget range.
        trip_duration (int): Desired trip duration in number of days.
        travel_style (str): Travel style preference - budget, balanced, or luxury.
        pace (str): Travel pace preference - chill, balanced, or fast.
        additional_info (Optional[str]): Optional free-text description for NLP processing.
    """
    vibe: List[Literal["relaxing", "adventurous", "party", "culture"]]
    interests: List[str]
    departure_airports: List[str]
    budget: Budget
    trip_duration: int
    travel_style: Literal["budget", "balanced", "luxury"]
    pace: Literal["chill", "balanced", "fast"]
    accommodation_preference: Literal["budget", "standard", "luxury"] = "standard"
    room_sharing: Literal["private", "share", "any"] = "any" 
    dietary_restrictions: Optional[List[str]] = None
    additional_info: Optional[str] = None

class UserInput(BaseModel):
    """
    Represents a single user's trip input.

    Attributes:
        name (str): The user's full name.
        email (str): The user's email address.
        phone (str): The user's phone number.
        role (str): User role - "creator" or "member".
        preferences (Preferences): The user's trip preferences.
        availability (Availability): The user's available travel dates.
        group_code (Optional[str]): The group code this user belongs to.
    """
    name: str
    email: str
    phone: str
    role: Optional[Literal["creator", "member"]] = "member"
    preferences: Preferences
    availability: Availability
    group_code: Optional[str] = None

class TripGroup(BaseModel):
    """
    Represents a trip group with destinations set by the creator.
    
    Attributes:
        group_code (str): Unique identifier for the group.
        destinations (List[str]): 1-3 destinations chosen by the trip creator.
        creator_email (str): Email of the user who created the group.
        created_at (str): Timestamp when the group was created.
        trip_name (Optional[str]): Name of the trip.
        departure_date (Optional[str]): Departure date in YYYY-MM-DD format.
        return_date (Optional[str]): Return date in YYYY-MM-DD format.
        budget (Optional[int]): Budget per person in USD.
        group_size (Optional[int]): Expected group size.
        accommodation (Optional[str]): Accommodation preference.
        description (Optional[str]): Trip description.
    """
    group_code: str
    destinations: List[str]  # 1-3 destinations set by creator
    creator_email: str
    created_at: str
    trip_name: Optional[str] = None
    departure_date: Optional[str] = None
    return_date: Optional[str] = None
    budget: Optional[int] = None
    group_size: Optional[int] = None
    accommodation: Optional[str] = None
    description: Optional[str] = None

class GroupInput(BaseModel):
    """
    Represents the group-level input consisting of multiple users.

    Attributes:
        users (List[UserInput]): A list of all users participating in the group trip.
        group_info (Optional[TripGroup]): Information about the group and destinations.
    """
    users: List[UserInput]
    group_info: Optional[TripGroup] = None
