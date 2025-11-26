class UserRanking:
    def __init__(self, data):
        self.value = data["value"]
        self.rank = data["rank"]
        self.tier = data.get("tier")