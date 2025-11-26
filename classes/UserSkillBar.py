from classes.UserSkill import UserSkill

class UserSkillBar(UserSkill):
    def __init__(self, data):
        super().__init__(data)
        self.current_bar_value: float = data["currentBarValue"]
        self.hourly_bar_regen: float = data["hourlyBarRegen"]