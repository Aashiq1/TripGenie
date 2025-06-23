# app/services/activities_search.py
"""Service for searching activities and extracting booking links."""

from typing import List, Dict, Optional
import re
from app.services.tavily_client import TavilyClient

class ActivitySearchService:
    """Search for activities and track booking links."""
    
    # Known booking platforms for activities
    ACTIVITY_BOOKING_DOMAINS = [
        "viator.com",
        "getyourguide.com",
        "tripadvisor.com",
        "klook.com",
        "tiqets.com",
        "headout.com",
        "civitatis.com",
        "veltra.com",
        "expedia.com/things-to-do",
        "airbnb.com/experiences",
        "ticketmaster.com",
        "eventbrite.com"
    ]
    
    def __init__(self, tavily_client: Optional[TavilyClient] = None):
        self.client = tavily_client or TavilyClient()
    
    def search_activities(self,
                         destination: str,
                         interests: List[str],
                         travel_style: str,
                         num_days: int,
                         trip_pace: str = "balanced") -> Dict:
        """
        Search for activities with booking links.
        
        Returns:
            Dict with daily itinerary including booking links
        """
        all_activities = []
        
        # Search for each interest
        for interest in interests:
            activities = self._search_by_interest(destination, interest, travel_style)
            all_activities.extend(activities)
        
        # Also search for top attractions
        general_activities = self._search_top_attractions(destination, travel_style)
        all_activities.extend(general_activities)
        
        # Remove duplicates based on name
        unique_activities = self._deduplicate_activities(all_activities)
        
        # Create daily itinerary
        daily_plan = self._create_daily_itinerary(
            unique_activities,
            num_days,
            trip_pace
        )
        
        return {
            "destination": destination,
            "total_activities_found": len(unique_activities),
            "daily_itinerary": daily_plan,
            "all_bookable_links": self._extract_all_booking_links(unique_activities)
        }
    
    def _search_by_interest(self, destination: str, interest: str, travel_style: str) -> List[Dict]:
        """Search for activities based on specific interest."""
        query = f"best {interest} activities things to do in {destination} {travel_style} with booking tickets"
        
        results = self.client.search(
            query=query,
            max_results=10,
            include_domains=self.ACTIVITY_BOOKING_DOMAINS
        )
        
        if not results:
            return []
        
        activities = []
        
        # Parse search results
        for idx, result in enumerate(results.get("results", [])):
            activity = self._parse_activity_result(result, interest)
            if activity:
                activity["search_rank"] = idx + 1
                activities.append(activity)
        
        return activities
    
    def _search_top_attractions(self, destination: str, travel_style: str) -> List[Dict]:
        """Search for general top attractions."""
        query = f"top attractions must visit {destination} book tickets online"
        
        results = self.client.search(
            query=query,
            max_results=10,
            include_answer=True
        )
        
        if not results:
            return []
        
        activities = []
        
        # Parse the AI answer for quick recommendations
        if results.get("answer"):
            activities.extend(self._parse_answer_for_activities(results["answer"], destination))
        
        # Parse individual results
        for result in results.get("results", []):
            activity = self._parse_activity_result(result, "sightseeing")
            if activity:
                activities.append(activity)
        
        return activities
    
    def _parse_activity_result(self, result: Dict, interest: str) -> Optional[Dict]:
        """Parse a single search result into activity data."""
        url = result.get("url", "")
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        content = result.get("content", "")
        
        # Check if this is a booking page
        is_bookable = self._is_booking_url(url)
        platform = self._identify_platform(url) if is_bookable else None
        
        # Extract price if available
        price_info = self._extract_price(snippet + " " + content)
        
        # Extract key details
        activity_name = self._clean_activity_name(title)
        
        return {
            "name": activity_name,
            "description": snippet,
            "interest": interest,
            "url": url,
            "is_bookable": is_bookable,
            "booking_platform": platform,
            "booking_url": url if is_bookable else None,
            "price_info": price_info,
            "duration": self._estimate_duration(activity_name, content),
            "highlights": self._extract_highlights(content),
            "source": result.get("source", ""),
            "content_snippet": content[:500] if content else ""  # Store for context
        }
    
    def _is_booking_url(self, url: str) -> bool:
        """Check if URL is from a booking platform."""
        return any(domain in url.lower() for domain in self.ACTIVITY_BOOKING_DOMAINS)
    
    def _identify_platform(self, url: str) -> str:
        """Identify which booking platform the URL is from."""
        url_lower = url.lower()
        
        platform_map = {
            "viator.com": "Viator",
            "getyourguide.com": "GetYourGuide",
            "tripadvisor.com": "TripAdvisor",
            "klook.com": "Klook",
            "tiqets.com": "Tiqets",
            "headout.com": "Headout",
            "airbnb.com/experiences": "Airbnb Experiences",
            "ticketmaster": "Ticketmaster",
            "eventbrite": "Eventbrite"
        }
        
        for domain, name in platform_map.items():
            if domain in url_lower:
                return name
        
        return "Direct Booking"
    
    def _extract_price(self, text: str) -> Optional[Dict]:
        """Extract price information from text."""
        price_patterns = [
            r"(?:from\s+)?([€$£]?\d+(?:\.\d{2})?)\s*(?:USD|EUR|GBP)?\s*(?:per\s+person)?",
            r"(?:tickets?\s+from\s+)?([€$£]?\d+(?:\.\d{2})?)",
            r"(?:price|cost)s?\s*:?\s*([€$£]?\d+(?:\.\d{2})?)",
            r"([€$£]?\d+(?:\.\d{2})?)\s*(?:per\s+adult|pp|per\s+ticket)",
            r"(?:only\s+)?([€$£]?\d+(?:\.\d{2})?)\s*(?:euros?|dollars?|pounds?)",
            r"(\d+(?:\.\d{2})?)\s*(?:€|\$|£|USD|EUR|GBP)"
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1)
                
                # Determine currency
                currency = "$"  # Default to USD
                if "€" in text or "EUR" in text or "euro" in text.lower():
                    currency = "€"
                elif "£" in text or "GBP" in text or "pound" in text.lower():
                    currency = "£"
                elif price_str.startswith(("€", "$", "£")):
                    currency = price_str[0]
                    price_str = price_str[1:]
                
                try:
                    amount = float(price_str)
                    
                    # Convert to USD for budget calculations
                    usd_amount = self._convert_to_usd(amount, currency)
                    
                    return {
                        "price_string": f"{currency}{amount}",
                        "currency": currency,
                        "amount": amount,
                        "amount_usd": usd_amount,
                        "per_person": True  # Assume per person unless stated otherwise
                    }
                except ValueError:
                    continue
        
        return None
    
    def _convert_to_usd(self, amount: float, currency: str) -> float:
        """Convert price to USD for budget calculations."""
        # Simple conversion rates (in production, use real-time rates)
        conversion_rates = {
            "$": 1.0,
            "€": 1.1,  # 1 EUR = 1.10 USD
            "£": 1.27  # 1 GBP = 1.27 USD
        }
        
        rate = conversion_rates.get(currency, 1.0)
        return round(amount * rate, 2)
    
    def _estimate_duration(self, name: str, content: str) -> float:
        """Estimate activity duration in hours."""
        # Check content for duration mentions
        duration_patterns = [
            r"(\d+(?:\.\d+)?)\s*hours?",
            r"(\d+)h\s*(\d+)?m?",
            r"duration:\s*(\d+(?:\.\d+)?)\s*hours?"
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, content.lower())
            if match:
                hours = float(match.group(1))
                if match.groups() and len(match.groups()) > 1 and match.group(2):
                    hours += float(match.group(2)) / 60
                return min(hours, 12)  # Cap at 12 hours
        
        # Default estimates based on activity type
        name_lower = name.lower()
        if any(word in name_lower for word in ["tour", "excursion", "day trip"]):
            return 4.0
        elif any(word in name_lower for word in ["museum", "gallery", "exhibition"]):
            return 2.5
        elif any(word in name_lower for word in ["show", "performance", "concert"]):
            return 2.0
        elif any(word in name_lower for word in ["class", "workshop", "lesson"]):
            return 3.0
        else:
            return 2.0
    
    def _extract_highlights(self, content: str) -> List[str]:
        """Extract key highlights from content."""
        highlights = []
        
        # Look for bullet points or lists
        list_patterns = [
            r"•\s*(.+?)(?=•|\n|$)",
            r"-\s*(.+?)(?=-|\n|$)",
            r"\d+\.\s*(.+?)(?=\d+\.|\n|$)"
        ]
        
        for pattern in list_patterns:
            matches = re.findall(pattern, content)
            highlights.extend([match.strip() for match in matches[:3]])
        
        return highlights[:5]  # Max 5 highlights
    
    def _clean_activity_name(self, title: str) -> str:
        """Clean up activity name from title."""
        # Remove common suffixes
        suffixes = [
            " - Book Online",
            " | Book Now",
            " - Tickets",
            " | GetYourGuide",
            " | Viator",
            " - TripAdvisor"
        ]
        
        clean_name = title
        for suffix in suffixes:
            clean_name = clean_name.replace(suffix, "")
        
        return clean_name.strip()
    
    def _parse_answer_for_activities(self, answer: str, destination: str) -> List[Dict]:
        """Parse AI answer for activity mentions."""
        activities = []
        
        # Look for numbered lists or bullet points
        lines = answer.split('\n')
        for line in lines:
            # Check if line mentions an activity
            if any(word in line.lower() for word in ['visit', 'explore', 'tour', 'see', 'experience']):
                activity_name = self._extract_activity_name_from_line(line)
                if activity_name:
                    activities.append({
                        "name": activity_name,
                        "description": f"Recommended attraction in {destination}",
                        "interest": "top_picks",
                        "url": None,
                        "is_bookable": False,
                        "booking_platform": None,
                        "booking_url": None,
                        "from_ai_summary": True
                    })
        
        return activities
    
    def _extract_activity_name_from_line(self, line: str) -> Optional[str]:
        """Extract activity name from a text line."""
        # Remove list markers
        line = re.sub(r'^[\d\-\*\•\.]+\s*', '', line)
        
        # Look for patterns like "Visit the..." or "Explore..."
        patterns = [
            r"(?:visit|explore|tour|see)\s+(?:the\s+)?([A-Z][^,\.\n]+)",
            r"^([A-Z][^:,\.\n]+?)(?:\s*[-–]\s*|\s*:\s*)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no pattern matches but line seems like activity name
        if len(line) < 100 and line[0].isupper():
            return line.split('-')[0].split(':')[0].strip()
        
        return None
    
    def _deduplicate_activities(self, activities: List[Dict]) -> List[Dict]:
        """Remove duplicate activities based on name similarity."""
        unique = []
        seen_names = set()
        
        for activity in activities:
            name_lower = activity["name"].lower()
            
            # Check for similar names
            is_duplicate = False
            for seen in seen_names:
                if self._are_names_similar(name_lower, seen):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(activity)
                seen_names.add(name_lower)
        
        return unique
    
    def _are_names_similar(self, name1: str, name2: str) -> bool:
        """Check if two activity names are similar."""
        # Simple similarity check - can be made more sophisticated
        if name1 == name2:
            return True
        
        # Check if one contains the other
        if name1 in name2 or name2 in name1:
            return True
        
        # Check if they share key words
        words1 = set(name1.split())
        words2 = set(name2.split())
        common_words = words1.intersection(words2)
        
        # If they share more than 50% of words
        if len(common_words) > max(len(words1), len(words2)) * 0.5:
            return True
        
        return False
    
    def _create_daily_itinerary(self, activities: List[Dict], num_days: int, trip_pace: str) -> Dict:
        """Create daily itinerary from activities with budget tracking."""
        activities_per_day = {
            "chill": 2,
            "balanced": 3,
            "fast": 4
        }.get(trip_pace, 3)
        
        # Prioritize bookable activities with prices
        activities_with_prices = [a for a in activities if a.get("price_info")]
        activities_without_prices = [a for a in activities if not a.get("price_info")]
        bookable_no_price = [a for a in activities_without_prices if a["is_bookable"]]
        non_bookable = [a for a in activities_without_prices if not a["is_bookable"]]
        
        # Sort by priority: priced activities first, then bookable, then others
        sorted_activities = activities_with_prices + bookable_no_price + non_bookable
        
        daily_plan = {}
        total_trip_cost_usd = 0
        
        for day in range(1, num_days + 1):
            start_idx = (day - 1) * activities_per_day
            end_idx = start_idx + activities_per_day
            
            day_activities = sorted_activities[start_idx:end_idx]
            day_cost_usd = 0
            
            # Calculate daily cost
            for activity in day_activities:
                if activity.get("price_info"):
                    day_cost_usd += activity["price_info"].get("amount_usd", 0)
            
            total_trip_cost_usd += day_cost_usd
            
            if day_activities:
                daily_plan[f"day_{day}"] = {
                    "date": f"Day {day}",
                    "activities": day_activities,
                    "total_duration": sum(a.get("duration", 2) for a in day_activities),
                    "bookable_count": sum(1 for a in day_activities if a["is_bookable"]),
                    "day_cost_usd": day_cost_usd,
                    "day_cost_summary": self._format_cost_summary(day_activities)
                }
        
        # Add total cost summary
        daily_plan["trip_totals"] = {
            "total_activity_cost_usd": total_trip_cost_usd,
            "average_per_day": total_trip_cost_usd / num_days if num_days > 0 else 0,
            "cost_breakdown": self._create_cost_breakdown(sorted_activities[:num_days * activities_per_day])
        }
        
        return daily_plan
    
    def _format_cost_summary(self, activities: List[Dict]) -> Dict:
        """Create a cost summary for a day's activities."""
        total_usd = 0
        priced_activities = 0
        
        for activity in activities:
            if activity.get("price_info"):
                total_usd += activity["price_info"].get("amount_usd", 0)
                priced_activities += 1
        
        return {
            "total_usd": total_usd,
            "priced_activities": priced_activities,
            "unpriced_activities": len(activities) - priced_activities,
            "note": f"Estimated additional costs for {len(activities) - priced_activities} activities without prices"
        }
    
    def _create_cost_breakdown(self, activities: List[Dict]) -> Dict:
        """Create detailed cost breakdown by category."""
        breakdown = {}
        
        for activity in activities:
            category = activity.get("interest", "general")
            if category not in breakdown:
                breakdown[category] = {
                    "count": 0,
                    "total_usd": 0,
                    "activities": []
                }
            
            breakdown[category]["count"] += 1
            
            if activity.get("price_info"):
                price_usd = activity["price_info"].get("amount_usd", 0)
                breakdown[category]["total_usd"] += price_usd
                breakdown[category]["activities"].append({
                    "name": activity["name"],
                    "price": activity["price_info"]["price_string"],
                    "price_usd": price_usd
                })
        
        return breakdown
    
    def _extract_all_booking_links(self, activities: List[Dict]) -> List[Dict]:
        """Extract all booking links from activities."""
        booking_links = []
        
        for activity in activities:
            if activity.get("is_bookable") and activity.get("booking_url"):
                booking_links.append({
                    "activity": activity["name"],
                    "platform": activity["booking_platform"],
                    "url": activity["booking_url"],
                    "price_info": activity.get("price_info")
                })
        
        return booking_links