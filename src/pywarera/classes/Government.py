class Government:
    def __init__(self, data):
        self._id: str = data["_id"]
        self.country: str = data["country"]
        self.congress_members: list[str] = data["congressMembers"]
        self.president: str | None = data.get("president")
        self.min_of_defense: str | None = data.get("minOfDefense")
        self.min_of_foreign_affairs: str | None = data.get("minOfForeignAffairs")
        self.vice_president: str | None = data.get("vicePresident")
        self.min_of_economy: str | None = data.get("minOfEconomy")

    def has_president(self) -> bool:
        return self.president is not None

    def has_congress(self) -> bool:
        return self.congress_members is not []