class UserLeveling:
    def __init__(self, data):
        self.level = data["level"]
        self.total_xp = data["totalXp"]
        self.daily_xp_left = data["dailyXpLeft"]
        self.available_skill_points = data["availableSkillPoints"]
        self.spent_skill_points = data["spentSkillPoints"]
        self.total_skill_points = data["totalSkillPoints"]
        self.free_reset = data["freeReset"]