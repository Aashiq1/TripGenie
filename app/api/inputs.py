from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from app.models.group_inputs import UserInput, GroupInput, TripGroup
from app.services import storage, auth
from app.services.planner import plan_trip
from app.models.auth import User
from app.api.auth import get_current_user

# Initialize the API router without prefix since it's added in main.py
router = APIRouter(tags=["inputs"])

@router.post("/group")
async def create_trip_group(trip_group: TripGroup, current_user: User = Depends(get_current_user)):
    """Create a new trip group with destinations."""
    try:
        # Store the trip group
        storage.create_trip_group(trip_group)
        
        # Add creator to their trips
        auth.add_user_to_trip(current_user.id, trip_group.group_code, role="creator")
        
        return {
            "message": "Trip group created successfully",
            "group": trip_group
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create trip group: {str(e)}")

@router.post("/user")
async def submit_user_input(
    user_input: UserInput, 
    group_code: Optional[str] = Query(None, description="Group code to add user to"),
    current_user: User = Depends(get_current_user)
):
    """Submit user preferences and availability for trip planning."""
    try:
        # Get group code from query parameter or user input (with fallback for backward compatibility)
        effective_group_code = group_code or getattr(user_input, 'group_code', 'DEFAULT_GROUP')
        if not effective_group_code:
            effective_group_code = 'DEFAULT_GROUP'
            
        # Add user to the specific group
        storage.add_user_to_group(user_input, effective_group_code)
        
        # Add user to their trips (role determined by user input, default to member)
        role = getattr(user_input, 'role', 'member') or 'member'
        auth.add_user_to_trip(current_user.id, effective_group_code, role=role)
        
        return {
            "message": "User input received successfully",
            "user": user_input,
            "group_code": effective_group_code
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process user input: {str(e)}")

@router.get("/group", response_model=GroupInput)
async def get_group(
    group_code: str,
    current_user: User = Depends(get_current_user)
):
    """Get group data for a specific group code"""
    # First check if user is a member of this trip
    user_trips = auth.get_user_trips(current_user.id)
    is_member = any(trip.groupCode == group_code for trip in user_trips)
    
    if not is_member:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this trip"
        )
    
    group_data = storage.get_group_data(group_code)
    if not group_data:
        raise HTTPException(
            status_code=404,
            detail="Group not found"
        )
    return GroupInput(users=group_data)

@router.post("/plan")
async def plan_trip_endpoint(group_code: Optional[str] = Query(None, description="Group code to plan trip for")):
    """Generate trip plan based on group inputs."""
    try:
        # Use default group if no group code provided (backward compatibility)
        if not group_code:
            group_code = 'DEFAULT_GROUP'
            
        users = storage.get_group_data(group_code)
        
        if not users:
            raise HTTPException(status_code=400, detail=f"No users found in group {group_code}")
        
        # Pass the users list directly to plan_trip
        return await plan_trip(users)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate trip plan: {str(e)}")

@router.delete("/clear")
async def clear_group_data(group_code: Optional[str] = Query(None, description="Group code to clear data for")):
    """Clear all data for a specific group."""
    try:
        if group_code:
            storage.clear_group_data(group_code)
            return {"message": f"Group {group_code} data cleared successfully"}
        else:
            storage.clear_all_data()
            return {"message": "All data cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")

@router.get("/groups")
async def list_groups():
    """List all available groups."""
    try:
        groups = storage.load_groups()
        return {
            "groups": [
                {
                    "group_code": code,
                    "user_count": len(users),
                    "users": [user.get('name', 'Unknown') for user in users]
                }
                for code, users in groups.items()
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list groups: {str(e)}")

