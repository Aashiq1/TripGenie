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
    """
    vibe: List[Literal["relaxing", "adventurous", "party", "culture"]]
    interests: List[str]
    departure_airports: List[str]
    budget: Budget
    trip_duration: int

class UserInput(BaseModel):
    """
    Represents a single user's trip input.

    Attributes:
        name (str): The user's full name.
        email (str): The user's email address.
        phone (str): The user's phone number.
        preferences (Preferences): The user's trip preferences.
        availability (Availability): The user's available travel dates.
        group_code (Optional[str]): The group code this user belongs to.
    """
    name: str
    email: str
    phone: str
    preferences: Preferences
    availability: Availability
    group_code: Optional[str] = None

class GroupInput(BaseModel):
    """
    Represents the group-level input consisting of multiple users.

    Attributes:
        users (List[UserInput]): A list of all users participating in the group trip.
    """
    users: List[UserInput]
