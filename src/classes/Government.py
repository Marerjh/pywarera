class Government:
    def __init__(self, data):
        self._id: str = data["_id"]
        self.country: str = data["country"]
        self.congress_members: list[str] = data["congressMembers"]
        self.president: str | None = data.get("president", None)
        self.minOfDefense: str | None = data.get("minOfDefense", None)
        self.minOfForeignAffairs: str | None = data.get("minOfForeignAffairs", None)
        self.vicePresident: str | None = data.get("vicePresident", None)
        self.minOfEconomy: str | None = data.get("minOfEconomy", None)

    def have_president(self) -> bool:
        return self.president is not None

    def have_congress(self) -> bool:
        return self.congress_members is not []