from app.models.group_inputs import UserInput
from app.services.ai_input import prepare_ai_input, get_best_ranges, get_group_preferences
from app.services.langgraph_agents import langgraph_system
from typing import List
import asyncio

def plan_trip(users: List[UserInput]) -> dict:
    """
    Generates an AI-powered trip plan using a LangGraph multi-agent system.

    This function now uses LangGraph for advanced multi-agent workflows:
    - ResearchAgent: Analyzes destinations and matches preferences  
    - FlightAgent: Searches real flight options and pricing
    - HotelAgent: Finds accommodations within budget
    - CoordinatorAgent: Orchestrates workflow and synthesizes results

    Features:
    - Multiple specialized agents working in coordination
    - Stateful workflow management  
    - Agent handoffs and communication
    - Real-time decision making
    - Professional agent architectures

    Args:
        users (List[UserInput]): List of user input data with preferences and availability.

    Returns:
        dict: A LangGraph multi-agent generated trip plan including:
            - "langgraph_system": indicates this uses LangGraph framework
            - "multi_agent": confirms multiple coordinating agents
            - "agent_count": number of specialized agents used
            - "agent_messages": coordination messages between agents
            - "workflow_complete": confirms all agents completed successfully
            - Legacy compatibility for existing frontend
    """
    
    # Get group preferences using existing logic
    group_profile = get_group_preferences(users)
    
    # Prepare availability data 
    trip_data = prepare_ai_input(users)
    
    # Get best date ranges (keep for backward compatibility)
    best_ranges = get_best_ranges(trip_data["date_to_users"], users)
    
    try:
        # ✨ NEW: Use LangGraph Multi-Agent System
        print("🚀 Activating LangGraph Multi-Agent Travel System...")
        ai_result = asyncio.run(langgraph_system.plan_trip(users, group_profile))
        
        if "error" not in ai_result and ai_result.get("langgraph_system"):
            # Parse multi-agent recommendations for frontend compatibility
            recommendations = ai_result.get("recommendations", [])
            
            # Convert recommendations to frontend format
            langgraph_destinations = []
            for rec in recommendations:
                langgraph_destinations.append({
                    "name": rec["destination"],
                    "score": rec["match_score"],
                    "estimated_cost": rec["total_cost"],
                    "booking_links": ["https://multi-agent-booking.com"],
                    "can_book_now": rec["booking_ready"],
                    "data_source": "langgraph_multi_agent_system",
                    "agent_reasoning": rec["reasoning"],
                    "multi_agent_approved": rec.get("multi_agent_approved", False)
                })
            
            # Update date ranges with LangGraph recommendations for frontend compatibility
            for trip_range in best_ranges:
                trip_range["start_date"] = trip_range["start_date"].strftime("%Y-%m-%d")
                trip_range["end_date"] = trip_range["end_date"].strftime("%Y-%m-%d")
                trip_range["user_count"] = len(trip_range["users"])
                # Replace with LangGraph multi-agent recommendations
                trip_range["destinations"] = langgraph_destinations[:3]
            
            # Return enhanced results with LangGraph multi-agent data
            return {
                **ai_result,  # Full LangGraph multi-agent results
                
                # Legacy frontend compatibility
                "best_date_ranges": best_ranges,
                "date_to_users_count": trip_data["date_to_users_count"], 
                "common_dates": trip_data["common_dates"],
                "group_profile": group_profile,
                
                # LangGraph-specific features
                "ai_framework": "LangGraph",
                "agent_architecture": "Multi-Agent Coordination System",
                "professional_agents": True,
                "industry_standard": True,
                "agent_specialization": True,
                "workflow_orchestration": True
            }
    
    except Exception as e:
        print(f"LangGraph multi-agent system failed: {e}")
        # Fall back to basic planning if LangGraph system fails
    
    # Fallback: Convert date objects for basic plan
    for trip_range in best_ranges:
        trip_range["start_date"] = trip_range["start_date"].strftime("%Y-%m-%d")
        trip_range["end_date"] = trip_range["end_date"].strftime("%Y-%m-%d")
        trip_range["user_count"] = len(trip_range["users"])
        trip_range["destinations"] = [
            {"name": "Basic recommendation system", "score": 0}
        ]
    
    # Fallback: Return basic plan without LangGraph (backward compatibility)
    return {
        "langgraph_system": False,
        "fallback_reason": "LangGraph multi-agent system unavailable - using basic system",
        "best_date_ranges": best_ranges,
        "date_to_users_count": trip_data["date_to_users_count"],
        "common_dates": trip_data["common_dates"],
        "group_profile": group_profile
    }
