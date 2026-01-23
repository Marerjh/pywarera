from .. import core as pywarera
from . import Country

class Region:
    def __init__(self, data):
        self.id: str = data.get("_id")
        self.is_capital: bool = data.get("isCapital")
        self.is_linked_to_capital: bool = data.get("isLinkedToCapital")
        self.country: str = data.get("country")
        self.initial_country: str = data.get("initialCountry")
        self.neighbors: list[str] = data.get("neighbors")
        self.name: str = data.get("name")
        self.main_city: str = data.get("mainCity")
        self.development: float = data.get("development")
        self.country_code: str = data.get("countryCode")
        self.biome: str = data.get("biome")
        self.climate: str = data.get("climate")
        self.resistance: str = data.get("resistance")
        self.deposit: dict = data.get("deposit", {})

    def get_country(self) -> Country:
        return pywarera.get_country(self.country)

    @property
    def deposit_type(self) -> str | None:
        if self.deposit:
            return self.deposit.get("type")
        return None


    @property
    def deposit_production_bonus(self) -> float:
        if self.deposit:
            return self.deposit.get("bonusPercent", 0) / 100
        return 0