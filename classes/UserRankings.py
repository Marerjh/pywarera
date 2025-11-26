from classes.UserRanking import UserRanking

class UserRankings:
    def __init__(self, data):
        self.user_wealth = UserRanking(data["userWealth"])
        self.user_level = UserRanking(data["userLevel"])
        self.user_referrals = UserRanking(data["userReferrals"])