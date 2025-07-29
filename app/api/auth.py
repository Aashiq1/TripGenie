from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import List
from jose import JWTError, jwt
from app.models.auth import User, UserCreate, UserLogin, Token, TokenRefresh, TokenResponse, UserTrip
from app.services import auth as auth_service

router = APIRouter(tags=["auth"])

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current authenticated user from the token"""
    # Verify the access token
    user_id = auth_service.verify_token(token, "access")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
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
        
        # Create token pair
        token_data = auth_service.create_token_pair(user["id"])
        
        return Token(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
            user=User(
                id=user["id"],
                email=user["email"],
                fullName=user["name"],
                createdAt=datetime.fromisoformat(user["created_at"])
            )
        )
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
    
    # Create token pair
    token_data = auth_service.create_token_pair(user_data["id"])
    
    return Token(
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"], 
        token_type=token_data["token_type"],
        expires_in=token_data["expires_in"],
        user=User(
            id=user_data["id"],
            email=user_data["email"],
            fullName=user_data["name"],
            createdAt=datetime.fromisoformat(user_data["created_at"])
        )
    )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout the current user (client should clear token)"""
    return {"message": "Successfully logged out"}

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh):
    """Refresh access token using refresh token"""
    # Verify the refresh token
    user_id = auth_service.verify_token(token_data.refresh_token, "refresh")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Check if user still exists
    user_data = auth_service.get_user_by_id(user_id)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new access token
    new_access_token = auth_service.create_access_token(user_id)
    
    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the current user's profile"""
    return current_user

@router.get("/trips", response_model=List[UserTrip])
async def get_trips(current_user: User = Depends(get_current_user)):
    """Get all trips for the current user"""
    trips = auth_service.get_user_trips(current_user.id)
    return trips 