from typing import Dict, Any, Optional


class MemoryStorage:
    def __init__(self):
        # Format: {user_id: {"state": "flow_name:step_name", "data": {...}}}
        self._data: Dict[int, Dict[str, Any]] = {}

    def set_state(self, user_id: int, state: Optional[str]) -> None:
        if user_id not in self._data:
            self._data[user_id] = {"state": None, "data": {}}
        self._data[user_id]["state"] = state

    def get_state(self, user_id: int) -> Optional[str]:
        return self._data.get(user_id, {}).get("state")

    def update_data(self, user_id: int, **kwargs) -> None:
        if user_id not in self._data:
            self._data[user_id] = {"state": None, "data": {}}
        self._data[user_id]["data"].update(kwargs)

    def get_data(self, user_id: int) -> Dict[str, Any]:
        return self._data.get(user_id, {}).get("data", {})

    def clear(self, user_id: int) -> None:
        if user_id in self._data:
            del self._data[user_id]