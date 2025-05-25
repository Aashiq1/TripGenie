from fastapi import APIRouter;
from app.models.group_inputs import GroupInput, UserInput
from app.services.storage import save_group_data, load_group_data

router = APIRouter(prefix="/inputs", tags=["inputs"])

group_data: list[UserInput] = load_group_data()

@router.post("/user")
def submit_user(user: UserInput):
    group_data.append(user)
    save_group_data(group_data)
    return {"status": "received", "data": user}

@router.get("/group")
def get_group():
    return GroupInput(users=group_data)

