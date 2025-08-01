# app/services/agent_response_parser.py
"""
Consolidated parser to extract structured booking data from LangChain agent responses.
Handles flights, hotels, and activities in one place.
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentResponseParser:
    """
    Parses LangChain agent responses to extract flight, hotel, and activity data
    for use with booking finder services.
    """
    
    # Airline mappings
    AIRLINE_CODES = {
        "delta": "DL",
        "united": "UA", 
        "american": "AA",
        "southwest": "WN",
        "jetblue": "B6",
        "alaska": "AS",
        "frontier": "F9",
        "spirit": "NK",
        "lufthansa": "LH",
        "british airways": "BA",
        "air france": "AF",
        "klm": "KL",
        "emirates": "EK",
        "qatar": "QR",
        "vueling": "VY",
        "ryanair": "FR",
        "easyjet": "U2"
    }
    
    def parse_agent_response(self, agent_response: str, preferences: Dict) -> Dict:
        """
        Main parsing method that extracts all booking data from agent response.
        
        Args:
            agent_response: Raw text response from LangChain agent
            preferences: Original preferences used in the query
            
        Returns:
            Dict with parsed flights, hotel, and activities
        """
        return {
            "flights": self.extract_flight_data(agent_response, preferences),
            "hotel": self.extract_hotel_data(agent_response, preferences),
            "activities": self.extract_activity_data(agent_response),
            "destination": self.extract_selected_destination(agent_response, preferences)
        }
    
    def extract_flight_data(self, response: str, preferences: Dict) -> Dict[str, Dict]:
        """
        Extract flight information for each departure city.
        """
        flights = {}
        flight_groups = preferences.get("flight_groups", [])
        
        for group in flight_groups:
            departure_city = group["departure_city"]
            
            # Try multiple extraction methods
            flight_info = (
                self._extract_structured_flight(response, departure_city) or
                self._extract_flight_from_section(response, departure_city) or
                self._extract_flight_basic(response, departure_city)
            )
            
            if flight_info:
                # Add additional context from preferences
                flight_info["departure_date"] = group["departure_date"]
                flight_info["return_date"] = group["return_date"]
                flight_info["passengers"] = group["passengers"]
                flight_info["passenger_count"] = group["passenger_count"]
                
                flights[departure_city] = flight_info
        
        return flights
    
    def _extract_structured_flight(self, response: str, origin: str) -> Optional[Dict]:
        """Extract flight from structured format."""
        # Look for structured format like:
        # From LAX:
        # - Airline: Delta
        # - Flight: DL447
        # - Route: LAX→BCN
        
        pattern = rf"From {origin}:(.*?)(?=From \w{{3}}:|ACCOMMODATION|HOTEL|$)"
        match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return None
        
        section = match.group(1)
        flight_data = {}
        
        # Extract fields
        airline_match = re.search(r"Airline:\s*([^\n]+)", section)
        flight_match = re.search(r"Flight:\s*(\w+\d+)", section)
        route_match = re.search(r"Route:\s*(\w{3})[→\-](\w{3})", section)
        price_match = re.search(r"Cost:\s*\$(\d+)", section)
        
        # Also try alternative patterns
        if not flight_match:
            # Try pattern like "Delta 447" or "DL447"
            alt_match = re.search(r"(\w+)\s+(\d{3,4})|([A-Z]{2})(\d{3,4})", section)
            if alt_match:
                if alt_match.group(1):  # "Delta 447" format
                    airline = alt_match.group(1)
                    flight_num = alt_match.group(2)
                    airline_code = self.AIRLINE_CODES.get(airline.lower(), airline[:2].upper())
                    flight_data["airline"] = airline.title()
                    flight_data["airline_code"] = airline_code
                    flight_data["flight_number"] = f"{airline_code}{flight_num}"
                else:  # "DL447" format
                    airline_code = alt_match.group(3)
                    flight_num = alt_match.group(4)
                    flight_data["airline_code"] = airline_code
                    flight_data["flight_number"] = f"{airline_code}{flight_num}"
                    flight_data["airline"] = self._get_airline_from_code(airline_code)
        
        if airline_match and not flight_data.get("airline"):
            airline = airline_match.group(1).strip()
            flight_data["airline"] = airline
            flight_data["airline_code"] = self.AIRLINE_CODES.get(airline.lower(), "XX")
        
        if flight_match and not flight_data.get("flight_number"):
            flight_num = flight_match.group(1)
            flight_data["flight_number"] = flight_num
            
            # Extract airline code from flight number if not already set
            if not flight_data.get("airline_code"):
                code_match = re.match(r"([A-Z]{2})\d+", flight_num)
                if code_match:
                    flight_data["airline_code"] = code_match.group(1)
        
        if route_match:
            flight_data["origin"] = route_match.group(1)
            flight_data["destination"] = route_match.group(2)
        else:
            flight_data["origin"] = origin
        
        if price_match:
            flight_data["price"] = int(price_match.group(1))
        
        return flight_data if flight_data.get("flight_number") else None
    
    def _extract_flight_from_section(self, response: str, origin: str) -> Optional[Dict]:
        """Extract flight from less structured format."""
        # Look for patterns like "Delta 447 LAX→BCN June 15, 10:15 AM $580/person"
        patterns = [
            rf"(\w+)\s+(\d{{3,4}})\s+{origin}[→\-](\w{{3}}).*?\$(\d+)",
            rf"{origin}.*?(\w+)\s+flight\s+(\d{{3,4}}).*?\$(\d+)",
            rf"(\w{{2}})(\d{{3,4}})\s+from\s+{origin}.*?\$(\d+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) >= 3:
                    airline = groups[0]
                    flight_num = groups[1]
                    
                    # Handle different group configurations
                    if len(groups) == 4:
                        destination = groups[2] if len(groups[2]) == 3 else "XXX"
                        price = int(groups[3])
                    else:
                        destination = "XXX"
                        price = int(groups[2])
                    
                    # Handle airline code
                    if len(airline) == 2:  # It's already a code
                        airline_code = airline
                        airline_name = self._get_airline_from_code(airline)
                    else:
                        airline_code = self.AIRLINE_CODES.get(airline.lower(), airline[:2].upper())
                        airline_name = airline.title()
                    
                    return {
                        "airline": airline_name,
                        "airline_code": airline_code,
                        "flight_number": f"{airline_code}{flight_num}",
                        "origin": origin,
                        "destination": destination,
                        "price": price
                    }
        
        return None
    
    def _extract_flight_basic(self, response: str, origin: str) -> Optional[Dict]:
        """Basic extraction as last resort."""
        # Just find any flight number and price near the origin
        origin_section = self._find_origin_section(response, origin)
        if not origin_section:
            return None
        
        flight_match = re.search(r"([A-Z]{2}\d{3,4})", origin_section)
        price_match = re.search(r"\$(\d+)", origin_section)
        
        if flight_match and price_match:
            flight_code = flight_match.group(1)
            airline_code = flight_code[:2]
            
            return {
                "airline": self._get_airline_from_code(airline_code),
                "airline_code": airline_code,
                "flight_number": flight_code,
                "origin": origin,
                "destination": "XXX",  # Will need to be inferred
                "price": int(price_match.group(1))
            }
        
        return None
    
    def _find_origin_section(self, response: str, origin: str) -> Optional[str]:
        """Find the section of response about a specific origin."""
        patterns = [
            rf"(From {origin}:.*?)(?=From \w{{3}}:|ACCOMMODATION|$)",
            rf"({origin}\s+flights?:.*?)(?=\w{{3}}\s+flights?:|ACCOMMODATION|$)",
            rf"({origin}.*?departure.*?)(?=\w{{3}}.*?departure|ACCOMMODATION|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1)
        
        return None
    
    def extract_hotel_data(self, response: str, preferences: Dict) -> Dict:
        """
        Extract hotel information with enhanced parsing for structured format.
        """
        hotel_data = {}
        
        # Look for structured hotel section
        hotel_section = self._extract_hotel_section(response)
        if not hotel_section:
            return hotel_data
        
        # Parse structured fields
        patterns = {
            'name': [r"Hotel Name:\s*([^\n]+)", r"Hotel:\s*([^\n]+)", r"Staying at:\s*([^\n]+)"],
            'city': [r"City:\s*([^\n]+)"],
            'check_in': [r"Check-in:\s*(\d{4}-\d{2}-\d{2})"],
            'check_out': [r"Check-out:\s*(\d{4}-\d{2}-\d{2})"],
            'price_per_night': [r"Price:\s*\$(\d+)\s*per night", r"\$(\d+)/night"],
            'total_nights': [r"Total Nights:\s*(\d+)", r"(\d+)\s*nights?"],
            'total_cost': [r"Total (?:Hotel )?Cost:\s*\$(\d+)", r"Total:\s*\$(\d+)"]
        }
        
        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, hotel_section, re.IGNORECASE)
                if match:
                    if field in ['price_per_night', 'total_nights', 'total_cost']:
                        hotel_data[field] = int(match.group(1))
                    else:
                        hotel_data[field] = match.group(1).strip()
                    break
        
        # Parse room configuration
        room_patterns = [
            r"Room Configuration:\s*([^\n]+)",
            r"(\d+)\s*singles?,?\s*(\d+)\s*doubles?",
            r"(\d+)\s*double.+?(\d+)\s*single"
        ]
        
        for pattern in room_patterns:
            match = re.search(pattern, hotel_section, re.IGNORECASE)
            if match:
                if "Configuration" in pattern:
                    hotel_data['room_configuration'] = match.group(1).strip()
                else:
                    singles = int(match.group(2) if "singles" in pattern else match.group(1))
                    doubles = int(match.group(1) if "singles" in pattern else match.group(2))
                    hotel_data['rooms'] = {'singles': singles, 'doubles': doubles}
                    hotel_data['room_configuration'] = f"{singles} singles, {doubles} doubles"
                break
        
        # Ensure we have check-in/out dates
        if 'check_in' not in hotel_data:
            hotel_data['check_in'] = preferences.get('departure_date')
        if 'check_out' not in hotel_data:
            hotel_data['check_out'] = preferences.get('return_date')
        
        # Get destination if not city
        if 'city' not in hotel_data:
            hotel_data['city'] = self.extract_selected_destination(response, preferences)
        
        return hotel_data
    
    def _extract_hotel_section(self, response: str) -> Optional[str]:
        """Extract the hotel/accommodation section from response."""
        patterns = [
            r"\*\*ACCOMMODATION\*\*(.*?)(?=\*\*[A-Z]|\Z)",
            r"ACCOMMODATION(.*?)(?=ACTIVITY|FINAL|$)",
            r"Hotel:(.*?)(?=Activity|Day \d|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(0)  # Include the header for context
        
        return None
    
    def extract_selected_destination(self, response: str, preferences: Dict) -> Optional[str]:
        """Extract which destination was selected."""
        patterns = [
            r"\*\*SELECTED DESTINATION:\s*([^\*\n]+)",
            r"Selected destination:\s*(\w+)",
            r"Best destination:\s*(\w+)",
            r"Winner:\s*(\w+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Check against known destinations
        destinations = preferences.get("top_destinations", [])
        response_lower = response.lower()
        
        for dest in destinations:
            if f"selected destination: {dest.lower()}" in response_lower:
                return dest
        
        return destinations[0] if destinations else None
    
    def extract_activity_data(self, response: str) -> List[Dict]:
        """
        Extract detailed activity information including booking URLs.
        """
        activities = []
        
        # Look for activity itinerary section
        activity_section = self._extract_activity_section(response)
        if not activity_section:
            return activities
        
        # Parse each day's activities
        day_pattern = r"Day\s+(\d+)\s*[-–]?\s*([^:]*?):(.*?)(?=Day\s+\d+|Total Activity Cost|$)"
        day_matches = re.finditer(day_pattern, activity_section, re.IGNORECASE | re.DOTALL)
        
        for day_match in day_matches:
            day_num = int(day_match.group(1))
            day_date = day_match.group(2).strip()
            day_content = day_match.group(3)
            
            # Parse individual activities
            activities_in_day = self._parse_structured_activities(day_content, day_num)
            activities.extend(activities_in_day)
        
        return activities
    
    def _extract_activity_section(self, response: str) -> Optional[str]:
        """Extract the activity itinerary section."""
        patterns = [
            r"\*\*ACTIVITY ITINERARY\*\*(.*?)(?=\*\*[A-Z]|\Z)",
            r"ACTIVITY ITINERARY(.*?)(?=BOOKING LINKS|FINAL|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(0)  # Include header
        
        return None
    
    def _parse_structured_activities(self, day_content: str, day_num: int) -> List[Dict]:
        """Parse structured activity format."""
        activities = []
        
        # Try structured format first (Activity: name, Description: ..., etc.)
        activity_blocks = re.split(r'(?=Activity:)', day_content)
        
        for block in activity_blocks:
            if 'Activity:' in block:
                activity = self._parse_activity_block(block, day_num)
                if activity:
                    activities.append(activity)
        
        # If no structured format found, try line-by-line parsing
        if not activities:
            lines = day_content.strip().split('\n')
            for line in lines:
                if line.strip() and not line.strip().startswith(('Total', 'Day')):
                    activity = self._parse_activity_line(line, day_num)
                    if activity:
                        activities.append(activity)
        
        return activities
    
    def _parse_activity_block(self, block: str, day_num: int) -> Optional[Dict]:
        """Parse a structured activity block."""
        activity = {'day': day_num}
        
        # Parse each field
        patterns = {
            'name': r"Activity:\s*([^\n]+)",
            'description': r"Description:\s*([^\n]+)",
            'duration': r"Duration:\s*(\d+(?:\.\d+)?)\s*hours?",
            'price': r"Price:\s*\$(\d+)\s*per person",
            'platform': r"Booking Platform:\s*([^\n]+)",
            'url': r"Booking URL:\s*(https?://[^\s\n]+)"
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                if field == 'duration':
                    activity['duration_hours'] = float(match.group(1))
                elif field == 'price':
                    activity['price_per_person'] = int(match.group(1))
                elif field == 'platform':
                    activity['booking_platform'] = match.group(1).strip()
                elif field == 'url':
                    activity['booking_url'] = match.group(1).strip()
                else:
                    activity[field] = match.group(1).strip()
        
        # Only return if we have at least a name
        if 'name' in activity:
            activity['has_booking'] = 'booking_url' in activity
            return activity
        
        return None
    
    def _parse_activity_line(self, line: str, day_num: int) -> Optional[Dict]:
        """Parse a single activity line."""
        # Remove bullet points
        line = re.sub(r'^[\-\*•]\s*', '', line).strip()
        
        if not line:
            return None
        
        activity = {
            "day": day_num,
            "has_booking": False
        }
        
        # Extract URL if present
        url_match = re.search(r'(https?://[^\s]+)', line)
        if url_match:
            activity['booking_url'] = url_match.group(1)
            activity['has_booking'] = True
            line = line.replace(url_match.group(1), '').strip()
        
        # Extract price
        price_match = re.search(r'\$(\d+)(?:/person|/pp)?', line)
        if price_match:
            activity['price_per_person'] = int(price_match.group(1))
            line = line.replace(price_match.group(0), '').strip()
        
        # Extract duration
        duration_match = re.search(r'(\d+(?:\.\d+)?)\s*hours?', line)
        if duration_match:
            activity['duration_hours'] = float(duration_match.group(1))
            line = line.replace(duration_match.group(0), '').strip()
        
        # Extract platform if mentioned
        platform_match = re.search(r'(?:on\s+|via\s+|through\s+)(Viator|GetYourGuide|TripAdvisor|Klook)', line, re.IGNORECASE)
        if platform_match:
            activity['booking_platform'] = platform_match.group(1)
            line = line.replace(platform_match.group(0), '').strip()
        
        # Clean up the name
        activity['name'] = line.strip(' -–,')
        
        return activity if activity['name'] else None
    
    def _get_airline_from_code(self, code: str) -> str:
        """Get airline name from IATA code."""
        code_to_airline = {v: k.title() for k, v in self.AIRLINE_CODES.items()}
        return code_to_airline.get(code.upper(), f"Airline {code}")
    
    def prepare_complete_booking_data(self, agent_response: str, preferences: Dict) -> Dict:
        """
        Prepare complete booking data for all components.
        This is the main method to use for getting data ready for booking finder.
        """
        # Parse all components
        parsed_data = self.parse_agent_response(agent_response, preferences)
        
        # Format flights for booking finder
        flights_for_booking = {}
        for city, flight_info in parsed_data['flights'].items():
            if flight_info:
                flights_for_booking[city] = {
                    'airline': flight_info.get('airline'),
                    'airline_code': flight_info.get('airline_code'),
                    'flight_number': flight_info.get('flight_number'),
                    'origin': flight_info.get('origin'),
                    'destination': flight_info.get('destination'),
                    'departure_date': flight_info.get('departure_date'),
                    'return_date': flight_info.get('return_date'),
                    'price': flight_info.get('price')
                }
        
        # Format hotel for booking finder
        hotel_for_booking = None
        if parsed_data['hotel']:
            hotel = parsed_data['hotel']
            hotel_for_booking = {
                'name': hotel.get('name'),
                'city': hotel.get('city', parsed_data['destination']),
                'check_in': hotel.get('check_in'),
                'check_out': hotel.get('check_out'),
                'room_configuration': hotel.get('room_configuration'),
                'total_price': hotel.get('total_cost', 0)
            }
        
        # Format activities
        activities_for_booking = []
        for activity in parsed_data['activities']:
            formatted_activity = {
                'day': activity.get('day'),
                'name': activity.get('name'),
                'description': activity.get('description', ''),
                'duration_hours': activity.get('duration_hours', 2),
                'price_per_person': activity.get('price_per_person'),
                'has_direct_booking': activity.get('has_booking', False),
                'booking_platform': activity.get('booking_platform'),
                'booking_url': activity.get('booking_url')
            }
            activities_for_booking.append(formatted_activity)
        
        return {
            'flights': flights_for_booking,
            'hotel': hotel_for_booking,
            'activities': activities_for_booking,
            'destination': parsed_data['destination'],
            'raw_parsed_data': parsed_data  # Keep original for debugging
        }


# Convenience function for direct use
def get_complete_booking_data(agent_response: str, preferences: Dict) -> Dict:
    """
    Get complete booking data from agent response.
    
    Returns data formatted for booking finder services.
    """
    parser = AgentResponseParser()
    return parser.prepare_complete_booking_data(agent_response, preferences)