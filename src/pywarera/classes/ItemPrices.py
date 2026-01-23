import logging

class ItemPrices:
    def __init__(self, data: dict):
        self.cooked_fish: float = data.get("cookedFish", 0)
        self.heavy_ammo: float = data.get("heavyAmmo", 0)
        self.steel: float = data.get("steel", 0)
        self.bread: float = data.get("bread", 0)
        self.grain: float = data.get("grain", 0)
        self.limestone: float = data.get("limestone", 0)
        self.coca: float = data.get("coca", 0)
        self.concrete: float = data.get("concrete", 0)
        self.oil: float = data.get("oil", 0)
        self.case: float = data.get("case1", 0)
        self.light_ammo: float = data.get("lightAmmo", 0)
        self.steak: float = data.get("steak", 0)
        self.livestock: float = data.get("livestock", 0)
        self.cocain: float = data.get("cocain", 0)
        self.lead: float = data.get("lead", 0)
        self.fish: float = data.get("fish", 0)
        self.petroleum: float = data.get("petroleum", 0)
        self.ammo: float = data.get("ammo", 0)
        self.iron: float = data.get("iron", 0)
        self.scraps: float = data.get("scraps", 0)
        self.elite_case: float = data.get("case2", 0)

    def get_price_by_code(self, code: str) -> float:
        prices = self.to_dict()
        if code in prices.keys():
            return prices[code]
        else:
            logging.warning(f"Wrong item code: {code}, returned 0 as price")
            return 0

    def to_dict(self) -> dict:
        return {
            "cookedFish": self.cooked_fish,
            "heavyAmmo": self.heavy_ammo,
            "steel": self.steel,
            "bread": self.bread,
            "grain": self.grain,
            "limestone": self.limestone,
            "coca": self.coca,
            "concrete": self.concrete,
            "oil": self.oil,
            "case1": self.case,
            "lightAmmo": self.light_ammo,
            "steak": self.steak,
            "livestock": self.livestock,
            "cocain": self.cocain,
            "lead": self.lead,
            "fish": self.fish,
            "petroleum": self.petroleum,
            "ammo": self.ammo,
            "iron": self.iron,
            "scraps": self.scraps,
            "case2": self.elite_case
        }
