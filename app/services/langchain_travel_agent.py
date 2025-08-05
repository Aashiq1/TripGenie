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
from app.tools.activity_planning_tool import ActivityPlanningTool
# DISABLED: Old Tavily-based itinerary tool - will be replaced with new multi-API system  
# from app.tools.tavily_itinerary_tool import ItineraryTool

# Load environment variables
load_dotenv()

class TravelAgent:
    """LangChain-powered travel planning agent with real tools."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        # Instantiate tool wrappers
        self.flight_tool = AmadeusFlightTool()
        self.hotel_tool = HotelSearchTool()
        self.activity_tool = ActivityPlanningTool()
        # DISABLED: Old Tavily-based itinerary tool - replaced with new Google Places system
        # self.itinerary_tool = ItineraryTool()

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
                name=self.activity_tool.name,
                description=self.activity_tool.description,
                func=self.activity_tool._call
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
        
        # Use destination directly (now stores original user input like "Madrid")
        activity_destination = top_destinations[0] if top_destinations else 'Barcelona'
        
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

        DESTINATION: {top_destinations[0] if top_destinations else 'Barcelona'}

        ==== STEP 1: SEARCH FLIGHTS ====
        Use the flight_prices tool:
        {{
            "flight_groups": {json.dumps(flight_groups)},
            "flight_preferences": {{
                "travel_class": "{travel_class}",
                "nonstop_preferred": {str(nonstop_preferred).lower()}
            }}
        }}

        IMPORTANT: Check the flight search results carefully. If flights are not found:

        1. **Review the search_summary** - Look for success_rate and failed_routes
        2. **Check for flight_search_status** - If status is "NO_FLIGHTS_FOUND", explain this to the user
        3. **If no flights found:**
           - Acknowledge the issue: "I was unable to retrieve flight pricing and schedule information"
           - Explain why: Mention test environment limitations, future dates, or route availability
           - Provide alternatives from the recommendations in the response
           - Suggest manual searches using the alternative_search_options provided
           - DO NOT proceed with destination selection or trip planning

        4. **If some flights found:** Proceed with trip planning using available data

        ==== STEP 2: HANDLE FLIGHT SEARCH RESULTS ====
        
        **If ALL flight searches failed:**
        - Respond with: "I'm sorry, but I was unable to retrieve flight pricing and schedule information for {top_destinations[0] if top_destinations else 'the destination'} from the specified departure cities and dates. This is likely because [explain reason from flight_search_status]. 
        
        Here are some alternatives:
        - [List recommendations from the flight search response]
        - For manual flight searches, try: [List alternative_search_options]
        
        Without flight information, I cannot provide a complete group travel plan or confirm if the trip fits within your budget. Would you like to try different dates or have me assist with other aspects of trip planning?"

        **If SOME flights found:** Continue with trip planning using available flight data.

        ==== STEP 3: SEARCH HOTELS ====
        For the destination, use hotel_search tool:
        {{
            "destinations": ["XXX"],  // Use the 3-letter city code for {top_destinations[0] if top_destinations else 'Barcelona'}
            "check_in": "{departure_date}",
            "check_out": "{return_date}",
            "group_accommodation_style": "{group_accommodation_style}",
            "accommodation_details": {json.dumps(accommodation_details)}
        }}

        ==== STEP 4: PLAN ACTIVITIES (MANDATORY) ====
        **CRITICAL: You MUST call the plan_activities tool to generate the actual activity itinerary. Do NOT create placeholder text.**
        
        Call the plan_activities tool with exactly this JSON:
        {{
            "destination": "{activity_destination}",
            "interests": {json.dumps(interests)},
            "trip_duration_days": {trip_duration},
            "travel_style": "{travel_style}",
            "trip_pace": "{trip_pace}",
            "budget_per_person": {(budget['budget_min'] + budget['budget_max']) // 2}
        }}

        **REQUIRED:** The tool will return a complete day-by-day itinerary with real activities, costs, and venue details from Google Places API.
        **YOU MUST INCLUDE THE COMPLETE TOOL OUTPUT IN YOUR RESPONSE - DO NOT SUMMARIZE OR CREATE PLACEHOLDER TEXT.**

        ==== STEP 5: PRESENT COMPLETE PLAN (Only if all data available) ====

        **DESTINATION: {top_destinations[0] if top_destinations else 'Barcelona'}**

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

        **ACCOMMODATION**
        Hotel Name: [EXACT hotel name as it appears on booking sites]
        City: [City name]
        Check-in: [YYYY-MM-DD]
        Check-out: [YYYY-MM-DD]
        Room Configuration: [X singles, Y doubles]
        Price: $[AMOUNT] per night per room
        Total Nights: [NUMBER]
        Total Hotel Cost: $[TOTAL_AMOUNT]

        **ACTIVITY ITINERARY**
        [PASTE THE COMPLETE OUTPUT FROM THE plan_activities TOOL HERE - INCLUDING ALL DAYS, ACTIVITIES, COSTS, AND VENUE DETAILS]
        
        The itinerary will automatically include:
        - Day-by-day breakdown with scheduled times
        - Real venue names from Google Places API
        - Accurate addresses and contact information
        - Star ratings and user review counts
        - Estimated costs per person per activity
        - Activity types (cultural, dining, outdoor, etc.)
        - Duration estimates for each activity

        **FINAL COST BREAKDOWN**
        For each passenger email:
        [email@example.com]:
        - Flight from [AIRPORT]: $[amount]
        - Hotel ([room type]): $[amount] 
        - Activities (from Google Places): $[amount]
        - Estimated meals: $[amount]
        - TOTAL: $[amount] ✓ Within budget
        
        **ACTIVITY COST SUMMARY**
        - Total activity cost per person: $[amount from plan_activities tool]
        - Average per day: $[amount/number of days]
        - Source: Google Places API (real venues with verified ratings)

        **CRITICAL REMINDERS:**
        - ALWAYS check flight search status before proceeding
        - If no flights found, explain the issue and provide alternatives
        - Don't create incomplete plans - be transparent about what data is missing
        - Provide helpful next steps even when searches fail
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
