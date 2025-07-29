# app/api/trip_refinement_endpoints.py
"""
API endpoints for trip refinement chat feature.
These are the URLs your frontend will call.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional, List, Any

from app.services.trip_refinement_chat import refinement_service
from app.services import storage  # Your storage service for getting trip plans

# Create router for all refinement endpoints
router = APIRouter(prefix="/api/trips", tags=["trip-refinement"])


# Request/Response Models (what frontend sends/receives)
class RefinementChatRequest(BaseModel):
    """What frontend sends when user types a message"""
    message: str
    user_email: str


class RefinementChatResponse(BaseModel):
    """What frontend receives back"""
    success: bool
    response: Optional[str] = None  # AI's response
    error: Optional[str] = None
    changes_made: List[str] = []  # ["flights", "hotel"] if changes detected
    requires_regeneration: bool = False


# ENDPOINT 1: Start a refinement session
@router.post("/{group_code}/refinement/start")
async def start_refinement_session(
    group_code: str,
    user_email: str
) -> Dict:
    """
    Start a new refinement chat session.
    
    Frontend calls this when user clicks "Refine Trip" button.
    
    URL: POST /api/trips/BARCELONA123/refinement/start?user_email=john@email.com
    """
    # Get the saved trip plan from database/storage
    trip_plan = storage.get_trip_plan(group_code)
    
    if not trip_plan:
        raise HTTPException(status_code=404, detail="Trip plan not found")
    
    # Start the session (this creates TripRefinementChat instance)
    result = await refinement_service.start_refinement_session(
        group_code=group_code,
        user_email=user_email,
        trip_plan=trip_plan
    )
    
    if not result["success"]:
        raise HTTPException(status_code=403, detail=result["error"])
    
    return result


# ENDPOINT 2: Send a chat message
@router.post("/{group_code}/refinement/chat")
async def send_refinement_message(
    group_code: str,
    request: RefinementChatRequest
) -> RefinementChatResponse:
    """
    Send a message in the refinement chat.
    
    Frontend calls this every time user sends a message.
    
    URL: POST /api/trips/BARCELONA123/refinement/chat
    Body: {
        "message": "Find cheaper flights from LAX",
        "user_email": "john@email.com"
    }
    """
    # Process the message
    result = await refinement_service.process_message(
        session_id=f"{group_code}:{request.user_email}",
        message=request.message
    )
    
    # If no session exists, try to create one
    if not result["success"] and "No active session" in result.get("error", ""):
        # Get trip plan and start session
        trip_plan = storage.get_trip_plan(group_code)
        if trip_plan:
            # Start new session
            start_result = await refinement_service.start_refinement_session(
                group_code=group_code,
                user_email=request.user_email,
                trip_plan=trip_plan
            )
            
            if start_result["success"]:
                # Retry the message
                result = await refinement_service.process_message(
                    session_id=f"{group_code}:{request.user_email}",
                    message=request.message
                )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return RefinementChatResponse(**result)


# ENDPOINT 3: Get chat history
@router.get("/{group_code}/refinement/history")
async def get_chat_history(
    group_code: str,
    user_email: str
) -> Dict:
    """
    Get all previous messages in the chat.
    
    Frontend calls this to restore chat on page reload.
    
    URL: GET /api/trips/BARCELONA123/refinement/history?user_email=john@email.com
    """
    session_id = f"{group_code}:{user_email}"
    session = refinement_service.active_sessions.get(session_id)
    
    if not session:
        return {
            "success": True,
            "history": [],
            "message": "No active session"
        }
    
    # Verify user is the creator
    if user_email != session.creator_email:
        raise HTTPException(status_code=403, detail="Only trip creator can view history")
    
    return {
        "success": True,
        "history": session.get_chat_history(),
        "current_itinerary": session.current_itinerary
    }


# ENDPOINT 4: Apply changes from chat
@router.post("/{group_code}/refinement/apply")
async def apply_refinement_changes(
    group_code: str,
    user_email: str,
    changes: Dict[str, Any]
) -> Dict:
    """
    Apply the changes discussed in chat to the actual trip.
    
    Frontend calls this when user clicks "Apply These Changes".
    
    URL: POST /api/trips/BARCELONA123/refinement/apply
    Body: {
        "flights": {"LAX": "Spirit $380"},
        "hotel": "W Barcelona"
    }
    """
    # This is where you'd:
    # 1. Update the trip plan with new selections
    # 2. Regenerate booking links
    # 3. Save to database
    
    # For now, just return success
    return {
        "success": True,
        "message": "Changes applied successfully",
        "updated_trip": "Would contain new trip plan here"
    }


# ENDPOINT 5: End session
@router.post("/{group_code}/refinement/end")
async def end_refinement_session(
    group_code: str,
    user_email: str
) -> Dict:
    """
    End the chat session and free up memory.
    
    Frontend calls this when user closes chat window.
    
    URL: POST /api/trips/BARCELONA123/refinement/end?user_email=john@email.com
    """
    session_id = f"{group_code}:{user_email}"
    refinement_service.end_session(session_id)
    
    return {
        "success": True,
        "message": "Session ended"
    }


# Add router to your main FastAPI app
def setup_refinement_routes(app):
    """Call this in your main.py or app.py"""
    app.include_router(router)