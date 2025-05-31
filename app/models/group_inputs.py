from pydantic import BaseModel
from typing import List, Literal

class Availability(BaseModel):
    dates: List[str]  # Format: YYYY-MM-DD

class Preferences(BaseModel):
    vibe: List[Literal["relaxing", "adventurous", "party", "culture"]]
    interests: List[str]
    departure_airports: List[str]
    budget: float
    trip_duration: int

class UserInput(BaseModel):
    name: str
    email: str
    phone: str
    preferences: Preferences
    availability: Availability

class GroupInput(BaseModel):
    users: List[UserInput]
