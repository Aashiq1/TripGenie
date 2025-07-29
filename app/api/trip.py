from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from app.models.group_inputs import GroupInput
from app.services import storage, auth
from app.services.planner import plan_trip
from app.models.auth import User
from app.api.auth import get_current_user

router = APIRouter(tags=["trip"])

@router.get("/{group_code}/preview")
async def preview_trip_details(
    group_code: str,
    current_user: User = Depends(get_current_user)
):
    """Preview trip details for joining (no membership check)"""
    print(f"DEBUG: Preview request for group_code: {group_code}")
    
    # Check if trip group exists first
    trip_group = storage.get_trip_group(group_code)
    print(f"DEBUG: trip_group found: {trip_group is not None}")
    if trip_group:
        print(f"DEBUG: trip_group data: {trip_group.model_dump()}")
    
    if not trip_group:
        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )
    
    # Get group data (user inputs)
    group_data = storage.get_group_data(group_code)
    
    # If no user data exists yet, create minimal preview from trip group
    if not group_data:
        # Trip exists but no users have submitted preferences yet
        # Return real trip data from trip_group stored form data
        return {
            "groupCode": group_code,
            "groupData": [{
                "name": trip_group.trip_name or "Trip Creator",
                "email": trip_group.creator_email,
                "role": "creator",
                "destinations": trip_group.destinations,  # Real destinations
                "departure_date": trip_group.departure_date,  # Real departure date
                "return_date": trip_group.return_date,  # Real return date
                "budget": trip_group.budget,  # Real budget
                "accommodation_preference": trip_group.accommodation or "standard",
                "description": trip_group.description
            }],
            "tripPlan": None,
            "memberCount": 1,
            "status": "planning",
            "destinations": trip_group.destinations  # Add destinations at root level too
        }
    
    # Get trip plan if it exists
    trip_plan = None
    try:
        trip_plan = storage.get_trip_plan(group_code)
    except:
        pass  # Trip plan might not exist yet
    
    # Enhance user data with trip_group info for the creator
    enhanced_group_data = []
    for user in group_data:
        user_dict = user.model_dump()
        # For the creator, merge in trip_group data
        if user.role == "creator":
            user_dict.update({
                "trip_name": trip_group.trip_name,
                "departure_date": trip_group.departure_date,
                "return_date": trip_group.return_date,
                "budget": trip_group.budget,
                "accommodation_preference": trip_group.accommodation or user_dict.get("accommodation_preference", "standard"),
                "description": trip_group.description,
                "destinations": trip_group.destinations
            })
        enhanced_group_data.append(user_dict)
    
    return {
        "groupCode": group_code,
        "groupData": enhanced_group_data,
        "tripPlan": trip_plan,
        "memberCount": len(group_data),
        "status": "planned" if trip_plan else "planning"
    }

@router.get("/{group_code}")
async def get_trip_details(
    group_code: str,
    current_user: User = Depends(get_current_user)
):
    """Get trip details for a specific group code"""
    # Check if user is a member of this trip
    user_trips = auth.get_user_trips(current_user.id)
    is_member = any(trip.groupCode == group_code for trip in user_trips)
    
    if not is_member:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this trip"
        )
    
    # Check if trip group exists first
    trip_group = storage.get_trip_group(group_code)
    if not trip_group:
        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )
    
    # Get group data (user inputs)
    group_data = storage.get_group_data(group_code)
    
    # If no user data exists yet, create minimal data from trip group
    if not group_data:
        # Trip exists but no users have submitted preferences yet
        # This shouldn't happen with the new creation process, but handle gracefully
        # Return a properly structured response using actual trip_group stored data
        return {
            "groupCode": group_code,
            "groupData": [{
                "name": trip_group.trip_name or "Trip Creator",
                "email": trip_group.creator_email,
                "role": "creator",
                "destinations": trip_group.destinations,  # Real destinations
                "departure_date": trip_group.departure_date,  # Real departure date
                "return_date": trip_group.return_date,  # Real return date
                "budget": trip_group.budget,  # Real budget
                "accommodation_preference": trip_group.accommodation or "standard",
                "description": trip_group.description
            }],
            "tripPlan": None,
            "memberCount": 1,
            "status": "planning"
        }
    
    # Get trip plan if it exists
    trip_plan = None
    try:
        trip_plan = storage.get_trip_plan(group_code)
    except:
        pass  # Trip plan might not exist yet
    
    # Enhance user data with trip_group info for the creator
    enhanced_group_data = []
    for user in group_data:
        user_dict = user.model_dump()
        # For the creator, merge in trip_group data
        if user.role == "creator":
            user_dict.update({
                "trip_name": trip_group.trip_name,
                "departure_date": trip_group.departure_date,
                "return_date": trip_group.return_date,
                "budget": trip_group.budget,
                "accommodation_preference": trip_group.accommodation or user_dict.get("accommodation_preference", "standard"),
                "description": trip_group.description,
                "destinations": trip_group.destinations
            })
        enhanced_group_data.append(user_dict)
    
    return {
        "groupCode": group_code,
        "groupData": enhanced_group_data,
        "tripPlan": trip_plan,
        "memberCount": len(group_data),
        "status": "planned" if trip_plan else "planning"
    }

@router.post("/{group_code}/plan")
async def plan_trip_for_group(
    group_code: str,
    current_user: User = Depends(get_current_user)
):
    """Generate trip plan for a specific group"""
    # Check if user is a member of this trip
    user_trips = auth.get_user_trips(current_user.id)
    is_member = any(trip.groupCode == group_code for trip in user_trips)
    
    if not is_member:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this trip"
        )
    
    try:
        users = storage.get_group_data(group_code)
        
        if not users:
            raise HTTPException(
                status_code=400, 
                detail=f"No users found in group {group_code}"
            )
        
        # Generate the trip plan
        plan_result = await plan_trip(users)
        
        # Save the trip plan
        storage.save_trip_plan(group_code, plan_result)
        
        return plan_result
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate trip plan: {str(e)}"
        )

@router.get("/{group_code}/plan")
async def get_trip_plan(
    group_code: str,
    current_user: User = Depends(get_current_user)
):
    """Get the saved trip plan for a group"""
    # Check if user is a member of this trip
    user_trips = auth.get_user_trips(current_user.id)
    is_member = any(trip.groupCode == group_code for trip in user_trips)
    
    if not is_member:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this trip"
        )
    
    try:
        trip_plan = storage.get_trip_plan(group_code)
        if not trip_plan:
            raise HTTPException(
                status_code=404,
                detail="Trip plan not found. Generate a plan first."
            )
        
        return trip_plan
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail="Trip plan not found. Generate a plan first."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get trip plan: {str(e)}"
        )

@router.put("/{group_code}")
async def update_trip(
    group_code: str,
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Update trip details"""
    # Check if user is a member of this trip
    user_trips = auth.get_user_trips(current_user.id)
    is_member = any(trip.groupCode == group_code for trip in user_trips)
    
    if not is_member:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this trip"
        )
    
    try:
        # For now, just return success - you can implement actual update logic here
        return {
            "message": "Trip updated successfully",
            "groupCode": group_code,
            "updates": updates
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update trip: {str(e)}"
        ) 