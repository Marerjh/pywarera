import logging

from . import wareraapi
from .classes.User import User
from .classes.Country import Country
from .classes.Company import Company
from .classes.Government import Government
from .classes.MilitaryUnit import MilitaryUnit
from .classes.ItemPrices import ItemPrices
from .classes.Region import Region
from .classes.GameConfig import GameConfig
from .classes.Item import Item
from .classes.WorkersPerCompany import WorkersPerCompany
from .classes.RecommendedRegion import RecommendedRegion
from .classes.Party import Party
from .wareraapi import BatchSession, WarEraApiSession


countries_id_to_names = dict()
countries = dict()

logger = logging.getLogger(__name__)


class WarEraSession:
    def __init__(self, api_token: str):
        self.api_session: WarEraApiSession = WarEraApiSession(api_token=api_token)

    def clear_cache(self) -> None:
        self.api_session.session.cache.clear()

    def get_company_recommended_regions(self, company_id: str, include_deposit: bool = True) -> list[RecommendedRegion]:
        results = wareraapi.company_get_recommended_region_ids(company_id=company_id, include_deposit=include_deposit).execute(self.api_session)
        return [RecommendedRegion(data) for data in results]

    def get_workers_per_company(self, company_id: str) -> WorkersPerCompany:
        return WorkersPerCompany(wareraapi.worker_get_workers(company_id=company_id).execute(self.api_session))

    def get_user_workers_per_company(self, user_id: str) -> WorkersPerCompany:
        return WorkersPerCompany(wareraapi.worker_get_workers(user_id=user_id).execute(self.api_session))

    def get_items(self):
        return GameConfig(wareraapi.game_config_get_game_config().execute(self.api_session)).items

    def get_item(self, item_code: str) -> Item:
        return self.get_items().get_item_by_code(item_code)

    def get_user_wage(self, user_id, cursor=None):
        logger.debug("User wage were requested, searching for wage transaction")
        wage = 0
        wage_transactions = wareraapi.transaction_get_paginated_transactions(limit=20, user_id=user_id, transaction_type="wage", cursor=cursor).execute(self.api_session)
        if len(wage_transactions[0]) > 0:
            for transaction in wage_transactions[0]:
                if transaction["sellerId"] == user_id:
                    wage = transaction["money"] / transaction["quantity"]
            if wage == 0:
                wage = self.get_user_wage(user_id, wage_transactions[1])
        return wage

    def get_trading_prices(self) -> ItemPrices:
        return ItemPrices(wareraapi.item_trading_get_prices().execute(self.api_session))

    def get_item_price(self, item_code: str) -> float:
        return self.get_trading_prices().get_price_by_code(item_code)

    def get_region(self, region_id: str) -> Region:
        return Region(wareraapi.region_get_regions_object().execute(self.api_session)[region_id])

    def get_user(self, user_id: str) -> User:
        return User(wareraapi.user_get_user_lite(user_id).execute(self.api_session))

    def get_users(self, users_ids: list[str]) -> list[User]:
        with BatchSession(self.api_session) as batch:
            for user_id in users_ids:
                batch.add(wareraapi.user_get_user_lite(user_id))
        return [User(user_data["result"]["data"]) for user_data in batch.responses]

    def get_government(self, country_id: str) -> Government:
        return Government(wareraapi.government_get_by_country_id(country_id).execute(self.api_session))

    def get_country(self, country_id: str) -> Country:
        global countries
        if not countries:
            self.get_all_countries()
        return countries[country_id]

    def get_all_countries(self, return_list: bool = False) -> list[Country] | dict[str, Country]:
        global countries
        response = wareraapi.country_get_all_countries().execute(self.api_session)
        countries = {i["_id"]: Country(i) for i in response}
        if return_list:
            return [Country(i) for i in response]
        return countries


    def get_country_id_by_name(self, country_name: str) -> str:
        global countries_id_to_names
        if countries_id_to_names:
            for key, value in countries_id_to_names.items():
                if value[0] == country_name:
                    return key
        else:
            countries_id_to_names = {i.id: (i.name, i.code) for i in self.get_all_countries(return_list=True)}
            return self.get_country_id_by_name(country_name)

    def get_country_citizens_ids(self, country_id: str) -> list[str]:
        to_return = []
        cursor = ""
        while cursor is not None:
            items, cursor = wareraapi.user_get_users_by_country(country_id, limit=100, cursor=cursor).execute(self.api_session)
            to_return.extend([item["_id"] for item in items])
        return to_return

    def get_country_citizens(self, country_id: str) -> list[User]:
        ids = self.get_country_citizens_ids(country_id)
        return self.get_users(ids)

    def get_country_citizen_ids_by_name(self, country_name: str) -> list[str]:
        return self.get_country_citizens_ids(self.get_country_id_by_name(country_name))

    def get_country_citizens_by_name(self, country_name: str) -> list[User]:
        ids = self.get_country_citizen_ids_by_name(country_name)
        return self.get_users(ids)

    def get_user_company_ids(self, user_id: str) -> list[str]:
        return wareraapi.company_get_companies(user_id, per_page=15).execute(self.api_session)[0]  # 15 just to be sure that exceeding companies will be inclided

    def get_users_company_ids(self, user_ids: list[str]) -> list[str]:
        to_return = []
        with BatchSession(self.api_session) as batch:
            for user_id in user_ids:
                batch.add(wareraapi.company_get_companies(user_id, per_page=15)) # 15 just to be sure that exceeding companies will be inclided
        for response in batch.responses:
            try:
                to_return.extend(response["result"]["data"]["items"])
            except KeyError as e:
                logger.warning("Got KeyError when working with get_companies_ids_of_players. Broken request?")
                logger.warning(f"{e}")
                pass
        return to_return

    def get_country_citizens_company_ids(self, country_id: str) -> list[str]:
        return self.get_users_company_ids(self.get_country_citizens_ids(country_id))

    def get_company(self, company_id: str) -> Company:
        return Company(wareraapi.company_get_by_id(company_id).execute(self.api_session))

    def get_companies(self, company_ids: list[str]) -> list[Company]:
        with BatchSession(self.api_session) as batch:
            for company_id in company_ids:
                batch.add(wareraapi.company_get_by_id(company_id))
        return [Company(response["result"]["data"]) for response in batch.responses]

    def get_country_citizens_companies(self, country_id: str) -> list[Company]:
        company_ids = self.get_country_citizens_company_ids(country_id)
        return self.get_companies(company_ids)

    def get_user_companies(self, user_id: str) -> list[Company]:
        company_ids = self.get_user_company_ids(user_id)
        return self.get_companies(company_ids)

    def get_military_unit(self, mu_id: str) -> MilitaryUnit:
        return MilitaryUnit(wareraapi.mu_get_by_id(mu_id).execute(self.api_session))

    def get_military_units_from_paginated(self, items: list) -> tuple[MilitaryUnit]:
        to_return = []
        for mu_data in items:
            to_return.append(MilitaryUnit(mu_data))
        return tuple(to_return)

    def get_party(self, party_id: str) -> Party:
        return Party(wareraapi.party_get_by_id(party_id).execute(self.api_session))

    def get_parties(self, party_ids: list[str]) -> list[Party]:
        with BatchSession(self.api_session) as batch:
            for party_id in party_ids:
                batch.add(wareraapi.party_get_by_id(party_id))
        return [Party(response["result"]["data"]) for response in batch.responses]