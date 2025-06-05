from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import List
from jose import JWTError, jwt
from app.models.auth import User, UserCreate, UserLogin, Token, UserTrip
from app.services import auth as auth_service

router = APIRouter(tags=["auth"])

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current authenticated user from the token"""
    try:
        payload = jwt.decode(token, auth_service.SECRET_KEY, algorithms=[auth_service.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user_data = auth_service.get_user_by_id(user_id)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return User(
        id=user_id,
        email=user_data["email"],
        fullName=user_data.get("name", "Unknown"),
        createdAt=datetime.fromisoformat(user_data["created_at"])
    )

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        password_hash = auth_service.get_password_hash(user_data.password)
        user = auth_service.create_user(
            email=user_data.email,
            password_hash=password_hash,
            name=user_data.fullName
        )
        token = auth_service.create_access_token({"sub": user["id"]})
        return {"token": token, "user": User(
            id=user["id"],
            email=user["email"],
            fullName=user["name"],
            createdAt=datetime.fromisoformat(user["created_at"])
        )}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with email and password"""
    user_data = auth_service.get_user_by_email(form_data.username)
    if not user_data or not auth_service.verify_password(form_data.password, user_data["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    token = auth_service.create_access_token({"sub": user_data["id"]})
    return {"token": token, "user": User(
        id=user_data["id"],
        email=user_data["email"],
        fullName=user_data["name"],
        createdAt=datetime.fromisoformat(user_data["created_at"])
    )}

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout the current user (client should clear token)"""
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the current user's profile"""
    return current_user

@router.get("/trips", response_model=List[UserTrip])
async def get_trips(current_user: User = Depends(get_current_user)):
    """Get all trips for the current user"""
    trips = auth_service.get_user_trips(current_user.id)
    return trips 