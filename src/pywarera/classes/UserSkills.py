from .UserSkill import UserSkill
from .UserSkillBar import UserSkillBar

class UserSkills:
    def __init__(self, data):
        self.energy: UserSkillBar = UserSkillBar(data["energy"])
        self.health: UserSkillBar = UserSkillBar(data["health"])
        self.hunger: UserSkillBar = UserSkillBar(data["hunger"])
        self.attack: UserSkill = UserSkill(data["attack"])
        self.companies: UserSkill = UserSkill(data["companies"])
        self.entrepreneurship: UserSkillBar = UserSkillBar(data["entrepreneurship"])
        self.production: UserSkillBar = UserSkillBar(data["production"])
        self.critical_chance: UserSkill = UserSkill(data["criticalChance"])
        self.critical_damages: UserSkill = UserSkill(data["criticalDamages"])
        self.armor: UserSkill = UserSkill(data["armor"])
        self.precision: UserSkill = UserSkill(data["precision"])
        self.dodge: UserSkill = UserSkill(data["dodge"])
        self.loot_chance: UserSkill = UserSkill(data["lootChance"])

    def get_skillpoints_spent(self, skill: UserSkill) -> int:
        return (skill.level * (skill.level + 1)) / 2

    def get_total_skill_points_spent_groups(self) -> tuple[int, int]:
        economy_skills = [self.energy, self.companies, self.entrepreneurship, self.production, self.loot_chance]
        military_skills = [self.health, self.hunger, self.attack, self.critical_chance, self.critical_damages, self.armor, self.dodge]
        economy_skills_price, military_skills_price = 0, 0
        for i in economy_skills:
            economy_skills_price += self.get_skillpoints_spent(i)
        for i in military_skills:
            military_skills_price += self.get_skillpoints_spent(i)
        return economy_skills_price, military_skills_price

    def get_military_skill_points(self) -> int:
        return self.get_total_skill_points_spent_groups()[1]

    def get_economy_skill_points(self) -> int:
        return self.get_total_skill_points_spent_groups()[0]

    def get_total_skill_points_spent(self) -> int:
        by_groups = self.get_total_skill_points_spent_groups()
        return by_groups[0] + by_groups[1]
