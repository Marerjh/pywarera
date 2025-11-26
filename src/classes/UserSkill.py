class UserSkill:
    def __init__(self, data):
        self.level: int = data["level"]
        self.ammo_percent: int | None = data["ammoPercent"]
        self.buffs_percent: int | None = data["buffsPercent"]
        self.debuffs_percent: int | None = data["debuffsPercent"]
        self.value: int | None = data["value"]
        self.weapon: int | None = data["weapon"]
        self.equipment: int | None = data["equipment"]
        self.limited: int | None = data["limited"]
        self.total: int = data["total"]