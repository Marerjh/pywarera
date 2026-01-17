from typing import Literal

class Company:
    def __init__(self, data):
        self.id: str = data["_id"]
        self.user: str = data["user"]
        self.storage = data["activeUpgradeLevels"]["storage"]
        self.automated_engine = data["activeUpgradeLevels"]["automatedEngine"]
        self.break_room = data["activeUpgradeLevels"]["breakRoom"]
        self.workers = {i["_id"]: (i["user"], i["wage"]) for i in data["workers"]}
        self.created_at = data["createdAt"]
        self.updated_at = data["updatedAt"]
        self.v = data["__v"]
        self.estimated_value = data["estimatedValue"]
        self.last_hires_at = data["dates"]["lastHiresAt"] if data.get("dates", False) else []
        self.moved_up_at = data["movedUpAt"] if data.get("movedUpAt", False) else None

    def get_upgrades(self) -> dict[Literal["storage", "automated_engine", "break_room"], int]:
        return {"storage": self.storage, "automated_engine": self.automated_engine, "break_room": self.break_room}