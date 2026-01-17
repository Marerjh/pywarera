from .CountryRanking import CountryRanking

class CountryRankings:
    def __init__(self, data):
        self.country_region_diff = CountryRanking(data["countryRegionDiff"])
        self.country_damages = CountryRanking(data["countryDamages"])
        self.weekly_country_damages = CountryRanking(data["weeklyCountryDamages"])
        self.country_development = CountryRanking(data["countryDevelopment"])
        self.country_active_population = CountryRanking(data["countryActivePopulation"])
        self.country_wealth = CountryRanking(data["countryWealth"])
        self.country_production_bonus = CountryRanking(data["countryProductionBonus"])
