from typing import Tuple, Dict, Optional
from app.services import storage
from app.models.group_inputs import TripGroup

def update_trip_group_and_invalidate(group_code: str, updates: Dict) -> Tuple[dict, bool, Dict[str, bool]]:
    trip_group = storage.get_trip_group(group_code)
    if not trip_group:
        raise ValueError("Trip not found")

    old = trip_group.model_dump()
    for k, v in updates.items():
        setattr(trip_group, k, v)
    storage.update_trip_group(trip_group)

    changed = {
        "destination": old.get("destination") != trip_group.destination,
        "dates": (old.get("departure_date") != trip_group.departure_date) or (old.get("return_date") != trip_group.return_date),
        "hotel": (old.get("budget") != trip_group.budget) or (old.get("accommodation") != trip_group.accommodation),
    }
    requires_replanning = changed["destination"] or changed["dates"] or changed["hotel"]
    if requires_replanning:
        storage.delete_trip_plan(group_code)

    return trip_group.model_dump(), requires_replanning, changed

def can_reset_trip_plan(user_email: str, trip_group: Optional[TripGroup]) -> bool:
    if trip_group is None:
        return False
    
    if getattr(trip_group, 'creator_email', None) == user_email:
        return True
    
    return False