from .CountryRankings import CountryRankings

class Country:
    def __init__(self, data):
        self.taxes_income: float | None = data.get("taxes", {}).get("income")
        self.taxes_market: float | None = data.get("taxes", {}).get("market")
        self.taxes_self_work: float | None = data.get("taxes", {}).get("selfWork")
        self.id: str | None = data.get("_id")
        self.name: str | None = data.get("name")
        self.code: str | None = data.get("code")
        self.money: float | None = data.get("money")
        self.orgs: str | None = data.get("orgs")
        self.allies: list[str] | None = data.get("allies")
        self.wars_with: list[str] | None = data.get("warsWith")
        self.scheme: str | None = data.get("scheme")
        self.map_accent: str | None = data.get("mapAccent")
        self.__v: int = data["__v"]
        self.resources: dict[str, list[str]] | None = data.get("strategicResources", {}).get("resources")
        self.production_percent: float | None = data.get("strategicResources", {}).get("bonuses", {}).get("productionPercent", 0)
        self.development_percent: float | None = data.get("strategicResources", {}).get("bonuses", {}).get("developmentPercent", 0)
        self.rankings = CountryRankings(data.get("rankings"))
        self.current_battle_order: str | None = data.get("currentBattleOrder")
        self.updated_at: str = data.get("updatedAt")
        self.development: float | None = data.get("development")
        self.discord_url: str | None = data.get("discordUrl")
        self.specialized_item: str | None = data.get("specializedItem")
        self.enemy: str | None = data.get("enemy")