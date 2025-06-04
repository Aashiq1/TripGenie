import json
from app.models.group_inputs import GroupInput, UserInput
from typing import List
from pathlib import Path

# File path for persisting user data
DATA_FILE = Path("data.json")

def save_group_data(users: List[UserInput]):
    """
    Save a list of user inputs to disk as JSON.

    Args:
        users (List[UserInput]): The list of all current user inputs to save.
    """
    data = GroupInput(users=users).model_dump()
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_group_data() -> List[UserInput]:
    """
    Load previously saved user inputs from disk.

    Returns:
        List[UserInput]: The list of user inputs if available, otherwise an empty list.
    """
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    group = GroupInput(**data)
    return group.users
