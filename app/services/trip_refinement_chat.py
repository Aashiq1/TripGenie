# app/services/trip_refinement_chat.py
"""
Chat system for trip creators to refine their itinerary with AI assistance.
Only the trip creator can access this feature.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType

# Import the tools from the tools folder
from app.tools.refinement_tool import create_refinement_tools

# Import the parser
from app.services.agent_parser import AgentParser

logger = logging.getLogger(__name__)


class TripRefinementChat:
    """
    Chat interface for trip creators to refine their itinerary.
    Maintains context of the current trip and can make specific changes.
    """
    
    def __init__(self, trip_plan: Dict, group_code: str, creator_email: str):
        """
        Initialize with existing trip plan and creator info.
        """
        self.trip_plan = trip_plan
        self.group_code = group_code
        self.creator_email = creator_email
        
        # Parse current itinerary
        self.parser = AgentParser()
        self.current_itinerary = self._parse_current_itinerary()
        
        # Initialize chat components
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7
        )
        
        # Initialize memory with context
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Add initial context to memory
        self._initialize_context()
        
        # Get tools from the tools folder
        self.tools = create_refinement_tools(
            current_itinerary=self.current_itinerary,
            preferences=self.trip_plan.get('preferences_used', {})
        )
        
        # Create the refinement agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True
        )
    
    def _parse_current_itinerary(self) -> Dict:
        """Extract structured data from current trip plan."""
        agent_response = self.trip_plan.get('agent_response', '')
        preferences = self.trip_plan.get('preferences_used', {})
        
        return self.parser.parse_agent_response(agent_response, preferences)
    
    def _initialize_context(self):
        """Add trip context to chat memory."""
        context = f"""
        I'm helping refine a group trip that's already been planned. Here's the current itinerary:
        
        Destination: {self.current_itinerary.get('destination')}
        Dates: {self.trip_plan['preferences_used']['departure_date']} to {self.trip_plan['preferences_used']['return_date']}
        Group Size: {self.trip_plan['preferences_used']['group_size']} people
        Budget: ${self.trip_plan['preferences_used']['budgets']['budget_min']}-${self.trip_plan['preferences_used']['budgets']['budget_max']} per person
        
        Current Flights:
        {self._format_current_flights()}
        
        Current Hotel:
        {self._format_current_hotel()}
        
        Current Activities:
        {self._format_current_activities()}
        
        I can help you:
        - Search for alternative flights
        - Find different hotels
        - Add/remove/replace activities
        - Adjust the schedule
        - Search for specific things you want to include
        """
        
        # Add as system context
        self.memory.chat_memory.add_message(
            AIMessage(content=context)
        )
    
    def _format_current_flights(self) -> str:
        """Format current flight info for context."""
        flights = self.current_itinerary.get('flights', {})
        formatted = []
        
        for city, flight in flights.items():
            formatted.append(
                f"From {city}: {flight.get('airline', 'Unknown')} "
                f"{flight.get('flight_number', '')} - ${flight.get('price', 0)}/person"
            )
        
        return "\n".join(formatted) if formatted else "No flights selected yet"
    
    def _format_current_hotel(self) -> str:
        """Format current hotel info for context."""
        hotel = self.current_itinerary.get('hotel', {})
        if hotel:
            return (
                f"{hotel.get('name', 'Unknown Hotel')}\n"
                f"Configuration: {hotel.get('room_configuration', 'Unknown')}\n"
                f"Price: ${hotel.get('price_per_night', 0)}/night"
            )
        return "No hotel selected yet"
    
    def _format_current_activities(self) -> str:
        """Format current activities for context."""
        activities = self.current_itinerary.get('activities', [])
        if not activities:
            return "No activities planned yet"
        
        formatted = []
        for act in activities:
            formatted.append(
                f"Day {act.get('day', '?')}: {act.get('name', 'Unknown')} "
                f"(${act.get('price_per_person', 0)}/person)"
            )
        
        return "\n".join(formatted)
    
    # REMOVED: _create_refinement_tools() - Now imported from tools folder
    
    # REMOVED: Individual tool functions - Now in refinement_tools.py
    
    def _calculate_total_cost(self) -> float:
        """Calculate total cost per person for current itinerary."""
        total = 0
        
        # Flight costs
        for flight in self.current_itinerary.get('flights', {}).values():
            total += flight.get('price', 0)
        
        # Hotel costs (simplified - would need room sharing logic)
        hotel = self.current_itinerary.get('hotel', {})
        if hotel:
            nights = self.trip_plan['preferences_used']['trip_duration_days']
            total += hotel.get('price_per_night', 0) * nights / 2  # Assuming sharing
        
        # Activity costs
        for activity in self.current_itinerary.get('activities', []):
            total += activity.get('price_per_person', 0)
        
        # Food estimate
        total += 100 * self.trip_plan['preferences_used']['trip_duration_days']
        
        return total
    
    async def process_refinement_request(self, user_email: str, message: str) -> Dict[str, Any]:
        """
        Process a refinement request from the trip creator.
        """
        # Verify user is the creator
        if user_email != self.creator_email:
            return {
                "success": False,
                "error": "Only the trip creator can refine the itinerary"
            }
        
        try:
            # Process the message through the agent
            response = self.agent.run(message)
            
            # Check if any changes were made
            changes_made = self._detect_changes(message, response)
            
            return {
                "success": True,
                "response": response,
                "changes_made": changes_made,
                "requires_regeneration": len(changes_made) > 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing refinement request: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _detect_changes(self, message: str, response: str) -> List[str]:
        """Detect what changes were made based on the conversation."""
        changes = []
        
        # Simple keyword detection for now
        message_lower = message.lower()
        response_lower = response.lower()
        
        if any(word in message_lower for word in ["change flight", "different flight", "alternative flight"]):
            if "option" in response_lower or "found" in response_lower:
                changes.append("flights")
        
        if any(word in message_lower for word in ["change hotel", "different hotel", "alternative hotel"]):
            if "option" in response_lower or "found" in response_lower:
                changes.append("hotel")
        
        if any(word in message_lower for word in ["add activity", "remove activity", "change activity"]):
            if "found" in response_lower or "added" in response_lower or "removed" in response_lower:
                changes.append("activities")
        
        return changes
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """Get the chat history for display."""
        history = []
        
        for message in self.memory.chat_memory.messages:
            if isinstance(message, HumanMessage):
                history.append({
                    "role": "user",
                    "content": message.content,
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif isinstance(message, AIMessage):
                history.append({
                    "role": "assistant", 
                    "content": message.content,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return history


# Service class for managing refinement sessions
class TripRefinementService:
    """
    Service to manage trip refinement chat sessions.
    Handles authorization and session management.
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, TripRefinementChat] = {}
    
    async def start_refinement_session(self, 
                                     group_code: str, 
                                     user_email: str,
                                     trip_plan: Dict) -> Dict[str, Any]:
        """
        Start a new refinement session for a trip creator.
        """
        # Verify user is the creator
        creator_email = trip_plan.get('group_profile', {}).get('user_profiles', [{}])[0].get('email')
        
        if user_email != creator_email:
            return {
                "success": False,
                "error": "Only the trip creator can refine the itinerary"
            }
        
        # Create new session
        session = TripRefinementChat(
            trip_plan=trip_plan,
            group_code=group_code,
            creator_email=creator_email
        )
        
        # Store session
        session_key = f"{group_code}:{user_email}"
        self.active_sessions[session_key] = session
        
        return {
            "success": True,
            "session_id": session_key,
            "message": "Refinement session started. How would you like to modify your trip?"
        }
    
    async def process_message(self,
                            session_id: str,
                            message: str) -> Dict[str, Any]:
        """
        Process a message in an active refinement session.
        """
        session = self.active_sessions.get(session_id)
        
        if not session:
            return {
                "success": False,
                "error": "No active session found. Please start a new session."
            }
        
        # Extract user email from session_id
        user_email = session_id.split(':')[1]
        
        return await session.process_refinement_request(user_email, message)
    
    def end_session(self, session_id: str):
        """End a refinement session."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]


# Global service instance
refinement_service = TripRefinementService()


# Example usage in your API
async def handle_refinement_chat(group_code: str, user_email: str, message: str, trip_plan: Optional[Dict] = None):
    """
    Handle refinement chat requests from API.
    """
    session_id = f"{group_code}:{user_email}"
    
    # Start new session if needed
    if session_id not in refinement_service.active_sessions and trip_plan:
        result = await refinement_service.start_refinement_session(
            group_code=group_code,
            user_email=user_email,
            trip_plan=trip_plan
        )
        if not result["success"]:
            return result
    
    # Process the message
    return await refinement_service.process_message(session_id, message)