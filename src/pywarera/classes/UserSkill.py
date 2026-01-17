class UserSkill:
    def __init__(self, data):
        self.level: int = data["level"]
        self.ammo_percent: int | None = data.get("ammoPercent", None)
        self.buffs_percent: int | None = data.get("buffsPercent", None)
        self.debuffs_percent: int | None = data.get("debuffsPercent", None)
        self.value: int | None = data.get("value", None)
        self.weapon: int | None = data["weapon"]
        self.equipment: int | None = data["equipment"]
        self.limited: int | None = data["limited"]
        self.total: int = data["total"]