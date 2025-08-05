# app/services/activity_providers.py
"""
Abstract base for activity providers and concrete implementations.
Designed for easy extension with GetYourGuide, Viator, etc.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.services.google_places_service import GooglePlacesService


class ActivityProvider(ABC):
    """Abstract base class for all activity providers."""
    
    @abstractmethod
    def search_activities(self, destination: str, interests: List[str], travel_style: str) -> List[Dict[str, Any]]:
        """
        Search for activities in a destination.
        
        Args:
            destination: Destination city name
            interests: List of user interests
            travel_style: budget/balanced/luxury
            
        Returns:
            List of standardized activity dictionaries
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'Google Places', 'GetYourGuide')"""
        pass
    
    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Type of provider (e.g., 'places', 'tours', 'experiences')"""
        pass


class GooglePlacesProvider(ActivityProvider):
    """Google Places API provider for local activities and venues."""
    
    def __init__(self):
        self.service = GooglePlacesService()
    
    def search_activities(self, destination: str, interests: List[str], travel_style: str) -> List[Dict[str, Any]]:
        """Search Google Places for activities."""
        activities = self.service.search_activities_by_interest(
            destination=destination,
            interests=interests,
            travel_style=travel_style
        )
        
        # Add provider metadata
        for activity in activities:
            activity["provider"] = self.provider_name
            activity["provider_type"] = self.provider_type
            activity["bookable_online"] = False  # Most Google Places results are venues, not bookable tours
        
        return activities
    
    @property
    def provider_name(self) -> str:
        return "Google Places"
    
    @property
    def provider_type(self) -> str:
        return "places"


class GetYourGuideProvider(ActivityProvider):
    """GetYourGuide API provider for bookable tours and experiences."""
    
    def __init__(self):
        # TODO: Initialize GetYourGuide API client
        pass
    
    def search_activities(self, destination: str, interests: List[str], travel_style: str) -> List[Dict[str, Any]]:
        """Search GetYourGuide for bookable tours and experiences."""
        # TODO: Implement GetYourGuide API integration
        # This will return tours, experiences, skip-the-line tickets, etc.
        
        # Placeholder implementation
        print(f"🚧 GetYourGuide integration coming soon for {destination}")
        return []
    
    @property
    def provider_name(self) -> str:
        return "GetYourGuide"
    
    @property
    def provider_type(self) -> str:
        return "tours"


class ViatorProvider(ActivityProvider):
    """Viator API provider for bookable tours and activities."""
    
    def __init__(self):
        # TODO: Initialize Viator API client
        pass
    
    def search_activities(self, destination: str, interests: List[str], travel_style: str) -> List[Dict[str, Any]]:
        """Search Viator for bookable activities."""
        # TODO: Implement Viator API integration
        # This will return tours, activities, day trips, etc.
        
        # Placeholder implementation
        print(f"🚧 Viator integration coming soon for {destination}")
        return []
    
    @property
    def provider_name(self) -> str:
        return "Viator"
    
    @property
    def provider_type(self) -> str:
        return "activities"


class ActivityAggregator:
    """
    Aggregates activities from multiple providers for comprehensive results.
    """
    
    def __init__(self):
        self.providers = [
            GooglePlacesProvider(),
            # GetYourGuideProvider(),  # TODO: Enable when API is integrated
            # ViatorProvider(),        # TODO: Enable when API is integrated
        ]
    
    def search_all_providers(self, destination: str, interests: List[str], travel_style: str) -> Dict[str, List[Dict]]:
        """
        Search all providers and return categorized results.
        
        Returns:
            Dictionary with provider names as keys and activity lists as values
        """
        results = {}
        
        for provider in self.providers:
            try:
                activities = provider.search_activities(destination, interests, travel_style)
                results[provider.provider_name] = activities
                print(f"✅ {provider.provider_name}: Found {len(activities)} activities")
            except Exception as e:
                print(f"❌ {provider.provider_name}: Error - {str(e)}")
                results[provider.provider_name] = []
        
        return results
    
    def get_combined_activities(self, destination: str, interests: List[str], travel_style: str, max_per_provider: int = 20) -> List[Dict]:
        """
        Get combined activities from all providers, with balanced representation.
        
        Args:
            destination: Destination city name
            interests: List of user interests  
            travel_style: budget/balanced/luxury
            max_per_provider: Maximum activities to take from each provider
            
        Returns:
            Combined list of activities from all providers
        """
        all_results = self.search_all_providers(destination, interests, travel_style)
        combined_activities = []
        
        # Add activities from each provider
        for provider_name, activities in all_results.items():
            # Take up to max_per_provider activities from each
            provider_activities = activities[:max_per_provider]
            combined_activities.extend(provider_activities)
            
            if provider_activities:
                print(f"📍 Added {len(provider_activities)} activities from {provider_name}")
        
        # Sort by rating and provider type (places first, then tours)
        combined_activities.sort(key=lambda x: (
            x.get("provider_type") != "places",  # Places first
            -(x.get("rating", 0) or 0)          # Then by rating descending
        ))
        
        print(f"🎯 Total combined activities: {len(combined_activities)}")
        return combined_activities
    
    def add_provider(self, provider: ActivityProvider):
        """Add a new activity provider to the aggregator."""
        self.providers.append(provider)
        print(f"➕ Added provider: {provider.provider_name} ({provider.provider_type})")
    
    def list_providers(self) -> List[str]:
        """List all available providers."""
        return [provider.provider_name for provider in self.providers]