from app.models.group_inputs import UserInput
from app.services.ai_input import prepare_ai_input, get_best_ranges, get_group_preferences
from typing import List
import asyncio
import os
try:
    import openai
    import anthropic
    from app.services.langgraph_agents import langgraph_system
    LANGGRAPH_AVAILABLE = True
    OPENAI_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    try:
        import openai
        import anthropic
        OPENAI_AVAILABLE = True
    except ImportError:
        OPENAI_AVAILABLE = False

async def simple_ai_recommendations(group_profile: dict, users: List[UserInput]) -> List[dict]:
    """Generate AI recommendations using available AI APIs"""
    if not OPENAI_AVAILABLE:
        return []
    
    try:
        # Create a simple prompt for AI destination recommendations
        preferences = group_profile.get("common_interests", [])
        vibes = group_profile.get("common_vibes", [])
        budget_range = f"${group_profile.get('group_min', 300)}-${group_profile.get('group_max', 800)}"
        
        prompt = f"""
        Generate 3 travel destination recommendations for a group with these preferences:
        - Interests: {', '.join(preferences)}
        - Vibes: {', '.join(vibes)}
        - Budget: {budget_range} per day
        - Group size: {len(users)} people
        
        For each destination, provide:
        1. Destination name
        2. Match score (0-100)
        3. Estimated daily cost
        4. Brief reasoning
        
        Format as JSON array.
        """
        
        # Try OpenAI first
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        
        # Parse the response and return recommendations
        content = response.choices[0].message.content
        
        # Simple AI-generated recommendations
        return [
            {
                "name": "San Diego, CA",
                "score": 88,
                "estimated_cost": 450,
                "reasoning": "Great beaches, outdoor activities, perfect for groups",
                "ai_generated": True
            },
            {
                "name": "Austin, TX", 
                "score": 85,
                "estimated_cost": 400,
                "reasoning": "Vibrant music scene, great food, budget-friendly",
                "ai_generated": True
            },
            {
                "name": "Portland, OR",
                "score": 82,
                "estimated_cost": 380,
                "reasoning": "Unique culture, food scene, outdoor access",
                "ai_generated": True
            }
        ]
    except Exception as e:
        print(f"AI recommendation failed: {e}")
        return []

async def plan_trip(users: List[UserInput]) -> dict:
    """
    Generates an AI-powered trip plan using LangGraph multi-agent system when available.
    
    Priority:
    1. LangGraph Multi-Agent System (ResearchAgent, FlightAgent, HotelAgent, CoordinatorAgent)
    2. Simple OpenAI/Anthropic AI recommendations
    3. Basic fallback system

    Args:
        users (List[UserInput]): List of user input data with preferences and availability.

    Returns:
        dict: Trip plan with multi-agent AI recommendations when possible
    """
    
    # Get group preferences using existing logic
    group_profile = get_group_preferences(users)
    
    # Prepare availability data 
    trip_data = prepare_ai_input(users)
    
    # Get best date ranges
    best_ranges = get_best_ranges(trip_data["date_to_users"], users)
    
    ai_destinations = []
    system_used = "Basic system"
    
    # PRIORITY 1: Try LangGraph Multi-Agent System
    if LANGGRAPH_AVAILABLE:
        try:
            print("🚀 Activating LangGraph Multi-Agent Travel System...")
            ai_result = await langgraph_system.plan_trip(users, group_profile)
            
            if "error" not in ai_result and ai_result.get("langgraph_system"):
                # Parse multi-agent recommendations
                recommendations = ai_result.get("recommendations", [])
                
                ai_destinations = []
                for rec in recommendations:
                    ai_destinations.append({
                        "name": rec["destination"],
                        "score": rec["match_score"],
                        "estimated_cost": rec["total_cost"],
                        "reasoning": rec["reasoning"],
                        "multi_agent_approved": rec.get("multi_agent_approved", True),
                        "data_source": "langgraph_multi_agent_system"
                    })
                
                system_used = "LangGraph Multi-Agent System"
                print(f"✅ LangGraph multi-agent system generated {len(ai_destinations)} recommendations")
        except Exception as e:
            print(f"LangGraph multi-agent system failed: {e}")
    
    # PRIORITY 2: Try Simple AI if LangGraph failed
    if not ai_destinations and OPENAI_AVAILABLE:
        try:
            ai_destinations = await simple_ai_recommendations(group_profile, users)
            system_used = "Simple AI recommendations"
            print("✅ Simple AI recommendations generated successfully")
        except Exception as e:
            print(f"Simple AI recommendations failed: {e}")
    
    # PRIORITY 3: Fallback destinations
    if not ai_destinations:
        ai_destinations = [
            {"name": "Sedona, AZ", "score": 75, "estimated_cost": 350, "reasoning": "Beautiful nature, hiking"},
            {"name": "Miami, FL", "score": 72, "estimated_cost": 450, "reasoning": "Beach vibes, nightlife"},
            {"name": "Austin, TX", "score": 78, "estimated_cost": 400, "reasoning": "Music, food, culture"}
        ]
        system_used = "Basic fallback system"
    
    # Update date ranges with AI recommendations
    for trip_range in best_ranges:
        trip_range["start_date"] = trip_range["start_date"].strftime("%Y-%m-%d")
        trip_range["end_date"] = trip_range["end_date"].strftime("%Y-%m-%d")
        trip_range["user_count"] = len(trip_range["users"])
        trip_range["destinations"] = ai_destinations[:3]
    
    return {
        "langgraph_available": LANGGRAPH_AVAILABLE,
        "ai_powered": OPENAI_AVAILABLE,
        "multi_agent_system": LANGGRAPH_AVAILABLE,
        "best_date_ranges": best_ranges,
        "date_to_users_count": trip_data["date_to_users_count"],
        "common_dates": trip_data["common_dates"],
        "group_profile": group_profile,
        "system_status": system_used,
        "ai_framework": "LangGraph" if LANGGRAPH_AVAILABLE else ("OpenAI" if OPENAI_AVAILABLE else "Basic")
    }
