# app/services/booking_finder.py
"""Service for finding specific booking links for flights and hotels."""

from typing import Dict, List, Optional
from app.services.tavily_client import TavilyClient

class BookingFinderService:
    """Find specific booking links for flights and hotels using Tavily."""
    
    FLIGHT_BOOKING_DOMAINS = [
        "delta.com", "united.com", "aa.com", 
        "southwest.com", "jetblue.com", "spirit.com",
        "alaskaair.com", "frontier.com",
        "lufthansa.com", "britishairways.com", "airfrance.com",
        "expedia.com", "kayak.com", "google.com/flights",
        "priceline.com", "momondo.com"
    ]
    
    HOTEL_BOOKING_DOMAINS = [
        "booking.com", "hotels.com", "expedia.com",
        "agoda.com", "marriott.com", "hilton.com", 
        "hyatt.com", "ihg.com", "accor.com",
        "priceline.com", "trivago.com", "hotelscombined.com"
    ]
    
    def __init__(self, tavily_client: Optional[TavilyClient] = None):
        self.client = tavily_client or TavilyClient()
    
    def find_flight_booking_links(self, flight_data: Dict) -> Dict:
        """
        Find booking links for a specific flight.
        
        Args:
            flight_data: {
                "airline": "Delta",
                "airline_code": "DL",
                "flight_number": "DL447",
                "origin": "LAX",
                "destination": "BCN",
                "departure_date": "2024-06-15",
                "return_date": "2024-06-20",
                "price": 580
            }
        
        Returns:
            Dict with direct booking links and search links
        """
        airline = flight_data.get("airline", "")
        flight_number = flight_data.get("flight_number", "")
        route = f"{flight_data.get('origin')} to {flight_data.get('destination')}"
        date = flight_data.get("departure_date", "")
        
        # Try different search strategies
        search_queries = [
            f"book {airline} flight {flight_number} {date}",
            f"{flight_number} {route} booking",
            f"buy tickets {airline} {flight_number}"
        ]
        
        all_results = []
        
        for query in search_queries:
            results = self.client.search(
                query=query,
                max_results=5,
                search_depth="basic",
                include_domains=self.FLIGHT_BOOKING_DOMAINS
            )
            
            if results and results.get("results"):
                all_results.extend(results["results"])
        
        # Parse results
        booking_links = self._parse_flight_results(all_results, flight_data)
        
        # Add fallback search links
        search_links = self._generate_flight_search_links(flight_data)
        
        return {
            "flight_info": {
                "flight_number": flight_number,
                "route": route,
                "date": date,
                "price": flight_data.get("price")
            },
            "direct_booking_links": booking_links,
            "search_links": search_links,
            "total_links_found": len(booking_links)
        }
    
    def find_hotel_booking_links(self, hotel_data: Dict) -> Dict:
        """
        Find booking links for a specific hotel.
        
        Args:
            hotel_data: {
                "name": "Hotel Barcelona Center",
                "city": "Barcelona",
                "check_in": "2024-06-15",
                "check_out": "2024-06-20",
                "room_configuration": "2 singles, 1 double",
                "total_price": 540
            }
        
        Returns:
            Dict with hotel booking links
        """
        hotel_name = hotel_data.get("name", "")
        city = hotel_data.get("city", "")
        
        # Search queries
        search_queries = [
            f"{hotel_name} {city} booking.com",
            f"book {hotel_name} {city} hotels.com",
            f"{hotel_name} official website reservations"
        ]
        
        all_results = []
        
        for query in search_queries:
            results = self.client.search(
                query=query,
                max_results=5,
                search_depth="basic",
                include_domains=self.HOTEL_BOOKING_DOMAINS
            )
            
            if results and results.get("results"):
                all_results.extend(results["results"])
        
        # Parse results
        booking_links = self._parse_hotel_results(all_results, hotel_data)
        
        # Group by platform and deduplicate
        unique_links = self._deduplicate_hotel_links(booking_links)
        
        # Add fallback search links
        search_links = self._generate_hotel_search_links(hotel_data)
        
        return {
            "hotel_info": {
                "name": hotel_name,
                "city": city,
                "check_in": hotel_data.get("check_in"),
                "check_out": hotel_data.get("check_out"),
                "room_configuration": hotel_data.get("room_configuration")
            },
            "direct_booking_links": unique_links,
            "search_links": search_links,
            "total_links_found": len(unique_links)
        }
    
    def _parse_flight_results(self, results: List[Dict], flight_data: Dict) -> List[Dict]:
        """Parse search results for flight booking links."""
        booking_links = []
        flight_number = flight_data.get("flight_number", "").lower()
        airline = flight_data.get("airline", "").lower()
        
        for result in results:
            url = result.get("url", "")
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            
            # Check relevance
            is_relevant = (
                flight_number in title or 
                flight_number in snippet or
                (airline in url.lower() and "booking" in url.lower())
            )
            
            if is_relevant:
                platform = self._identify_platform(url)
                confidence = self._calculate_confidence(result, flight_data)
                
                booking_links.append({
                    "platform": platform,
                    "url": url,
                    "title": result.get("title"),
                    "type": "direct" if airline in url.lower() else "aggregator",
                    "confidence": confidence
                })
        
        # Sort by confidence
        booking_links.sort(key=lambda x: x["confidence"], reverse=True)
        
        return booking_links
    
    def _parse_hotel_results(self, results: List[Dict], hotel_data: Dict) -> List[Dict]:
        """Parse search results for hotel booking links."""
        booking_links = []
        hotel_name_lower = hotel_data.get("name", "").lower()
        
        for result in results:
            url = result.get("url", "")
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            
            # Check if this is about our specific hotel
            is_relevant = (
                hotel_name_lower in title or 
                hotel_name_lower in snippet or
                hotel_name_lower in url.lower()
            )
            
            if is_relevant:
                platform = self._identify_platform(url)
                
                # Check if it's a booking page
                is_booking_page = any(term in url.lower() 
                                    for term in ["hotel", "property", "accommodation", "book"])
                
                if is_booking_page:
                    booking_links.append({
                        "platform": platform,
                        "url": url,
                        "title": result.get("title"),
                        "has_availability": "available" in snippet or "book" in snippet,
                        "confidence": "high" if hotel_name_lower in url.lower() else "medium"
                    })
        
        return booking_links
    
    def _identify_platform(self, url: str) -> str:
        """Identify which platform a URL belongs to."""
        url_lower = url.lower()
        
        # Check airlines
        airline_map = {
            "delta.com": "Delta",
            "united.com": "United Airlines",
            "aa.com": "American Airlines",
            "southwest.com": "Southwest",
            "jetblue.com": "JetBlue",
            "lufthansa.com": "Lufthansa",
            "britishairways.com": "British Airways"
        }
        
        for domain, name in airline_map.items():
            if domain in url_lower:
                return name
        
        # Check hotel/travel sites
        platform_map = {
            "booking.com": "Booking.com",
            "hotels.com": "Hotels.com",
            "expedia.com": "Expedia",
            "agoda.com": "Agoda",
            "kayak.com": "Kayak",
            "priceline.com": "Priceline",
            "marriott.com": "Marriott",
            "hilton.com": "Hilton",
            "google.com/flights": "Google Flights"
        }
        
        for domain, name in platform_map.items():
            if domain in url_lower:
                return name
        
        return "Unknown"
    
    def _calculate_confidence(self, result: Dict, flight_data: Dict) -> str:
        """Calculate confidence level for a flight booking link."""
        url = result.get("url", "").lower()
        title = result.get("title", "").lower()
        
        flight_number = flight_data.get("flight_number", "").lower()
        airline = flight_data.get("airline", "").lower()
        
        # High confidence if flight number is in URL or title
        if flight_number in url or flight_number in title:
            return "high"
        
        # Medium confidence if it's the airline's website
        if airline in url and any(term in url for term in ["booking", "flights", "reservations"]):
            return "medium"
        
        return "low"
    
    def _deduplicate_hotel_links(self, links: List[Dict]) -> List[Dict]:
        """Remove duplicate hotel links, keeping highest confidence."""
        platform_links = {}
        
        for link in links:
            platform = link["platform"]
            if platform not in platform_links:
                platform_links[platform] = link
            else:
                # Keep the one with higher confidence
                existing = platform_links[platform]
                if link.get("confidence", "low") > existing.get("confidence", "low"):
                    platform_links[platform] = link
        
        return list(platform_links.values())
    
    def _generate_flight_search_links(self, flight_data: Dict) -> List[Dict]:
        """Generate fallback search links for flights."""
        origin = flight_data.get("origin", "")
        dest = flight_data.get("destination", "")
        depart_date = flight_data.get("departure_date", "")
        return_date = flight_data.get("return_date", "")
        
        return [
            {
                "platform": "Google Flights",
                "url": f"https://www.google.com/flights/#search;f={origin};t={dest};d={depart_date};r={return_date}",
                "type": "search"
            },
            {
                "platform": "Kayak",
                "url": f"https://www.kayak.com/flights/{origin}-{dest}/{depart_date}/{return_date}",
                "type": "search"
            },
            {
                "platform": "Expedia",
                "url": f"https://www.expedia.com/Flights-Search?trip=roundtrip&leg1=from:{origin},to:{dest},departure:{depart_date}&leg2=from:{dest},to:{origin},departure:{return_date}",
                "type": "search"
            }
        ]
    
    def _generate_hotel_search_links(self, hotel_data: Dict) -> List[Dict]:
        """Generate fallback search links for hotels."""
        city = hotel_data.get("city", "")
        check_in = hotel_data.get("check_in", "")
        check_out = hotel_data.get("check_out", "")
        
        # URL encode city name
        city_encoded = city.replace(" ", "+")
        
        return [
            {
                "platform": "Booking.com",
                "url": f"https://www.booking.com/search.html?ss={city_encoded}&checkin={check_in}&checkout={check_out}",
                "type": "search"
            },
            {
                "platform": "Hotels.com",
                "url": f"https://www.hotels.com/search.do?destination-id=&q-destination={city_encoded}&q-check-in={check_in}&q-check-out={check_out}",
                "type": "search"
            },
            {
                "platform": "Expedia",
                "url": f"https://www.expedia.com/Hotel-Search?destination={city_encoded}&startDate={check_in}&endDate={check_out}",
                "type": "search"
            }
        ]