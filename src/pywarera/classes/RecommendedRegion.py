class RecommendedRegion:
    def __init__(self, data):
        self.region_id = data.get("regionId")
        self.bonus = data.get("bonus")
        self.deposit_end_at = data.get("depositEndAt")
        self.item_code = data.get("itemCode")
        self.deposit_bonus = data.get("depositBonus")
        self.ethic_deposit_bonus = data.get("ethicDepositBonus")
        self.strategic_bonus = data.get("strategicBonus")
        self.ethic_specialization_bonus = data.get("ethicSpecializationBonus")
        self.tax_percent = data.get("taxPercent")