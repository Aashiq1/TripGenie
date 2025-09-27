from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.models.group_inputs import GroupInput
from app.services import storage, auth
from app.services.planner import plan_trip
from app.models.auth import User
from app.api.auth import get_current_user
from app.models.group_inputs import TripGroup, UserInput
from app.services.trip import update_trip_group_and_invalidate, can_reset_trip_plan


class TripUpdate(BaseModel):
    destination: Optional[str] = None
    trip_name: Optional[str] = None
    departure_date: Optional[str] = None
    return_date: Optional[str] = None
    budget: Optional[int] = None
    accommodation: Optional[str] = None
    description: Optional[str] = None

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
                "destination": trip_group.destination,  # Real destination
                "departure_date": trip_group.departure_date,  # Real departure date
                "return_date": trip_group.return_date,  # Real return date
                "budget": trip_group.budget,  # Real budget
                "accommodation_preference": trip_group.accommodation or "standard",
                "description": trip_group.description
            }],
            "tripPlan": None,
            "memberCount": 1,
            "status": "planning",
            "destination": trip_group.destination  # Add destination at root level too
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
                "destination": trip_group.destination
            })
        enhanced_group_data.append(user_dict)
    
    return {
        "groupCode": group_code,
        "groupData": enhanced_group_data,
        "tripPlan": trip_plan,
        "memberCount": len(group_data),
        "status": "planned" if trip_plan else "planning"
    }

# === New consolidated routes (mirror /inputs) ===

@router.post("/group")
async def create_trip_group_trip(trip_group: TripGroup, current_user: User = Depends(get_current_user)):
    """Create a new trip group (consolidated under /trip)."""
    try:
        storage.create_trip_group(trip_group)
        auth.add_user_to_trip(current_user.id, trip_group.group_code, role="creator")

        # Create default user input for the creator (same as /inputs/group)
        from app.models.group_inputs import Preferences, Availability
        from datetime import datetime, timedelta

        default_preferences = Preferences(
            vibe=["relaxing"],
            interests=["food"],
            departure_airports=["LAX"],
            budget={"min": 500, "max": 2000},
            trip_duration=7,
            travel_style="balanced",
            pace="balanced",
            accommodation_preference="standard",
            room_sharing="any",
            dietary_restrictions=None,
            additional_info=None
        )

        today = datetime.now()
        availability_dates = []
        for week in range(3):
            week_start = today + timedelta(days=(week * 7))
            availability_dates.append(week_start.strftime("%Y-%m-%d"))

        default_availability = Availability(dates=availability_dates)

        creator_input = UserInput(
            name=current_user.fullName,
            email=current_user.email,
            phone="0000000000",
            role="creator",
            preferences=default_preferences,
            availability=default_availability,
            group_code=trip_group.group_code
        )

        storage.add_user_to_group(creator_input, trip_group.group_code)

        return {"message": "Trip group created successfully", "group": trip_group}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create trip group: {str(e)}")


@router.post("/user")
async def submit_user_input_trip(user_input: UserInput, current_user: User = Depends(get_current_user)):
    """Submit user preferences (consolidated under /trip)."""
    try:
        effective_group_code = getattr(user_input, 'group_code', 'DEFAULT_GROUP') or 'DEFAULT_GROUP'

        existing_group_data = storage.get_group_data(effective_group_code)
        existing_user = None
        for user in existing_group_data or []:
            if user.email == current_user.email:
                existing_user = user
                break

        preserved_role = existing_user.role if (existing_user and existing_user.role) else getattr(user_input, 'role', 'member') or 'member'

        updated_user_input = UserInput(
            name=user_input.name,
            email=user_input.email,
            phone=user_input.phone,
            role=preserved_role,
            preferences=user_input.preferences,
            availability=user_input.availability,
            group_code=effective_group_code
        )

        # Determine if this update requires re-planning by comparing plan-driving fields
        def _to_set(lst):
            try:
                return set(lst or [])
            except Exception:
                return set()

        changed_flags = {
            "availability": False,
            "budget": False,
            "accommodation": False,
            "travel_style": False
        }
        if existing_user is not None:
            try:
                changed_flags["availability"] = _to_set(getattr(existing_user.availability, 'dates', [])) != _to_set(updated_user_input.availability.dates)
            except Exception:
                changed_flags["availability"] = True
            try:
                old_budget = getattr(existing_user.preferences, 'budget', None)
                new_budget = updated_user_input.preferences.budget
                changed_flags["budget"] = not old_budget or (old_budget.min != new_budget.min or old_budget.max != new_budget.max)
            except Exception:
                changed_flags["budget"] = True
            try:
                changed_flags["accommodation"] = getattr(existing_user.preferences, 'accommodation_preference', 'standard') != getattr(updated_user_input.preferences, 'accommodation_preference', 'standard')
            except Exception:
                changed_flags["accommodation"] = True
            try:
                changed_flags["travel_style"] = getattr(existing_user.preferences, 'travel_style', 'balanced') != getattr(updated_user_input.preferences, 'travel_style', 'balanced')
            except Exception:
                changed_flags["travel_style"] = True
        else:
            # New user being added impacts planning
            changed_flags = {k: True for k in changed_flags}

        storage.add_user_to_group(updated_user_input, effective_group_code)
        auth.add_user_to_trip(current_user.id, effective_group_code, role=preserved_role)

        group_data = storage.get_group_data(effective_group_code)
        requires_replan = any(changed_flags.values())
        if requires_replan:
            try:
                storage.delete_trip_plan(effective_group_code)
            except Exception:
                # Non-fatal if no prior plan exists
                pass

        return {
            "success": True,
            "message": "User preferences received successfully",
            "user": updated_user_input,
            "group_code": effective_group_code,
            "current_user_count": len(group_data) if group_data else 1,
            "requires_replan": requires_replan
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process user input: {str(e)}")


@router.get("/groups")
async def list_trip_groups():
    """List all groups (consolidated under /trip)."""
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


@router.delete("/clear")
async def clear_trip_data(group_code: Optional[str] = None):
    """Clear data for a group or all (consolidated under /trip)."""
    try:
        if group_code:
            storage.clear_group_data(group_code)
            return {"message": f"Group {group_code} data cleared successfully"}
        else:
            storage.clear_all_data()
            return {"message": "All data cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")

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
                "destination": trip_group.destination,  # Real destination
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
                "destination": trip_group.destination
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
    updates: TripUpdate,
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
        trip_group = storage.get_trip_group(group_code)
        if not trip_group:
            raise HTTPException(
                status_code=404,
                detail="Trip not found"
            )

        trip_group, requires_replanning, changed = update_trip_group_and_invalidate(
            group_code, updates.model_dump(exclude_unset=True)
        )

        group_payload = trip_group if isinstance(trip_group, dict) else getattr(trip_group, "model_dump", lambda: trip_group)()
        return {
            "message": "Trip updated successfully",
            "group": group_payload,
            "requires_replan": bool(requires_replanning)
        }
    except ValueError as e:
        # Map known service error to 404
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update trip: {str(e)}")

@router.delete("/{group_code}/plan")
async def reset_trip_plan(
    group_code: str,
    current_user: User = Depends(get_current_user)
):
    """Reset the trip plan for a specific group"""
    user_trips = auth.get_user_trips(current_user.id)
    is_member = any(trip.groupCode == group_code for trip in user_trips)
    if not is_member:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this trip"
        )
    
    trip_group = storage.get_trip_group(group_code)
    if not trip_group:
        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )
    
    if not can_reset_trip_plan(current_user.email, trip_group):
        raise HTTPException(
            status_code=403,
            detail="You are not the creator of this trip"
        )
    
    try:
        existing = storage.get_trip_plan(group_code)
        deleted = bool(existing)
        if deleted:
            storage.delete_trip_plan(group_code)
        return {
            "message": "Trip plan reset",
            "deleted": deleted
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset trip: {str(e)}")