from typing import Literal

class Company:
    def __init__(self, data):
        self.id: str | None = data.get("_id")
        self.user: str | None = data.get("user")
        self.region: str | None = data.get("region")
        self.item_code: str | None = data.get("itemCode")
        self.is_full: bool | None = data.get("isFull")
        self.name: str = data.get("name", "Unknown")
        self.production: float = data.get("production", 0)
        self.automated_engine: int = data["activeUpgradeLevels"]["automatedEngine"]
        self.break_room: int = data["activeUpgradeLevels"].get("breakRoom", 0)
        self.workers: list[dict] | None = {i["_id"]: (i["user"], i["wage"]) for i in data["workers"]} if data.get("workers", False) else None
        self.created_at = data["createdAt"]
        self.updated_at = data["updatedAt"]
        self.v = data["__v"]
        self.estimated_value: float = data.get("estimatedValue", 0)
        self.last_hires_at = data["dates"]["lastHiresAt"] if data.get("dates", False) else []
        self.moved_up_at = data["movedUpAt"] if data.get("movedUpAt", False) else None
        self.worker_count: int = data.get("workerCount", 0)
        self.disabled_at = data.get("disabledAt")

    def get_upgrades(self) -> dict[Literal["automated_engine", "break_room"], int]:
        return {"automated_engine": self.automated_engine, "break_room": self.break_room}

    @property
    def disabled(self):
        return True if self.disabled_at is not None else False
    