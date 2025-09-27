# app/services/complete_booking_integration.py
"""
Fixed integration for extracting booking links that properly handles your data structures.
"""

from typing import Dict, List, Optional
import logging
import re

from app.services.agent_parser import AgentResponseParser
from app.services.booking_finder import BookingFinderService
# DISABLED: Old Tavily search - will be replaced with direct API integration
# from app.services.tavily_client import TavilyClient

logger = logging.getLogger(__name__)


class CompleteBookingIntegration:
    """
    Handles booking link extraction for flights, hotels, and activities.
    Fixed to handle your specific data structures.
    """
    
    def __init__(self):
        self.parser = AgentResponseParser()
        self.booking_finder = BookingFinderService()
        # DISABLED: Tavily client removed during rebuild  
        # self.tavily_client = TavilyClient()
        self.tavily_client = None
    
    async def extract_all_booking_links(self, trip_plan: Dict) -> Dict:
        """
        Extract booking links for all components of the trip.
        """
        try:
            agent_response = trip_plan.get('agent_response', '')
            preferences = trip_plan.get('preferences_used', {})
            flights_override = trip_plan.get('flights_override')  # NEW: prefer passed-in Amadeus flights
            
            # Parse the agent response
            parsed_data = self.parser.parse_agent_response(agent_response, preferences)
            
            # Extract the selected destination from the response
            destination = parsed_data.get('destination')
            if not destination:
                # Try to extract from response text
                dest_match = re.search(r'\*\*SELECTED DESTINATION:\s*([^\*\n]+)', agent_response)
                if dest_match:
                    destination = dest_match.group(1).strip()
                else:
                    destination = preferences.get('top_destinations', ['Unknown'])[0]
            
            # Process each component
            # Prefer explicit flights override when provided (Amadeus source-of-truth)
            flights_input = parsed_data['flights']
            if isinstance(flights_override, dict) and flights_override:
                # Normalize to the same structure as parser output: { departure_city: flight_info }
                flights_input = flights_override

            flight_links = await self._extract_flight_links(flights_input)
            hotel_links = await self._extract_hotel_links(parsed_data['hotel'])
            activity_links = await self._extract_activity_links(
                parsed_data['activities'], 
                destination
            )
            
            return {
                'success': True,
                'destination': destination,
                'flights': flight_links,
                'hotel': hotel_links,
                'activities': activity_links,
                'summary': self._create_summary(flight_links, hotel_links, activity_links)
            }
            
        except Exception as e:
            logger.error(f"Failed to extract booking links: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'flights': {},
                'hotel': {},
                'activities': []
            }
    
    async def _extract_flight_links(self, flights_data: Dict[str, Dict]) -> Dict:
        """Extract booking links for all flights."""
        flight_links = {}
        
        for departure_city, flight_data in flights_data.items():
            if not flight_data:
                continue
            
            try:
                # Ensure we have all required fields
                booking_data = {
                    'airline': flight_data.get('airline', 'Unknown'),
                    'airline_code': flight_data.get('airline_code', 'XX'),
                    'flight_number': flight_data.get('flight_number', ''),
                    'origin': flight_data.get('origin', departure_city),
                    'destination': flight_data.get('destination', ''),
                    'departure_date': flight_data.get('departure_date', ''),
                    'return_date': flight_data.get('return_date', ''),
                    # Prefer total_price if present from Amadeus offers
                    'price': flight_data.get('price', flight_data.get('total_price', 0)),
                    'num_passengers': flight_data.get('num_passengers')
                }
                
                # Get booking links
                results = self.booking_finder.find_flight_booking_links(booking_data)
                
                flight_links[departure_city] = {
                    'flight_info': booking_data,
                    'booking_links': self._combine_links(
                        results.get('direct_booking_links', []),
                        results.get('search_links', [])
                    ),
                    'total_links': results.get('total_links_found', 0),
                    # Surface disclaimer and provenance
                    'subject_to_availability': True,
                    'source': flight_data.get('source', 'parsed')
                }
                
            except Exception as e:
                logger.error(f"Error getting flight links for {departure_city}: {e}")
                flight_links[departure_city] = {
                    'flight_info': flight_data,
                    'booking_links': self._get_fallback_flight_links(flight_data),
                    'error': str(e)
                }
        
        return flight_links
    
    async def _extract_hotel_links(self, hotel_data: Optional[Dict]) -> Dict:
        """Extract booking links for hotel."""
        if not hotel_data:
            return {}
        
        try:
            # Ensure we have all required fields
            booking_data = {
                'name': hotel_data.get('name', 'Unknown Hotel'),
                'city': hotel_data.get('city', 'Unknown'),
                'check_in': hotel_data.get('check_in', ''),
                'check_out': hotel_data.get('check_out', ''),
                'room_configuration': hotel_data.get('room_configuration', ''),
                'total_price': hotel_data.get('total_cost', hotel_data.get('price_per_night', 0) * 5)
            }
            
            results = self.booking_finder.find_hotel_booking_links(booking_data)
            
            return {
                'hotel_info': booking_data,
                'booking_links': self._combine_links(
                    results.get('direct_booking_links', []),
                    results.get('search_links', [])
                ),
                'total_links': results.get('total_links_found', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting hotel links: {e}")
            return {
                'hotel_info': hotel_data,
                'booking_links': self._get_fallback_hotel_links(hotel_data),
                'error': str(e)
            }
    
    async def _extract_activity_links(self, activities: List[Dict], destination: str) -> List[Dict]:
        """Process activity links.
        Accepts either a flat list of activity dicts or the parser's
        {"daily_itinerary": {"day_X": {"activities": [...]}, ...}} structure.
        """
        processed_activities: List[Dict] = []

        # Normalize input to a flat list of activity dicts with 'day'
        flat_activities: List[Dict] = []
        if isinstance(activities, dict):
            daily = activities.get('daily_itinerary', {}) if activities else {}
            for day_key, day_block in daily.items():
                # day_number is preferred, otherwise parse from key like "day_2"
                day_num = day_block.get('day_number') if isinstance(day_block, dict) else None
                if day_num is None and isinstance(day_key, str) and day_key.lower().startswith('day_'):
                    try:
                        day_num = int(day_key.split('_', 1)[1])
                    except Exception:
                        day_num = 1
                day_num = day_num or 1

                day_activities = []
                if isinstance(day_block, dict):
                    day_activities = day_block.get('activities', []) or []
                # Ensure we only add dict activities
                for act in day_activities:
                    if isinstance(act, dict):
                        # Attach day if missing
                        if 'day' not in act:
                            act = {**act, 'day': day_num}
                        flat_activities.append(act)
        elif isinstance(activities, list):
            # Already a flat list
            for act in activities:
                if isinstance(act, dict):
                    flat_activities.append(act)

        # Process each activity
        for activity in flat_activities:
            try:
                processed = {
                    'day': activity.get('day', 1),
                    'name': activity.get('name', 'Unknown Activity'),
                    'description': activity.get('description', ''),
                    'duration_hours': activity.get('duration_hours') or activity.get('duration') or 2,
                    'price_per_person': activity.get('price_per_person') or activity.get('estimated_cost'),
                    'booking_links': []
                }

                # Existing direct booking info
                if activity.get('booking_url'):
                    processed['booking_links'].append({
                        'platform': activity.get('booking_platform', 'Direct'),
                        'url': activity['booking_url'],
                        'type': 'direct'
                    })
                elif activity.get('name') and activity['name'] != 'Unknown Activity':
                    # Try to find booking links via web providers (currently disabled → returns [])
                    additional_links = await self._find_activity_links(
                        activity['name'], destination
                    )
                    processed['booking_links'].extend(additional_links)

                processed['has_booking'] = len(processed['booking_links']) > 0
                processed_activities.append(processed)

            except Exception as e:
                logger.error(f"Error processing activity: {e}")
                # Avoid accessing .get on non-dict
                fallback_name = activity['name'] if isinstance(activity, dict) and 'name' in activity else 'Unknown'
                fallback_day = activity['day'] if isinstance(activity, dict) and 'day' in activity else 1
                processed_activities.append({
                    'day': fallback_day,
                    'name': fallback_name,
                    'error': str(e),
                    'booking_links': []
                })

        return processed_activities
    
    async def _find_activity_links(self, activity_name: str, destination: str) -> List[Dict]:
        """Find booking links for an activity."""
        try:
            # DISABLED: Tavily search removed during rebuild
            # query = f"{activity_name} {destination} book tickets"
            # 
            # results = self.tavily_client.search_with_retry(
            #     query=query,
            #     max_results=5,
            #     include_domains=[
            #         "viator.com", "getyourguide.com", "tripadvisor.com",
            #         "klook.com", "tiqets.com", "headout.com"
            #     ]
            # )
            # 
            # if not results:
            #     return []
            
            # Return empty results during rebuild
            results = {"results": []}
            
            links = []
            for result in results.get('results', [])[:3]:
                if self._is_relevant_link(result, activity_name):
                    links.append({
                        'platform': self._extract_platform(result['url']),
                        'url': result['url'],
                        'type': 'search'
                    })
            
            return links
            
        except Exception as e:
            logger.error(f"Failed to find links for {activity_name}: {e}")
            return []
    
    def _is_relevant_link(self, result: Dict, activity_name: str) -> bool:
        """Check if a search result is relevant."""
        title = result.get('title', '').lower()
        url = result.get('url', '').lower()
        
        # Check for booking platforms
        booking_domains = ['viator.com', 'getyourguide.com', 'tripadvisor.com', 
                          'klook.com', 'tiqets.com', 'headout.com']
        
        if not any(domain in url for domain in booking_domains):
            return False
        
        # Check for activity relevance
        activity_words = [w.lower() for w in activity_name.split() if len(w) > 3]
        matches = sum(1 for word in activity_words if word in title or word in url)
        
        return matches >= len(activity_words) * 0.4
    
    def _extract_platform(self, url: str) -> str:
        """Extract platform name from URL."""
        platforms = {
            'viator.com': 'Viator',
            'getyourguide.com': 'GetYourGuide',
            'tripadvisor.com': 'TripAdvisor',
            'klook.com': 'Klook',
            'tiqets.com': 'Tiqets',
            'headout.com': 'Headout',
            'booking.com': 'Booking.com',
            'hotels.com': 'Hotels.com',
            'expedia.com': 'Expedia',
            'kayak.com': 'Kayak',
            'delta.com': 'Delta',
            'united.com': 'United',
            'aa.com': 'American Airlines'
        }
        
        url_lower = url.lower()
        for domain, name in platforms.items():
            if domain in url_lower:
                return name
        
        return 'Direct'
    
    def _combine_links(self, direct_links: List, search_links: List) -> List[Dict]:
        """Combine and deduplicate links."""
        all_links = []
        seen_urls = set()
        
        # Add direct links first (higher priority)
        for link in direct_links:
            url = link.get('url', '')
            if url and url not in seen_urls:
                all_links.append({
                    **link,
                    'priority': 'high' if link.get('confidence') == 'high' else 'medium'
                })
                seen_urls.add(url)
        
        # Add search links
        for link in search_links:
            url = link.get('url', '')
            if url and url not in seen_urls:
                all_links.append({
                    **link,
                    'priority': 'low'
                })
                seen_urls.add(url)
        
        return all_links
    
    def _get_fallback_flight_links(self, flight_data: Dict) -> List[Dict]:
        """Generate fallback flight links."""
        origin = flight_data.get('origin', '')
        dest = flight_data.get('destination', '')
        dep_date = flight_data.get('departure_date', '')
        ret_date = flight_data.get('return_date', '')
        
        return [
            {
                'platform': 'Google Flights',
                'url': f'https://www.google.com/flights?q={origin}+to+{dest}',
                'type': 'search',
                'priority': 'low'
            },
            {
                'platform': 'Kayak',
                'url': f'https://www.kayak.com/flights/{origin}-{dest}/{dep_date}/{ret_date}',
                'type': 'search',
                'priority': 'low'
            }
        ]
    
    def _get_fallback_hotel_links(self, hotel_data: Dict) -> List[Dict]:
        """Generate fallback hotel links."""
        city = hotel_data.get('city', '').replace(' ', '+')
        name = hotel_data.get('name', '').replace(' ', '+')
        
        return [
            {
                'platform': 'Google',
                'url': f'https://www.google.com/search?q={name}+{city}+hotel+booking',
                'type': 'search',
                'priority': 'low'
            }
        ]
    
    def _create_summary(self, flights: Dict, hotel: Dict, activities: List[Dict]) -> Dict:
        """Create summary of all booking links."""
        # Count flight links
        total_flight_links = sum(
            len(f.get('booking_links', [])) for f in flights.values()
        )
        flight_routes_with_links = sum(
            1 for f in flights.values() if f.get('booking_links')
        )
        
        # Count hotel links
        total_hotel_links = len(hotel.get('booking_links', []))
        
        # Count activity links
        activities_with_booking = sum(
            1 for a in activities if a.get('booking_links')
        )
        total_activity_links = sum(
            len(a.get('booking_links', [])) for a in activities
        )
        
        return {
            'flights': {
                'total_routes': len(flights),
                'routes_with_links': flight_routes_with_links,
                'total_links': total_flight_links
            },
            'hotel': {
                'has_links': total_hotel_links > 0,
                'total_links': total_hotel_links
            },
            'activities': {
                'total_activities': len(activities),
                'activities_with_booking': activities_with_booking,
                'total_links': total_activity_links
            },
            'grand_total_links': total_flight_links + total_hotel_links + total_activity_links
        }


# Async function to use in planner.py
async def get_all_booking_links(trip_plan: Dict) -> Dict:
    """
    Extract all booking links from trip plan.
    
    Args:
        trip_plan: Dict with 'agent_response' and 'preferences_used'
        
    Returns:
        Dict with booking links for flights, hotels, and activities
    """
    integration = CompleteBookingIntegration()
    return await integration.extract_all_booking_links(trip_plan)