from ItemsConfig import ItemsConfig

class GameConfig:
    def __init__(self, data):
        self.user = None
        self.skills = None
        self.battle = None
        self.org = None
        self.company = None
        self.worker = None
        self.mu = None
        self.law = None
        self.election = None
        self.badge = None
        self.merging_cost = None
        self.upgrades_config = None
        self.items = data.get("items")
        self.referral = None
        self.region = None
        self.newspaper = None
        self.country = None
        self.citizenship_application = None
        self.government = None
        self.mission = None

