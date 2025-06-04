from fastapi import APIRouter
from app.models.group_inputs import GroupInput, UserInput
from app.services.storage import save_group_data, load_group_data
from app.services.planner import plan_trip as run_plan_trip

# Initialize the API router with prefix and tags for documentation
router = APIRouter(prefix="/inputs", tags=["inputs"])

# Load existing group data from storage (in-memory cache for this session)
group_data: list[UserInput] = load_group_data()

@router.post("/user")
def submit_user(user: UserInput):
    """
    Submit a new user's input to the group data.

    Args:
        user (UserInput): The user's preferences and availability.

    Returns:
        dict: Confirmation status and submitted user data.
    """
    group_data.append(user)
    save_group_data(group_data)
    return {"status": "received", "data": user}

@router.get("/group")
def get_group():
    """
    Retrieve the current list of submitted users for the trip group.

    Returns:
        GroupInput: A wrapper around the list of all UserInput entries.
    """
    return GroupInput(users=group_data)

@router.post("/plan")
def plan_trip_endpoint():
    """
    Run the trip planning algorithm based on the current group data.

    Returns:
        dict: Trip plan including best date ranges, user availability, and group preferences.
    """
    return run_plan_trip(group_data)

