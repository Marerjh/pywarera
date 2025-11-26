from src.classes.CountryRankings import CountryRankings

class Country:
    def __init__(self, data):
        self.taxes_income: float = data["taxes"]["income"]
        self.taxes_market: float = data["taxes"]["market"]
        self.taxes_self_work: float = data["taxes"]["selfWork"]
        self.id: str = data["_id"]
        self.name: str = data["name"]
        self.code: str = data["code"]
        self.money: float = data["money"]
        self.orgs: str = data["orgs"]
        self.allies: list[str] = data["allies"]
        self.wars_with: list[str] = data["warsWith"]
        self.scheme: str = data["scheme"]
        self.map_accent: str = data["mapAccent"]
        self.__v: int = data["__v"]
        self.rankings = CountryRankings(data["rankings"])
        self.current_battle_order: str | None = data.get("currentBattleOrder", None)
        self.updated_at: str = data["updatedAt"]
        self.enemy: str | None = data.get("enemy", None)