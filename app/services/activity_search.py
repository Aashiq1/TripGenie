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
    
    # Interest-specific activity types for more targeted searching
    INTEREST_ACTIVITY_MAP = {
        "food": [
            "food tour", "cooking class", "wine tasting", "tapas tour", 
            "culinary experience", "market tour", "restaurant experience", "michelin restaurant"
        ],
        "culture": [
            "museum ticket", "art gallery", "historical tour", "cultural center",
            "heritage site", "monument tour", "archaeological site"
        ],
        "adventure": [
            "hiking tour", "bike tour", "kayaking", "climbing", "zip line",
            "outdoor adventure", "extreme sports", "adventure park"
        ],
        "nightlife": [
            "nightclub entry", "pub crawl", "rooftop bar", "live music venue",
            "cocktail bar", "VIP club access", "bar hopping tour", "nightlife experience"
        ],
        "party": [
            "club tickets", "nightclub booking", "party boat", "beach club",
            "VIP nightlife", "exclusive club", "party package", "nightlife tour"
        ],
        "relaxing": [
            "spa treatment", "wellness center", "beach access", "park visit",
            "thermal baths", "massage", "meditation class"
        ],
        "shopping": [
            "shopping tour", "market visit", "boutique experience", 
            "artisan workshop", "souvenir hunting", "fashion district tour"
        ],
        "art": [
            "art museum", "gallery tour", "street art tour", "art workshop",
            "painting class", "sculpture garden", "contemporary art"
        ],
        "history": [
            "historical tour", "castle visit", "palace tour", "archaeological site",
            "heritage walk", "museum", "historical monument"
        ],
        "architecture": [
            "architecture tour", "building tour", "design museum", "cathedral visit",
            "architectural walk", "landmark tour", "city skyline"
        ]
    }
    
    # Day-specific search strategies
    DAY_SPECIFIC_QUERIES = {
        "nightlife": {
            "friday": [
                "best bars {destination} friday night",
                "pub crawl {destination} friday booking",
                "rooftop bars {destination} reservations",
                "cocktail bars {destination} tickets"
            ],
            "saturday": [
                "best clubs {destination} saturday night",
                "nightclub {destination} VIP tickets",
                "exclusive clubs {destination} booking",
                "club entry {destination} saturday"
            ],
            "weekday": [
                "live music {destination} tickets",
                "jazz clubs {destination} booking",
                "wine bars {destination} reservations",
                "cocktail experience {destination}"
            ]
        },
        "party": {
            "friday": [
                "party {destination} friday night tickets",
                "club crawl {destination} booking",
                "nightlife tour {destination} friday"
            ],
            "saturday": [
                "best nightclubs {destination} saturday",
                "VIP club experience {destination}",
                "exclusive party {destination} tickets"
            ],
            "weekday": [
                "party boat {destination} tickets",
                "rooftop party {destination}",
                "beach club {destination} booking"
            ]
        },
        "food": {
            "evening": [
                "fine dining {destination} reservations",
                "michelin restaurants {destination} booking",
                "chef table experience {destination}",
                "tasting menu {destination} tickets"
            ],
            "daytime": [
                "food tour {destination} small group",
                "cooking class {destination} hands on",
                "market tour {destination} tasting",
                "culinary workshop {destination} booking"
            ]
        }
    }

    def __init__(self, tavily_client: Optional[TavilyClient] = None):
        self.client = tavily_client or TavilyClient()
    
    def search_activities(self,
                         destination: str,
                         interests: List[str],
                         travel_style: str,
                         num_days: int,
                         trip_pace: str = "balanced",
                         departure_date: str = None) -> Dict:
        """
        Search for activities with booking links using smart day-specific strategies.
        
        Returns:
            Dict with daily itinerary including booking links
        """
        all_activities = []
        
        # Analyze trip timing for day-of-week awareness
        trip_context = self._analyze_trip_context(departure_date, num_days, interests)
        
        # Search for activities using enhanced strategies
        for interest in interests:
            activities = self._search_smart_activities(destination, interest, travel_style, trip_context)
            all_activities.extend(activities)
        
        # Also search for must-see attractions with tickets
        must_see_activities = self._search_must_see_attractions(destination, travel_style)
        all_activities.extend(must_see_activities)
        
        # Remove duplicates and filter out non-activities
        unique_activities = self._filter_and_deduplicate_activities(all_activities)
        
        # Create daily itinerary with smart day assignment
        daily_plan = self._create_smart_daily_itinerary(
            unique_activities,
            num_days,
            trip_pace,
            trip_context
        )
        
        return {
            "destination": destination,
            "total_activities_found": len(unique_activities),
            "daily_itinerary": daily_plan,
            "all_bookable_links": self._extract_all_booking_links(unique_activities),
            "trip_context": trip_context
        }
    
    def _analyze_trip_context(self, departure_date: str, num_days: int, interests: List[str]) -> Dict:
        """Analyze trip timing and interests for smart activity assignment."""
        from datetime import datetime, timedelta
        
        context = {
            "has_nightlife": any(interest in ["nightlife", "party"] for interest in interests),
            "has_food": "food" in interests,
            "has_culture": "culture" in interests or "art" in interests,
            "weekend_days": [],
            "weekday_evenings": [],
            "day_mapping": {}
        }
        
        if departure_date:
            try:
                start_date = datetime.strptime(departure_date, "%Y-%m-%d")
                for day in range(num_days):
                    current_date = start_date + timedelta(days=day)
                    day_num = day + 1
                    weekday = current_date.strftime("%A").lower()
                    
                    context["day_mapping"][day_num] = {
                        "weekday": weekday,
                        "is_weekend": weekday in ["friday", "saturday"],
                        "is_friday": weekday == "friday",
                        "is_saturday": weekday == "saturday"
                    }
                    
                    if weekday in ["friday", "saturday"]:
                        context["weekend_days"].append(day_num)
                    else:
                        context["weekday_evenings"].append(day_num)
                        
            except ValueError:
                # If date parsing fails, use default logic
                context["weekend_days"] = [day for day in range(1, num_days + 1) if day % 7 in [5, 6]]
        
        return context
    
    def _search_smart_activities(self, destination: str, interest: str, travel_style: str, trip_context: Dict) -> List[Dict]:
        """Search for activities using smart, context-aware queries."""
        activities = []
        
        # Get base activity types
        activity_types = self.INTEREST_ACTIVITY_MAP.get(interest, [interest])
        
        # Use day-specific queries for nightlife/party interests
        if interest in ["nightlife", "party"] and trip_context["has_nightlife"]:
            weekend_days = trip_context.get("weekend_days", [])
            
            if weekend_days:
                # Use weekend-specific queries
                day_type = "saturday" if any(trip_context["day_mapping"].get(day, {}).get("is_saturday") for day in weekend_days) else "friday"
                queries = self.DAY_SPECIFIC_QUERIES[interest][day_type]
            else:
                # Use weekday queries
                queries = self.DAY_SPECIFIC_QUERIES[interest]["weekday"]
            
            # Format queries with destination
            formatted_queries = [q.format(destination=destination) for q in queries]
            
        elif interest == "food" and trip_context["has_food"]:
            # Mix of evening dining and daytime food experiences
            evening_queries = [q.format(destination=destination) for q in self.DAY_SPECIFIC_QUERIES["food"]["evening"]]
            daytime_queries = [q.format(destination=destination) for q in self.DAY_SPECIFIC_QUERIES["food"]["daytime"]]
            formatted_queries = evening_queries[:2] + daytime_queries[:2]  # Mix both
            
        else:
            # Use enhanced generic queries
            formatted_queries = []
            for activity_type in activity_types[:3]:
                formatted_queries.extend([
                    f"best {activity_type} {destination} tickets booking",
                    f"{activity_type} {destination} skip the line",
                    f"top {activity_type} {destination} advance booking"
                ])
        
        # Execute searches
        for query in formatted_queries[:5]:  # Limit to 5 queries per interest
            results = self.client.search(
                query=query,
                max_results=5,
                include_domains=self.ACTIVITY_BOOKING_DOMAINS
            )
            
            if results and results.get("results"):
                for result in results["results"]:
                    activity = self._parse_specific_activity(result, interest, activity_types[0])
                    if activity and self._is_valid_activity(activity):
                        # Add context for smart day assignment
                        activity["preferred_days"] = self._get_preferred_days(interest, trip_context)
                        activities.append(activity)
            
            # Don't overwhelm with too many requests
            if len(activities) >= 12:  # Slightly reduce to make room for quality
                break
        
        return activities
    
    def _get_preferred_days(self, interest: str, trip_context: Dict) -> List[str]:
        """Get preferred days for specific activity types."""
        if interest in ["nightlife", "party"]:
            weekend_days = trip_context.get("weekend_days", [])
            return ["weekend"] if weekend_days else ["evening"]
        elif interest == "food":
            return ["evening", "daytime"]
        elif interest in ["culture", "art", "history"]:
            return ["daytime"]
        else:
            return ["any"]
    
    def _search_specific_activities(self, destination: str, interest: str, travel_style: str) -> List[Dict]:
        """Search for specific bookable activities based on interest."""
        activities = []
        
        # Get specific activity types for this interest
        activity_types = self.INTEREST_ACTIVITY_MAP.get(interest, [interest])
        
        for activity_type in activity_types[:3]:  # Limit to 3 most relevant types per interest
            # Create targeted search queries
            queries = [
                f"{activity_type} {destination} book tickets online",
                f"{activity_type} {destination} viator getyourguide",
                f"book {activity_type} {destination} tickets price"
            ]
            
            for query in queries:
                results = self.client.search(
                    query=query,
                    max_results=5,
                    include_domains=self.ACTIVITY_BOOKING_DOMAINS
                )
                
                if results and results.get("results"):
                    for result in results["results"]:
                        activity = self._parse_specific_activity(result, interest, activity_type)
                        if activity and self._is_valid_activity(activity):
                            activities.append(activity)
                
                # Don't overwhelm with too many requests
                if len(activities) >= 15:  # Reasonable limit per interest
                    break
            
            if len(activities) >= 15:
                break
        
        return activities
    
    def _search_must_see_attractions(self, destination: str, travel_style: str) -> List[Dict]:
        """Search for specific must-see attractions with booking options."""
        queries = [
            f"{destination} famous attractions tickets book online",
            f"{destination} main sights entry tickets viator",
            f"skip the line tickets {destination} attractions"
        ]
        
        activities = []
        
        for query in queries:
            results = self.client.search(
                query=query,
                max_results=8,
                include_domains=self.ACTIVITY_BOOKING_DOMAINS
            )
            
            if results and results.get("results"):
                for result in results["results"]:
                    activity = self._parse_specific_activity(result, "sightseeing", "attraction")
                    if activity and self._is_valid_activity(activity):
                        activities.append(activity)
        
        return activities
    
    def _extract_price(self, text: str) -> Optional[Dict]:
        """Extract price information from text with enhanced validation."""
        
        # Enhanced price patterns that are more likely to be actual prices
        price_patterns = [
            # Pattern: "from $25" or "starting at €20"
            r"(?:from|starting\s+at|starting\s+from|prices?\s+from)\s*([€$£])(\d{1,3}(?:\.\d{2})?)",
            
            # Pattern: "€15 per person" or "$30/person"  
            r"([€$£])(\d{1,3}(?:\.\d{2})?)\s*(?:/|\s+per)\s*(?:person|adult|pp|guest)",
            
            # Pattern: "Admission: $15" or "Entry: €20"
            r"(?:admission|entry|ticket|price|cost):\s*([€$£])(\d{1,3}(?:\.\d{2})?)",
            
            # Pattern: "Book for $25" or "Reserve for €30"
            r"(?:book|reserve|buy|purchase)\s+for\s*([€$£])(\d{1,3}(?:\.\d{2})?)",
            
            # Pattern: "$25 tickets" or "€30 entry"
            r"([€$£])(\d{1,3}(?:\.\d{2})?)\s+(?:tickets?|entry|admission|access)",
            
            # Pattern: "Only $25" or "Just €30"
            r"(?:only|just|from)\s*([€$£])(\d{1,3}(?:\.\d{2})?)",
            
            # Pattern: "Price: $25-30" (range)
            r"(?:price|cost):\s*([€$£])(\d{1,3})-\d{1,3}",
            
            # Pattern: "$25.00" standalone with price context nearby
            r"([€$£])(\d{1,3}\.\d{2})(?=\s*(?:per|for|tickets?|admission|entry))",
            
            # Pattern: "Tickets from $25"
            r"tickets?\s+from\s*([€$£])(\d{1,3}(?:\.\d{2})?)",
            
            # Pattern: Adult prices specifically
            r"adult[s]?\s*:?\s*([€$£])(\d{1,3}(?:\.\d{2})?)"
        ]
        
        extracted_prices = []
        
        for pattern in price_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                currency_symbol = match.group(1)
                amount_str = match.group(2)
                
                try:
                    amount = float(amount_str)
                    
                    # Convert to USD (updated exchange rates)
                    if currency_symbol == "€":
                        amount_usd = amount * 1.08  # EUR to USD
                    elif currency_symbol == "£":
                        amount_usd = amount * 1.25  # GBP to USD  
                    else:  # $
                        amount_usd = amount
                    
                    # Enhanced reasonableness check - must be between $1 and $1000
                    if 1 <= amount_usd <= 1000:
                        extracted_prices.append({
                            "amount_usd": amount_usd,
                            "original_amount": amount,
                            "currency_symbol": currency_symbol,
                            "match_context": match.group(0),
                            "confidence": self._calculate_price_confidence(match.group(0), text)
                        })
                        
                except ValueError:
                    continue
        
        # If we found multiple prices, choose the most reasonable one
        if extracted_prices:
            # Sort by confidence first, then by how reasonable the price seems
            extracted_prices.sort(key=lambda x: (x["confidence"], -abs(x["amount_usd"] - 50)), reverse=True)
            
            best_price = extracted_prices[0]
            return {
                "price_string": f"${best_price['amount_usd']:.2f}",
                "amount_usd": best_price["amount_usd"],
                "currency": "USD",
                "per_person": True,
                "confidence": "high" if best_price["confidence"] > 0.7 else "medium",
                "note": "Price extracted from web content - may not be current",
                "original_match": best_price["match_context"]
            }
        
        return None
    
    def _calculate_price_confidence(self, match_context: str, full_text: str) -> float:
        """Calculate confidence score for extracted price."""
        confidence = 0.5  # Base confidence
        
        match_lower = match_context.lower()
        text_lower = full_text.lower()
        
        # Boost confidence for clear price indicators
        high_confidence_terms = ["per person", "admission", "ticket", "entry", "book for", "reserve for"]
        for term in high_confidence_terms:
            if term in match_lower:
                confidence += 0.3
                break
        
        # Boost for booking context
        booking_context = ["book", "reserve", "buy", "purchase", "tickets"]
        if any(term in text_lower for term in booking_context):
            confidence += 0.2
        
        # Reduce confidence for potential false positives
        false_positive_terms = ["phone", "address", "zip", "postal", "year", "age"]
        for term in false_positive_terms:
            if term in text_lower:
                confidence -= 0.3
                break
        
        return max(0.0, min(1.0, confidence))
    
    def _validate_price_for_activity_type(self, price_usd: float, activity_type: str) -> bool:
        """Validate if a price is reasonable for the activity type."""
        
        REALISTIC_RANGES = {
            "museum": (5, 100),
            "gallery": (5, 40), 
            "food_tour": (25, 150),
            "cooking_class": (40, 200),
            "wine_tasting": (30, 120),
            "walking_tour": (15, 80),
            "bike_tour": (20, 100),
            "boat_tour": (25, 150),
            "hiking_tour": (30, 120),
            "day_trip": (50, 500),
            "show": (20, 200),
            "concert": (30, 300),
            "attraction": (10, 80),
            "experience": (20, 150),
        }
        
        # Find the most specific matching category
        for category, (min_price, max_price) in REALISTIC_RANGES.items():
            if category in activity_type.lower():
                return min_price <= price_usd <= max_price
        
        # Default range if no specific category matches
        return 5 <= price_usd <= 200
    
    def _parse_specific_activity(self, result: Dict, interest: str, activity_type: str) -> Optional[Dict]:
        """Parse a search result into specific activity data, filtering out guides."""
        url = result.get("url", "")
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        content = result.get("content", "")
        
        # Skip if this looks like a generic guide or article
        if self._is_generic_guide(title, url):
            return None
        
        # Check if this is a booking page
        is_bookable = self._is_booking_url(url)
        platform = self._identify_platform(url) if is_bookable else None
        
        # Extract and clean activity name first
        activity_name = self._extract_specific_activity_name(title, activity_type)
        
        if not activity_name or len(activity_name) < 5:
            return None
        
        # Extract price with validation
        price_info = self._extract_price(snippet + " " + content)
        
        # Validate price against activity type if extracted
        if price_info and not self._validate_price_for_activity_type(
            price_info["amount_usd"], activity_type
        ):
            # Price seems unrealistic for this activity type - remove it
            price_info = None
        
        return {
            "name": activity_name,
            "description": self._create_activity_description(snippet, activity_type),
            "interest": interest,
            "activity_type": activity_type,
            "url": url,
            "is_bookable": is_bookable,
            "booking_platform": platform,
            "booking_url": url if is_bookable else None,
            "price_info": price_info,
            "duration": self._estimate_activity_duration(activity_name, content, activity_type),
            "highlights": self._extract_highlights(content),
            "source": result.get("source", ""),
            "search_relevance": self._calculate_relevance_score(title, snippet, activity_type),
            "price_note": "Prices shown are estimates from web search - click booking link for current pricing" if price_info else "Price available on booking platform"
        }
    
    def _is_generic_guide(self, title: str, url: str) -> bool:
        """Check if this is a generic guide rather than a specific activity."""
        title_lower = title.lower()
        
        # Patterns that indicate generic guides
        guide_patterns = [
            r"top \d+ things to do",
            r"best things to do",
            r"\d+ must visit",
            r"ultimate guide",
            r"travel guide",
            r"things you should know",
            r"planning your trip",
            r"itinerary",
            r"where to stay",
            r"how to",
            r"tips for",
            r"guide to"
        ]
        
        for pattern in guide_patterns:
            if re.search(pattern, title_lower):
                return True
        
        # Check for blog-like URLs
        blog_indicators = ["blog", "article", "/guide/", "/tips/", "/planning/"]
        if any(indicator in url.lower() for indicator in blog_indicators):
            return True
        
        return False
    
    def _extract_specific_activity_name(self, title: str, activity_type: str) -> str:
        """Extract specific activity name from title."""
        # Remove common booking platform suffixes
        suffixes = [
            " - Book Online", " | Book Now", " - Tickets", " | GetYourGuide",
            " | Viator", " - TripAdvisor", " - Klook", " | Headout",
            " - Book with Confidence", " | Book Today", " - Reserve Now",
            " | Book Tickets Online", " - Tiqets", " & Tours", " Tours & Tickets",
            " - Book Tickets & Tours"
        ]
        
        clean_name = title
        for suffix in suffixes:
            clean_name = clean_name.replace(suffix, "")
        
        # Remove generic prefixes
        prefixes = [
            "Book ", "Reserve ", "Buy Tickets for ", "Skip the Line: ",
            "Private ", "Small Group ", "Half Day ", "Full Day ",
            "Tickets to ", "Entry to "
        ]
        
        for prefix in prefixes:
            if clean_name.startswith(prefix):
                clean_name = clean_name[len(prefix):]
        
        # Clean up any trailing/leading punctuation
        clean_name = clean_name.strip(' -|•')
        
        # If it still looks like a guide title, try to extract activity name
        if any(word in clean_name.lower() for word in ["top", "best", "things to do", "guide"]):
            return ""  # Reject guide-like titles
        
        return clean_name.strip()
    
    def _create_activity_description(self, snippet: str, activity_type: str) -> str:
        """Create a concise activity description."""
        if not snippet:
            return f"Experience {activity_type}"
        
        # Take first sentence or up to 150 characters
        first_sentence = snippet.split('.')[0]
        if len(first_sentence) > 150:
            return snippet[:150] + "..."
        
        return first_sentence + "." if not first_sentence.endswith('.') else first_sentence
    
    def _estimate_activity_duration(self, activity_name: str, content: str, activity_type: str) -> float:
        """Estimate activity duration based on type and content."""
        name_lower = activity_name.lower()
        content_lower = content.lower()
        
        # Look for explicit duration in content
        duration_patterns = [
            r"(\d+(?:\.\d+)?)\s*hours?",
            r"(\d+)\s*h\b",
            r"duration:?\s*(\d+(?:\.\d+)?)\s*hours?",
            r"lasts?\s*(\d+(?:\.\d+)?)\s*hours?"
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, content_lower)
            if match:
                return float(match.group(1))
        
        # Default durations by activity type
        duration_defaults = {
            "food tour": 3.0,
            "cooking class": 4.0,
            "wine tasting": 2.0,
            "museum": 2.5,
            "walking tour": 3.0,
            "bike tour": 4.0,
            "boat tour": 2.0,
            "day trip": 8.0,
            "half day": 4.0,
            "full day": 8.0,
            "evening": 4.0,
            "workshop": 3.0,
            "class": 2.5,
            "show": 2.0,
            "concert": 3.0
        }
        
        for activity_key, duration in duration_defaults.items():
            if activity_key in name_lower or activity_key in activity_type.lower():
                return duration
        
        # General defaults
        if "tour" in name_lower:
            return 3.0
        elif "class" in name_lower or "workshop" in name_lower:
            return 2.5
        elif "experience" in name_lower:
            return 2.0
        else:
            return 2.0
    
    def _calculate_relevance_score(self, title: str, snippet: str, activity_type: str) -> float:
        """Calculate relevance score for activity ranking."""
        score = 0.0
        
        text = (title + " " + snippet).lower()
        activity_type_lower = activity_type.lower()
        
        # Boost if activity type appears in title/snippet
        if activity_type_lower in text:
            score += 3.0
        
        # Boost for booking-related terms
        booking_terms = ["book", "tickets", "reserve", "buy", "online booking"]
        for term in booking_terms:
            if term in text:
                score += 1.0
        
        # Boost for experience-related terms
        experience_terms = ["experience", "tour", "visit", "explore", "discover"]
        for term in experience_terms:
            if term in text:
                score += 0.5
        
        # Penalty for guide-like terms
        guide_terms = ["guide", "tips", "how to", "best", "top"]
        for term in guide_terms:
            if term in text:
                score -= 2.0
        
        return max(0.0, score)
    
    def _is_valid_activity(self, activity: Dict) -> bool:
        """Check if this is a valid, specific activity."""
        name = activity.get("name", "").lower()
        
        # Must have a reasonable name length
        if len(name) < 5 or len(name) > 200:
            return False
        
        # Reject if it contains guide-like terms
        invalid_terms = ["top things", "best things", "guide to", "how to", "tips for", "itinerary"]
        if any(term in name for term in invalid_terms):
            return False
        
        # Reject if relevance score is too low
        if activity.get("search_relevance", 0) < 0:
            return False
        
        return True
    
    def _filter_and_deduplicate_activities(self, activities: List[Dict]) -> List[Dict]:
        """Filter out invalid activities and remove duplicates."""
        # Filter valid activities
        valid_activities = [a for a in activities if self._is_valid_activity(a)]
        
        # Sort by relevance score and whether it's bookable
        valid_activities.sort(key=lambda x: (
            x.get("is_bookable", False),
            x.get("search_relevance", 0),
            x.get("price_info") is not None
        ), reverse=True)
        
        # Remove duplicates based on name similarity
        unique = []
        seen_names = set()
        
        for activity in valid_activities:
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
        
        return unique[:30]  # Limit to top 30 activities
    
    def _is_booking_url(self, url: str) -> bool:
        """Enhanced check if this is a booking page."""
        url_lower = url.lower()
        
        # Primary booking platforms
        primary_platforms = [
            "viator.com", "getyourguide.com", "tripadvisor.com", 
            "klook.com", "tiqets.com", "headout.com", "civitatis.com",
            "veltra.com", "airbnb.com/experiences", "expedia.com/things-to-do"
        ]
        
        # Check for primary platforms
        for platform in primary_platforms:
            if platform in url_lower:
                return True
        
        # Check for booking indicators in URL
        booking_indicators = [
            "/book", "/tickets", "/reserve", "/buy", "/purchase",
            "/experiences", "/tours", "/activities", "/attractions"
        ]
        
        return any(indicator in url_lower for indicator in booking_indicators)
    
    def _identify_platform(self, url: str) -> str:
        """Enhanced platform identification with better accuracy."""
        url_lower = url.lower()
        
        platform_map = {
            "viator.com": "Viator",
            "getyourguide.com": "GetYourGuide", 
            "tripadvisor.com": "TripAdvisor",
            "klook.com": "Klook",
            "tiqets.com": "Tiqets",
            "headout.com": "Headout",
            "civitatis.com": "Civitatis",
            "veltra.com": "Veltra",
            "airbnb.com": "Airbnb Experiences",
            "expedia.com": "Expedia",
            "ticketmaster.com": "Ticketmaster",
            "eventbrite.com": "Eventbrite",
            "bookingcom": "Booking.com",
            "hotels.com": "Hotels.com"
        }
        
        for domain, platform_name in platform_map.items():
            if domain in url_lower:
                return platform_name
        
        return "Direct Booking"
    
    def _extract_highlights(self, content: str) -> List[str]:
        """Extract activity highlights from content."""
        if not content:
            return []
        
        highlights = []
        
        # Look for bullet points or lists
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                highlight = line[1:].strip()
                if len(highlight) > 10 and len(highlight) < 100:
                    highlights.append(highlight)
        
        # If no bullet points, look for sentences with key terms
        if not highlights:
            sentences = content.split('.')
            key_terms = ['includes', 'features', 'experience', 'enjoy', 'discover', 'explore']
            
            for sentence in sentences[:5]:  # Check first 5 sentences
                sentence = sentence.strip()
                if any(term in sentence.lower() for term in key_terms) and len(sentence) > 15:
                    highlights.append(sentence)
        
        return highlights[:3]  # Return top 3 highlights
    
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
        
        # If they share more than 60% of words (stricter than before)
        if len(common_words) > max(len(words1), len(words2)) * 0.6:
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
    
    def _create_smart_daily_itinerary(self, activities: List[Dict], num_days: int, trip_pace: str, trip_context: Dict) -> Dict:
        """Create daily itinerary from activities with smart day assignment."""
        daily_plan = {}
        total_trip_cost_usd = 0
        
        # Determine activities per day
        activities_per_day = {
            "chill": 2,
            "balanced": 3,
            "fast": 4
        }.get(trip_pace, 3)
        
        # Prioritize bookable activities with prices first
        activities_with_prices = [a for a in activities if a.get("price_info")]
        activities_without_prices = [a for a in activities if not a.get("price_info")]
        bookable_no_price = [a for a in activities_without_prices if a["is_bookable"]]
        non_bookable = [a for a in activities_without_prices if not a["is_bookable"]]
        
        # Sort by priority: priced activities first, then bookable, then others
        all_sorted_activities = activities_with_prices + bookable_no_price + non_bookable
        
        # Smart day assignment based on activity types and trip context
        day_assignments = {}
        used_activities = set()
        
        # Initialize all days
        for day in range(1, num_days + 1):
            day_assignments[day] = []
        
        # First pass: Assign activities with strong day preferences
        for activity in all_sorted_activities:
            if id(activity) in used_activities:
                continue
                
            interest = activity.get("interest", "")
            preferred_days = activity.get("preferred_days", ["any"])
            
            # Handle nightlife/party activities - assign to weekend nights
            if interest in ["nightlife", "party"] and trip_context.get("has_nightlife"):
                weekend_days = trip_context.get("weekend_days", [])
                
                if weekend_days:
                    # Prefer Saturday over Friday for clubs
                    saturday_days = [day for day in weekend_days 
                                   if trip_context["day_mapping"].get(day, {}).get("is_saturday")]
                    friday_days = [day for day in weekend_days 
                                 if trip_context["day_mapping"].get(day, {}).get("is_friday")]
                    
                    target_days = saturday_days if saturday_days else friday_days
                    
                    # Find a weekend day with space
                    for day in target_days:
                        if len(day_assignments[day]) < activities_per_day:
                            day_assignments[day].append(activity)
                            used_activities.add(id(activity))
                            break
            
            # Handle fine dining - assign to evening days
            elif interest == "food" and "fine dining" in activity.get("name", "").lower():
                # Look for days that could use an evening activity
                for day in range(1, num_days + 1):
                    if len(day_assignments[day]) < activities_per_day:
                        day_assignments[day].append(activity)
                        used_activities.add(id(activity))
                        break
        
        # Second pass: Fill remaining spots with other activities
        remaining_activities = [a for a in all_sorted_activities if id(a) not in used_activities]
        activity_index = 0
        
        for day in range(1, num_days + 1):
            while len(day_assignments[day]) < activities_per_day and activity_index < len(remaining_activities):
                day_assignments[day].append(remaining_activities[activity_index])
                used_activities.add(id(remaining_activities[activity_index]))
                activity_index += 1
        
        # Build the final daily plan structure
        for day in range(1, num_days + 1):
            day_activities = day_assignments[day]
            day_cost_usd = 0
            
            # Calculate daily cost
            for activity in day_activities:
                if activity.get("price_info"):
                    day_cost_usd += activity["price_info"].get("amount_usd", 0)
            
            total_trip_cost_usd += day_cost_usd
            
            # Get day context for display
            day_info = trip_context.get("day_mapping", {}).get(day, {})
            weekday = day_info.get("weekday", "")
            is_weekend = day_info.get("is_weekend", False)
            
            day_label = f"Day {day}"
            if weekday:
                day_label += f" ({weekday.title()})"
            if is_weekend:
                day_label += " 🌙"  # Weekend indicator
            
            if day_activities:
                daily_plan[f"day_{day}"] = {
                    "date": day_label,
                    "weekday": weekday,
                    "is_weekend": is_weekend,
                    "activities": day_activities,
                    "total_duration": sum(a.get("duration", 2) for a in day_activities),
                    "bookable_count": sum(1 for a in day_activities if a["is_bookable"]),
                    "day_cost_usd": day_cost_usd,
                    "day_cost_summary": self._format_cost_summary(day_activities),
                    "day_theme": self._determine_day_theme(day_activities, is_weekend)
                }
        
        # Add total cost summary
        daily_plan["trip_totals"] = {
            "total_activity_cost_usd": total_trip_cost_usd,
            "average_per_day": total_trip_cost_usd / num_days if num_days > 0 else 0,
            "cost_breakdown": self._create_cost_breakdown([a for day_acts in day_assignments.values() for a in day_acts]),
            "smart_assignment_used": True,
            "weekend_days": trip_context.get("weekend_days", []),
            "nightlife_optimized": trip_context.get("has_nightlife", False)
        }
        
        return daily_plan
    
    def _determine_day_theme(self, activities: List[Dict], is_weekend: bool) -> str:
        """Determine the theme of a day based on its activities."""
        if not activities:
            return "exploration"
        
        interests = [a.get("interest", "") for a in activities]
        
        if "nightlife" in interests or "party" in interests:
            return "nightlife" if is_weekend else "evening entertainment"
        elif "food" in interests and len([i for i in interests if i == "food"]) >= 2:
            return "culinary adventure"
        elif "culture" in interests or "art" in interests:
            return "cultural exploration" 
        elif "adventure" in interests:
            return "adventure day"
        else:
            return "mixed exploration"
    
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