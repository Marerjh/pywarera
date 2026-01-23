from .Item import Item

class ItemsConfig:
    def __init__(self, data):
        self.limestone = Item(data.get("limestone"))
        self.grain = Item(data.get("grain"))
        self.livestock = Item(data.get("livestock"))
        self.fish = Item(data.get("fish"))
        self.iron = Item(data.get("iron"))
        self.coca = Item(data.get("coca"))
        self.mysterious_plant = self.coca
        self.lead = Item(data.get("lead"))
        self.petroleum = Item(data.get("petroleum"))
        self.concrete = Item(data.get("concrete"))
        self.steel = Item(data.get("steel"))
        self.bread = Item(data.get("bread"))
        self.steak = Item(data.get("steak"))
        self.cooked_fish = Item(data.get("cookedFish"))
        self.light_ammo = Item(data.get("lightAmmo"))
        self.ammo = Item(data.get("ammo"))
        self.cocain = Item(data.get("cocain"))
        self.pill = self.cocain
        self.oil = Item(data.get("oil"))
        self.heavy_ammo = Item(data.get("heavyAmmo"))

    def get_item_by_code(self, code: str) -> Item:
        items = self.to_dict()
        if code in items:
            return items[code]

    def to_dict(self) -> dict[str, Item]:
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
            "lightAmmo": self.light_ammo,
            "steak": self.steak,
            "livestock": self.livestock,
            "cocain": self.cocain,
            "lead": self.lead,
            "fish": self.fish,
            "petroleum": self.petroleum,
            "ammo": self.ammo,
            "iron": self.iron,
        }