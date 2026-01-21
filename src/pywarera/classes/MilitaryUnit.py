class MilitaryUnit:
    def __init__(self, data):
        self.managers: list = data.get("managers", [])
        self.commanders: list = data.get("commanders", [])
        self.id: str | None = data.get("_id")
        self.user: str | None = data.get("user")
        self.region: str | None = data.get("regions")
        self.name: str = data.get("Name", "Unknown")
        self.members: list = data.get("members", [])
        self.created_at = data.get("createdAt")
        self.updated_at = data.get("updatedAt")
        self.v = data.get("__v")
        self.dormitories: int = data.get("activeUpgradesLevels", {}).get("dormitories", 0)
        self.avatar_url: str | None = data.get("avatarUrl")
        self.invested_money_by_users: list = data.get("investedMOneyByUsers", [])

    def get_manager(self) -> str | None:
        return self.managers[0] if len(self.managers) > 0 else None