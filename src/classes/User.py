from src.classes.UserDates import UserDates
from src.classes.UserLeveling import UserLeveling
from src.classes.UserSkills import UserSkills
from src.classes.UserRankings import UserRankings
from typing import Literal

class User:
    def __init__(self, data):
        self.dates = UserDates(data["dates"])
        self.is_banned: bool = data.get("infos", {}).get("isBanned", False)
        self.leveling = UserLeveling(data["leveling"])
        self.id: str = data["_id"]
        self.username: str = data["username"]
        self.country: str = data["country"]
        self.is_active: bool = data["isActive"]
        self.skills = UserSkills(data["skills"])
        self.created_at: str = data["createdAt"]
        self.rankings = UserRankings(data["rankings"]) if data.get("rankings") else None
        self.mu: str = data.get("mu")

    def get_level(self) -> int:
        return self.leveling.level

    def get_wealth(self) -> int:
        return self.rankings.user_wealth.value

    def get_skills(self) -> dict[Literal[
                            "energy", "health", "hunger", "attack", "companies", "entrepreneurship",
                            "production", "critical_chance", "critical_damages", "armor", "precision",
                            "dodge", "loot_chance"], int]:
        result = {
            "energy": self.skills.energy.level,
            "health": self.skills.health.level,
            "hunger": self.skills.hunger.level,
            "attack": self.skills.attack.level,
            "companies": self.skills.companies.level,
            "entrepreneurship": self.skills.entrepreneurship.level,
            "production": self.skills.production.level,
            "critical_chance": self.skills.critical_chance.level,
            "critical_damages": self.skills.critical_damages.level,
            "armor": self.skills.armor.level,
            "precision": self.skills.precision.level,
            "dodge": self.skills.dodge.level,
            "loot_chance": self.skills.loot_chance.level
        }
        return result