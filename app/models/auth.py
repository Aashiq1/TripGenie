from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    fullName: str

class UserCreate(UserBase):
    password: constr(min_length=8)  # Password must be at least 8 characters

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: str
    createdAt: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: User

class TokenRefresh(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class UserTrip(BaseModel):
    groupCode: str
    tripStatus: str  # 'planning' or 'planned'
    memberCount: int
    role: str  # 'admin' or 'member'
    joinedAt: datetime
    destination: Optional[str] = None
    departureDate: Optional[str] = None

    class Config:
        from_attributes = True 