"""
LangChain Travel Agent with Real Tools
Single agent that calls different tools for flight prices, hotel prices, etc.
"""

import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from datetime import datetime

from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI

from app.tools.amadeus_flight_tool import AmadeusFlightTool
from app.tools.amadeus_hotel_tool import HotelSearchTool
from app.tools.tavily_itinerary_tool import ItineraryTool

# Load environment variables
load_dotenv()

class TravelAgent:
    """LangChain-powered travel planning agent with real tools."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4.1",
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        # Instantiate tool wrappers
        self.flight_tool = AmadeusFlightTool()
        self.hotel_tool = HotelSearchTool()
        self.itinerary_tool = ItineraryTool()

        # Convert tools to LangChain format
        self.tools = [
            Tool(
                name=self.flight_tool.name,
                description=self.flight_tool.description,
                func=self.flight_tool._call
            ),
            Tool(
                name=self.hotel_tool.name,
                description=self.hotel_tool.description,
                func=self.hotel_tool._call
            ),
            Tool(
                name=self.itinerary_tool.name,
                description=self.itinerary_tool.description,
                func=self.itinerary_tool._call
            )
        ]

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True
        )
    async def plan_trip(self, user_preferences: Dict) -> Dict[str, Any]:    

        # Unpack variables
        top_destinations = user_preferences.get("top_destinations", [])
        departure_date = user_preferences.get("departure_date")
        return_date = user_preferences.get("return_date")
        budget = user_preferences.get("budgets", {})
        group_size = user_preferences.get("group_size", 2)
        trip_duration = user_preferences.get("trip_duration_days", 5)
        interests = user_preferences.get("interests", [])
        travel_style = user_preferences.get("travel_style", "mid-range")
        trip_pace = user_preferences.get("trip_pace", "balanced")
        trip_vision = user_preferences.get("trip_vision", "Not specified")
        custom_note = user_preferences.get("custom_trip_note", "None provided")
        
        # NEW: Get flight groups and preferences
        flight_groups = user_preferences.get("flight_groups", [])
        flight_preferences = user_preferences.get("flight_preferences", {})
        travel_class = flight_preferences.get("travel_class", "economy")
        nonstop_preferred = flight_preferences.get("nonstop_preferred", False)
        
        # Get accommodation details
        group_accommodation_style = user_preferences.get("group_accommodation_style", "standard")
        accommodation_details = user_preferences.get("accommodation_details", [])

        # Update for langchain_travel_agent.py - Enhanced prompt section

        planning_prompt = f"""
        You are an expert group travel planner. Your task is to find the best destination and create a complete trip plan for a group where people are flying from different cities and have different room preferences.

        GROUP DETAILS:
        - Size: {group_size} people
        - Dates: {departure_date} to {return_date} ({trip_duration} days)
        - Budget: ${budget['budget_min']}-${budget['budget_max']} per person (TOTAL including flights, hotel, activities, food)
        - Travel style: {travel_style}
        - Trip pace: {trip_pace}
        - Interests: {', '.join(interests)}

        DESTINATIONS TO COMPARE: {', '.join(top_destinations)}

        ==== STEP 1: SEARCH FLIGHTS ====
        Use the flight_prices tool:
        {{
            "flight_groups": {json.dumps(flight_groups)},
            "flight_preferences": {{
                "travel_class": "{travel_class}",
                "nonstop_preferred": {str(nonstop_preferred).lower()}
            }}
        }}

        For each destination, calculate total flight costs and check arrival coordination.

        ==== STEP 2: SELECT BEST DESTINATION ====
        Choose the destination with:
        - Best total flight cost
        - Good arrival time coordination (within 3 hours)
        - Matches group interests

        ==== STEP 3: SEARCH HOTELS ====
        For the selected destination, use hotel_search tool:
        {{
            "destinations": ["XXX"],  // Use the 3-letter city code
            "check_in": "{departure_date}",
            "check_out": "{return_date}",
            "group_accommodation_style": "{group_accommodation_style}",
            "accommodation_details": {json.dumps(accommodation_details)}
        }}

        Select a hotel that fits the budget and room configuration needs.

        ==== STEP 4: GENERATE ACTIVITY ITINERARY ====
        Use the itinerary_generator tool:
        {{
            "destination": "City Name",  // Full city name, not code
            "interests": {json.dumps(interests)},
            "travel_style": "{travel_style}",
            "num_days": {trip_duration},
            "trip_pace": "{trip_pace}"
        }}

        This will return:
        - Daily activities with booking links
        - Activity costs in USD
        - Total activity budget

        ==== STEP 5: CALCULATE FINAL COSTS ====
        For EACH person, calculate:
        - Their flight cost (varies by departure city)
        - Their hotel cost (varies by room type)
        - Activity costs (from itinerary tool)
        - Food estimate ($100/day)
        - TOTAL

        Verify everyone is within their ${budget['budget_min']}-${budget['budget_max']} budget.

        ==== STEP 6: PRESENT COMPLETE PLAN ====

        **SELECTED DESTINATION: [City]**
        Reasoning: [Why this destination won]

        **FLIGHT PLAN**
        For each departure city, provide EXACT flight details in this format:
        
        From [AIRPORT_CODE]:
        - Airline: [Full airline name]
        - Flight: [AIRLINE_CODE][FLIGHT_NUMBER] (e.g., DL447, UA120)
        - Route: [ORIGIN_CODE]→[DEST_CODE]
        - Departure: [DATE] at [TIME]
        - Return Flight: [AIRLINE_CODE][FLIGHT_NUMBER]
        - Return Departure: [DATE] at [TIME]
        - Cost: $[AMOUNT] per person
        - Passengers: [List email addresses from flight group]

        Example:
        From LAX:
        - Airline: Delta
        - Flight: DL447
        - Route: LAX→BCN
        - Departure: June 15, 2024 at 10:15 AM
        - Return Flight: DL448
        - Return Departure: June 20, 2024 at 5:30 PM
        - Cost: $580 per person
        - Passengers: user1@email.com, user2@email.com

        **ACCOMMODATION**
        Hotel Name: [EXACT hotel name as it appears on booking sites]
        City: [City name]
        Check-in: [YYYY-MM-DD]
        Check-out: [YYYY-MM-DD]
        Room Configuration: [X singles, Y doubles]
        Price: $[AMOUNT] per night per room
        Total Nights: [NUMBER]
        Total Hotel Cost: $[TOTAL_AMOUNT]
        
        Example:
        Hotel Name: Hotel Barcelona Center
        City: Barcelona
        Check-in: 2024-06-15
        Check-out: 2024-06-20
        Room Configuration: 1 single, 2 doubles
        Price: $140 per night per room
        Total Nights: 5
        Total Hotel Cost: $2100 (for all rooms)

        **ACTIVITY ITINERARY**
        For each day, list activities with EXACT names and booking details:
        
        Day 1 - [Date]:
        Activity: [EXACT name as on booking platform]
        Description: [Brief description]
        Duration: [X] hours
        Price: $[AMOUNT] per person
        Booking Platform: [Viator/GetYourGuide/TripAdvisor/etc]
        Booking URL: [Full URL if available from itinerary tool]
        
        Example:
        Day 1 - June 15, 2024:
        Activity: Sagrada Familia Skip-the-Line Tour
        Description: Guided tour of Gaudi's masterpiece
        Duration: 2 hours
        Price: $45 per person
        Booking Platform: GetYourGuide
        Booking URL: https://www.getyourguide.com/barcelona-l45/sagrada-familia-tour
        
        Activity: Barcelona Tapas Walking Tour
        Description: Evening food tour in Gothic Quarter
        Duration: 3 hours
        Price: $75 per person
        Booking Platform: Viator
        Booking URL: https://www.viator.com/tours/Barcelona/tapas-tour
        
        [Continue for all days]

        Total Activity Cost: $[Amount] per person

        **BOOKING LINKS SUMMARY**
        Flight Bookings:
        - Use airline websites for best prices
        - Alternative: Google Flights, Kayak

        Hotel Booking:
        - Check hotel website directly
        - Alternative: Booking.com, Hotels.com

        Activities with direct booking:
        - [Activity name]: [Platform] - [URL]
        [List all bookable activities]

        **FINAL COST BREAKDOWN**
        For each passenger email:
        [email@example.com]:
        - Flight from [AIRPORT]: $[amount]
        - Hotel ([room type]): $[amount] 
        - Activities: $[amount]
        - Food: $[amount]
        - TOTAL: $[amount] ✓ Within budget

        **IMPORTANT**: 
        - Include specific flight numbers (e.g., DL447, UA120)
        - Use airport codes (e.g., LAX, JFK, BCN)
        - List exact costs for each component
        - Different people will have different totals due to flight origins and room choices
        """

        try:
            result = self.agent.run(planning_prompt)
            
            return {
                "success": True,
                "agent_response": result,
                "system_type": "LangChain Agent with Tools",
                "preferences_used": user_preferences
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "system_type": "LangChain Agent with Tools"
            }


# Optional: Initialize globally
travel_agent = TravelAgent()
