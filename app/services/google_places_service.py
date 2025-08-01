# app/services/google_places_service.py
"""Google Places API (New) service for finding free activities, restaurants, and POIs."""

import os
import requests
from typing import Dict, List, Optional, Tuple
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GooglePlacesService:
    """Service for finding activities using Google Places API (New)."""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY environment variable not set")
        
        # New Places API base URL
        self.base_url = "https://places.googleapis.com/v1/places"
        
        # Common headers for new API
        self.headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": ""  # Will be set per request for cost optimization
        }
        
        # Map user interests to Google Places types and keywords
        self.INTEREST_MAPPING = {
            "Food & Cuisine": {
                "place_types": ["restaurant", "cafe", "bakery", "meal_takeaway"],
                "keywords": ["local restaurant", "authentic cuisine", "traditional food", "local cafe"]
            },
            "Museums & Art": {
                "place_types": ["museum", "art_gallery"],
                "keywords": ["art museum", "history museum", "cultural center", "art gallery"]
            },
            "Nature & Hiking": {
                "place_types": ["park", "natural_feature"],
                "keywords": ["hiking trail", "nature park", "botanical garden", "scenic viewpoint"]
            },
            "Architecture": {
                "place_types": ["church", "synagogue", "mosque", "place_of_worship"],
                "keywords": ["historic building", "architecture", "cathedral", "historic site"]
            },
            "Shopping": {
                "place_types": ["shopping_mall", "store"],
                "keywords": ["local market", "shopping district", "artisan shops", "souvenir shops"]
            },
            "Local Markets": {
                "place_types": ["supermarket", "store"],
                "keywords": ["local market", "farmers market", "food market", "traditional market"]
            },
            "History": {
                "place_types": ["museum", "church", "cemetery"],
                "keywords": ["historic site", "monument", "memorial", "heritage site"]
            },
            "Photography": {
                "place_types": ["tourist_attraction", "park"],
                "keywords": ["scenic viewpoint", "photo spot", "panoramic view", "landmark"]
            },
            "Beaches": {
                "place_types": ["natural_feature"],
                "keywords": ["beach", "waterfront", "coastal view", "seaside"]
            },
            "Nightlife": {
                "place_types": ["bar", "night_club"],
                "keywords": ["cocktail bar", "rooftop bar", "nightclub", "live music venue"]
            }
        }
        
        # Price level mapping (same as legacy API)
        self.PRICE_LEVELS = {
            "PRICE_LEVEL_FREE": "Free",
            "PRICE_LEVEL_INEXPENSIVE": "$",
            "PRICE_LEVEL_MODERATE": "$$", 
            "PRICE_LEVEL_EXPENSIVE": "$$$",
            "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$"
        }
    
    def search_activities_by_interest(self, destination: str, interests: List[str], 
                                    travel_style: str = "balanced") -> List[Dict]:
        """
        Search for activities based on user interests using New Places API.
        
        Args:
            destination: City name (e.g., "Madrid", "Barcelona")
            interests: List of user interests
            travel_style: budget/balanced/luxury (affects price filtering)
            
        Returns:
            List of activity dictionaries with standardized format
        """
        all_activities = []
        
        # Get destination coordinates first
        destination_coords = self._get_destination_coordinates(destination)
        if not destination_coords:
            logger.error(f"Could not find coordinates for destination: {destination}")
            return []
        
        lat, lng = destination_coords
        
        for interest in interests:
            if interest in self.INTEREST_MAPPING:
                mapping = self.INTEREST_MAPPING[interest]
                
                # Search by place types using Nearby Search
                for place_type in mapping["place_types"]:
                    activities = self._search_nearby_places(
                        lat, lng, [place_type], destination, interest
                    )
                    all_activities.extend(activities)
                
                # Search by keywords using Text Search
                for keyword in mapping["keywords"]:
                    activities = self._search_places_by_text(
                        f"{keyword} in {destination}", destination, interest
                    )
                    all_activities.extend(activities)
        
        # Filter and deduplicate
        filtered_activities = self._filter_activities(all_activities, travel_style)
        unique_activities = self._remove_duplicates(filtered_activities)
        
        return unique_activities[:20]  # Limit results
    
    def _get_destination_coordinates(self, destination: str) -> Optional[Tuple[float, float]]:
        """Get latitude and longitude for a destination using Text Search."""
        try:
            url = f"{self.base_url}:searchText"
            
            # Set field mask for cost optimization
            headers = self.headers.copy()
            headers["X-Goog-FieldMask"] = "places.location"
            
            payload = {
                "textQuery": destination,
                "maxResultCount": 1
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("places"):
                location = data["places"][0]["location"]
                return location["latitude"], location["longitude"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting coordinates for {destination}: {e}")
            return None
    
    def _search_nearby_places(self, lat: float, lng: float, place_types: List[str], 
                            destination: str, interest: str) -> List[Dict]:
        """Search for places near coordinates by type using Nearby Search."""
        try:
            url = f"{self.base_url}:searchNearby"
            
            # Set comprehensive field mask for all data we need
            headers = self.headers.copy()
            headers["X-Goog-FieldMask"] = (
                "places.id,places.displayName,places.types,places.priceLevel,"
                "places.rating,places.userRatingCount,places.location,"
                "places.formattedAddress,places.websiteUri,places.nationalPhoneNumber,"
                "places.currentOpeningHours,places.photos"
            )
            
            payload = {
                "includedTypes": place_types,
                "maxResultCount": 10,
                "locationRestriction": {
                    "circle": {
                        "center": {
                            "latitude": lat,
                            "longitude": lng
                        },
                        "radius": 5000.0  # 5km radius
                    }
                }
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            activities = []
            for place in data.get("places", []):
                activity = self._parse_place_to_activity(place, destination, interest)
                if activity:
                    activities.append(activity)
            
            return activities
            
        except Exception as e:
            logger.error(f"Error searching nearby places: {e}")
            return []
    
    def _search_places_by_text(self, query: str, destination: str, interest: str) -> List[Dict]:
        """Search for places using text query with Text Search."""
        try:
            url = f"{self.base_url}:searchText"
            
            # Set comprehensive field mask
            headers = self.headers.copy()
            headers["X-Goog-FieldMask"] = (
                "places.id,places.displayName,places.types,places.priceLevel,"
                "places.rating,places.userRatingCount,places.location,"
                "places.formattedAddress,places.websiteUri,places.nationalPhoneNumber,"
                "places.currentOpeningHours,places.photos"
            )
            
            payload = {
                "textQuery": query,
                "maxResultCount": 8
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            activities = []
            for place in data.get("places", []):
                activity = self._parse_place_to_activity(place, destination, interest)
                if activity:
                    activities.append(activity)
            
            return activities
            
        except Exception as e:
            logger.error(f"Error searching places by text: {e}")
            return []
    
    def _parse_place_to_activity(self, place: Dict, destination: str, interest: str) -> Optional[Dict]:
        """Convert New Places API result to standardized activity format."""
        try:
            # Basic info (new API format)
            name = place.get("displayName", {}).get("text", "")
            place_id = place.get("id", "")
            
            if not name or len(name) < 3:
                return None
            
            # Determine if it's free or paid
            price_level = place.get("priceLevel", "PRICE_LEVEL_FREE")
            is_free = price_level == "PRICE_LEVEL_FREE"
            
            # Build activity
            activity = {
                "name": name,
                "description": self._create_description(place, interest),
                "interest": interest,
                "activity_type": self._determine_activity_type(place, interest),
                "location": {
                    "address": place.get("formattedAddress", ""),
                    "lat": place.get("location", {}).get("latitude"),
                    "lng": place.get("location", {}).get("longitude")
                },
                "is_free": is_free,
                "is_bookable": not is_free,  # Free places usually don't need booking
                "price_info": {
                    "price_level": self.PRICE_LEVELS.get(price_level, "Unknown"),
                    "amount_usd": 0 if is_free else None
                },
                "rating": place.get("rating"),
                "user_ratings_total": place.get("userRatingCount", 0),
                "photos": self._get_photo_urls(place.get("photos", [])[:2]),
                "website": place.get("websiteUri"),
                "phone": place.get("nationalPhoneNumber"),
                "opening_hours": self._parse_opening_hours(place.get("currentOpeningHours")),
                "duration": self._estimate_duration(place, interest),
                "google_place_id": place_id,
                "source": "google_places_new"
            }
            
            return activity
            
        except Exception as e:
            logger.error(f"Error parsing place to activity: {e}")
            return None
    
    def _create_description(self, place: Dict, interest: str) -> str:
        """Create a descriptive text for the activity."""
        name = place.get("displayName", {}).get("text", "")
        types = place.get("types", [])
        rating = place.get("rating")
        
        # Start with basic description
        description = f"Explore {name}"
        
        # Add type context
        if "restaurant" in types or "cafe" in types:
            description = f"Dine at {name}"
        elif "museum" in types:
            description = f"Visit {name}"
        elif "park" in types:
            description = f"Relax at {name}"
        elif "church" in types or "place_of_worship" in types:
            description = f"Visit the historic {name}"
        
        # Add rating if available
        if rating and rating >= 4.0:
            description += f" (Highly rated: {rating}★)"
        
        # Add activity type context
        if interest == "Photography":
            description += " - Perfect for photos"
        elif interest == "Nature & Hiking":
            description += " - Great for outdoor activities"
        elif interest == "Food & Cuisine":
            description += " - Experience local cuisine"
        
        return description
    
    def _determine_activity_type(self, place: Dict, interest: str) -> str:
        """Determine the activity type based on place and interest."""
        types = place.get("types", [])
        
        if any(t in types for t in ["restaurant", "cafe", "bakery"]):
            return "dining"
        elif any(t in types for t in ["museum", "art_gallery"]):
            return "cultural"
        elif any(t in types for t in ["park", "natural_feature"]):
            return "outdoor"
        elif any(t in types for t in ["church", "synagogue", "mosque"]):
            return "historical"
        elif any(t in types for t in ["shopping_mall", "store"]):
            return "shopping"
        elif any(t in types for t in ["bar", "night_club"]):
            return "nightlife"
        else:
            return "sightseeing"
    
    def _get_photo_urls(self, photos: List[Dict]) -> List[str]:
        """Get photo URLs from New Places API photos."""
        photo_urls = []
        for photo in photos:
            if photo.get("name"):
                # New API photo URL format
                url = f"https://places.googleapis.com/v1/{photo['name']}/media"
                url += f"?maxWidthPx=400&key={self.api_key}"
                photo_urls.append(url)
        return photo_urls
    
    def _parse_opening_hours(self, opening_hours: Optional[Dict]) -> Optional[Dict]:
        """Parse opening hours information from new API format."""
        if not opening_hours:
            return None
        
        return {
            "open_now": opening_hours.get("openNow"),
            "weekday_text": opening_hours.get("weekdayDescriptions", [])
        }
    
    def _estimate_duration(self, place: Dict, interest: str) -> float:
        """Estimate duration in hours for visiting this place."""
        types = place.get("types", [])
        
        if any(t in types for t in ["restaurant", "cafe"]):
            return 1.5  # Dining experience
        elif any(t in types for t in ["museum", "art_gallery"]):
            return 2.0  # Museum visit
        elif any(t in types for t in ["park"]):
            return 1.0  # Park stroll
        elif any(t in types for t in ["church", "synagogue", "mosque"]):
            return 0.5  # Quick visit
        elif any(t in types for t in ["shopping_mall", "store"]):
            return 1.0  # Shopping
        elif any(t in types for t in ["bar", "night_club"]):
            return 2.0  # Nightlife
        else:
            return 1.0  # Default
    
    def _filter_activities(self, activities: List[Dict], travel_style: str) -> List[Dict]:
        """Filter activities based on travel style and quality."""
        filtered = []
        
        for activity in activities:
            # Require minimum rating for quality
            rating = activity.get("rating")
            if rating and rating < 3.5:
                continue
            
            # Filter by travel style price preferences
            price_level = activity.get("price_info", {}).get("price_level", "Free")
            if travel_style == "budget" and price_level in ["$$$", "$$$$"]:
                continue
            elif travel_style == "luxury" and price_level in ["Free", "$"]:
                continue
            
            # Require reasonable number of reviews
            reviews = activity.get("user_ratings_total", 0)
            if reviews < 10 and not activity.get("is_free"):  # Free places can have fewer reviews
                continue
            
            filtered.append(activity)
        
        return filtered
    
    def _remove_duplicates(self, activities: List[Dict]) -> List[Dict]:
        """Remove duplicate activities based on name similarity."""
        unique = []
        seen_names = set()
        
        for activity in activities:
            name = activity.get("name", "").lower()
            
            # Check for similar names
            is_duplicate = False
            for seen_name in seen_names:
                if self._are_names_similar(name, seen_name):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(activity)
                seen_names.add(name)
        
        return unique
    
    def _are_names_similar(self, name1: str, name2: str) -> bool:
        """Check if two activity names are similar enough to be duplicates."""
        if not name1 or not name2:
            return False
        
        # Exact match
        if name1 == name2:
            return True
        
        # Check if one name contains the other (for things like "Museum" vs "Museum of Art")
        if len(name1) > 5 and len(name2) > 5:
            if name1 in name2 or name2 in name1:
                return True
        
        return False


def test_google_places_new():
    """Test function for Google Places API (New)."""
    try:
        service = GooglePlacesService()
        
        # Test with Madrid
        activities = service.search_activities_by_interest(
            destination="Madrid",
            interests=["Food & Cuisine", "Museums & Art"],
            travel_style="balanced"
        )
        
        print(f"Found {len(activities)} activities in Madrid:")
        for activity in activities[:5]:
            print(f"- {activity['name']} ({activity['activity_type']})")
            print(f"  Rating: {activity.get('rating', 'N/A')}")
            print(f"  Price: {activity['price_info']['price_level']}")
            print()
        
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    test_google_places_new() 