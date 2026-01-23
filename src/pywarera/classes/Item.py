from typing import Literal

rarities = Literal["common", "uncommon", "rare", "epic", "legendary", "mythic"]
usages = Literal["helmet", "chest", "boots", "gloves", "pants", "weapon", "case"]
types = Literal["raw", "product", "case", "equipment", "weapon"]

class Item:
    def __init__(self, data):
        self.type: types | None = data.get("type")
        self.code: str | None = data.get("code")
        self.usage: usages | None = data.get("usage")
        self.rarity: rarities | None = data.get("rarity")
        self.production_points: int | None = data.get("productionPoints")
        self.production_needs: dict[str, int] | None = data.get("productionNeeds")
        self.is_deposit: bool | None = data.get("isDeposit")
        self.climates: list[str] | None = data.get("climates")
        self.is_tradable: bool | None = data.get("isTradable")
        self.flat_stats: dict[str, int] | None = data.get("flatStats")
        self.dynamic_stats: dict[str, int] | None = data.get("dynamicStats")
        self.is_consumable: bool | None = data.get("isConsumable")

    def get_required_item_code(self):
        return list(self.production_needs.keys())[0]

    def get_required_item_amount(self):
        return list(self.production_needs.values())[0]