# app/api/activities.py
"""
API endpoints for activity search and recommendations using Google Places.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.models.auth import User
from app.api.auth import get_current_user
from app.services.google_places_service import GooglePlacesService

# Initialize the API router
router = APIRouter(tags=["activities"])


class ActivitySearchRequest(BaseModel):
    """Request model for activity search"""
    destination: str
    interests: List[str]
    travel_style: Optional[str] = "balanced"  # budget, balanced, luxury


class ActivitySearchResponse(BaseModel):
    """Response model for activity search"""
    destination: str
    interests: List[str]
    travel_style: str
    total_found: int
    activities: List[Dict[str, Any]]


@router.post("/search", response_model=ActivitySearchResponse)
async def search_activities(
    request: ActivitySearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search for activities in a destination based on interests.
    
    This endpoint allows users to search for activities using the Google Places API.
    Activities are filtered based on interests and travel style preferences.
    
    Args:
        request: ActivitySearchRequest containing destination, interests, and travel style
        current_user: Authenticated user (required)
    
    Returns:
        ActivitySearchResponse with list of found activities
    """
    try:
        # Initialize Google Places service
        places_service = GooglePlacesService()
        
        # Search for activities
        activities = places_service.search_activities_by_interest(
            destination=request.destination,
            interests=request.interests,
            travel_style=request.travel_style
        )
        
        return ActivitySearchResponse(
            destination=request.destination,
            interests=request.interests,
            travel_style=request.travel_style,
            total_found=len(activities),
            activities=activities
        )
        
    except ValueError as e:
        # Handle missing API key or other configuration errors
        raise HTTPException(
            status_code=500,
            detail=f"Service configuration error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search activities: {str(e)}"
        )


@router.get("/search", response_model=ActivitySearchResponse)
async def search_activities_get(
    destination: str = Query(..., description="Destination city name"),
    interests: str = Query(..., description="Comma-separated list of interests"),
    travel_style: str = Query("balanced", description="Travel style: budget, balanced, or luxury"),
    current_user: User = Depends(get_current_user)
):
    """
    Search for activities using GET method (for easy frontend integration).
    
    This is an alternative endpoint that uses query parameters instead of a POST body.
    Useful for simple frontend integrations or direct browser testing.
    
    Args:
        destination: Destination city name (e.g., "Barcelona", "Paris")
        interests: Comma-separated interests (e.g., "Food & Cuisine,Museums & Art")
        travel_style: Travel style preference (budget, balanced, luxury)
        current_user: Authenticated user (required)
    
    Returns:
        ActivitySearchResponse with list of found activities
    """
    try:
        # Parse interests from comma-separated string
        interests_list = [interest.strip() for interest in interests.split(",")]
        
        # Initialize Google Places service
        places_service = GooglePlacesService()
        
        # Search for activities
        activities = places_service.search_activities_by_interest(
            destination=destination,
            interests=interests_list,
            travel_style=travel_style
        )
        
        return ActivitySearchResponse(
            destination=destination,
            interests=interests_list,
            travel_style=travel_style,
            total_found=len(activities),
            activities=activities
        )
        
    except ValueError as e:
        # Handle missing API key or other configuration errors
        raise HTTPException(
            status_code=500,
            detail=f"Service configuration error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search activities: {str(e)}"
        )


@router.get("/interests")
async def get_available_interests():
    """
    Get list of available interest categories.
    
    Returns the list of interest categories that can be used in activity searches.
    This helps frontend applications provide proper interest selection options.
    
    Returns:
        Dict with available interests and their descriptions
    """
    try:
        # Initialize service to get the interest mapping
        places_service = GooglePlacesService()
        
        # Extract available interests from the service
        available_interests = list(places_service.INTEREST_MAPPING.keys())
        
        # Create detailed response with descriptions
        interest_details = {}
        for interest in available_interests:
            mapping = places_service.INTEREST_MAPPING[interest]
            interest_details[interest] = {
                "place_types": mapping["place_types"],
                "keywords": mapping["keywords"]
            }
        
        return {
            "available_interests": available_interests,
            "interest_details": interest_details,
            "travel_styles": ["budget", "balanced", "luxury"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get interests: {str(e)}"
        )


@router.get("/destination/{destination}")
async def get_destination_preview(
    destination: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a preview of activities for a destination (sample from multiple categories).
    
    This endpoint provides a quick preview of what's available in a destination
    by sampling activities from different interest categories.
    
    Args:
        destination: Destination city name
        current_user: Authenticated user (required)
    
    Returns:
        Preview of activities across different categories
    """
    try:
        places_service = GooglePlacesService()
        
        # Get sample activities from different categories
        preview_interests = ["Food & Cuisine", "Museums & Art", "Nature & Hiking"]
        all_activities = []
        
        for interest in preview_interests:
            activities = places_service.search_activities_by_interest(
                destination=destination,
                interests=[interest],
                travel_style="balanced"
            )
            # Take top 2 from each category
            category_activities = activities[:2]
            for activity in category_activities:
                activity["preview_category"] = interest
            all_activities.extend(category_activities)
        
        return {
            "destination": destination,
            "preview_categories": preview_interests,
            "sample_activities": all_activities,
            "total_sampled": len(all_activities)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get destination preview: {str(e)}"
        )