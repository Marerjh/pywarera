from .CountryRankings import CountryRankings
from typing import Optional

class Country:
    def __init__(self, data):
        self.taxes_income: Optional[float] = data.get("taxes", {}).get("income")
        self.taxes_market: Optional[float] = data.get("taxes", {}).get("market")
        self.taxes_self_work: Optional[float] = data.get("taxes", {}).get("selfWork")
        self.id: Optional[str] = data.get("_id")
        self.name: Optional[str] = data.get("name")
        self.code: Optional[str] = data.get("code")
        self.money: Optional[float] = data.get("money")
        self.orgs: Optional[str] = data.get("orgs")
        self.allies: list[str] | None = data.get("allies")
        self.wars_with: list[str] | None = data.get("warsWith")
        self.scheme: Optional[str] = data.get("scheme")
        self.map_accent: Optional[str] = data.get("mapAccent")
        self.__v: int = data["__v"]
        self.resources: dict[str, list[str]] | None = data.get("strategicResources", {}).get("resources")
        self.production_percent: Optional[float] = data.get("strategicResources", {}).get("bonuses", {}).get("productionPercent", 0)
        self.development_percent: Optional[float] = data.get("strategicResources", {}).get("bonuses", {}).get("developmentPercent", 0)
        self.rankings = CountryRankings(data.get("rankings"))
        self.current_battle_order: Optional[str] = data.get("currentBattleOrder")
        self.updated_at: str = data.get("updatedAt")
        self.development: Optional[float] = data.get("development")
        self.discord_url: Optional[str] = data.get("discordUrl")
        self.specialized_item: Optional[str] = data.get("specializedItem")
        self.enemy: Optional[str] = data.get("enemy")
        self.ruling_party: Optional[str] = data.get("rulingParty")

    @property
    def production_bonus(self):
        return self.production_percent / 100

    @property
    def development_bonus(self):
        return self.development_percent / 100