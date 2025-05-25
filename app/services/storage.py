import json
from app.models.group_inputs import GroupInput, UserInput
from typing import List
from pathlib import Path

DATA_FILE = Path("data.json")

def save_group_data(users: List[UserInput]):
    data = GroupInput(users=users).model_dump()
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_group_data() -> List[UserInput]:
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    group = GroupInput(**data)
    return group.users
