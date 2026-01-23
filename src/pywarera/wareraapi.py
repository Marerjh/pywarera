import math
import logging
from enum import Enum

import requests
from requests_cache import CachedSession
from requests import RequestException, PreparedRequest, Response
import datetime
import json
import time
from typing import Literal

# Clearing of expired cache
s = CachedSession("wareraapi_cache", use_temp=True, ignored_parameters=["X-API-KEY"])
s.cache.delete(expired=True)

API_TOKEN = ""

DELAY_SECONDS = 0.25
BATCH_DELAY = 1
BATCH_LIMIT = 100

logger = logging.getLogger(__name__)


class ResponseType(Enum):
    PAGINATED_LIST = "paginated_list"
    REGULAR = "regular"


class EndpointCall:
    def __init__(self, endpoint_path: str, cache_tll: int = 600, response_type: ResponseType = ResponseType.REGULAR, payload: dict = None, ):
        self.endpoint_path: str = endpoint_path
        self.payload: dict = payload
        self.cache_ttl: int = cache_tll
        self.response_type: ResponseType = response_type

    def execute(self) -> dict | tuple[dict, str | None]:
        response = send_request(endpoint=self.endpoint_path, data=self.payload, ttl=self.cache_ttl)["result"].get("data")
        if self.response_type == ResponseType.REGULAR:
            return response
        elif self.response_type == ResponseType.PAGINATED_LIST:
            return response.get("items"), response.get("nextCursor")


class BatchSession:
    def __init__(self, cache_ttl=600):
        self.cache_ttl = cache_ttl
        self.responses = None
        self.batched_endpoints = []
        self.batched_payload = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.responses = self.send_batch(self.cache_ttl)

    def add(self, batched_endpoint: EndpointCall):
        # These two lists should always be synchronized
        self.batched_endpoints.append((batched_endpoint.endpoint_path, batched_endpoint.cache_ttl))
        self.batched_payload.append(batched_endpoint.payload)

    def send_batch(self, ttl=600):
        """This method splits and sends batched requests, as well as returns and caches batched responses"""
        batch_limit = BATCH_LIMIT or 9999
        cycle, max_cycle = 0, math.ceil(len(self.batched_endpoints) / batch_limit)  # How much batches to prepare
        responses = []
        while cycle < max_cycle:
            # /endpoints,endpoint,endpoint?batch=1?input=<payload>
            endpoints_str = "/" + ",".join(
                ep[1:] for ep, _ in self.batched_endpoints[cycle * batch_limit:(cycle + 1) * batch_limit])
            # Input of endpoints
            input_payload = {str(i): p for i, p in
                             enumerate(self.batched_payload[cycle * batch_limit:(cycle + 1) * batch_limit])}
            responses.extend(send_request(f"{endpoints_str}?batch=1", data=input_payload, ttl=ttl))
            if not cycle + 1 == max_cycle:
                cycle += 1
                time.sleep(BATCH_DELAY)
                continue
            break

        # Here we cache every response from a batch in case something will be requested independently
        for index, response in enumerate(responses):
            save_cache_manually(self.batched_endpoints[index][0], self.batched_payload[index], response,
                                self.batched_endpoints[index][1])

        self.batched_endpoints.clear()
        self.batched_payload.clear()
        return responses

class WarEraApiException(Exception):
    pass


def update_api_token(new_api_token):
    global API_TOKEN
    API_TOKEN = new_api_token


def send_request(endpoint, data=None, ttl=0) -> dict | list:
    s.cache.delete(expired=True)  # clearing of expired cache every time request is being prepared
    url = f"https://api2.warera.io/trpc{endpoint}"
    params = {"input": json.dumps(data)} if data else None
    logger.info(f"Creating request: {url} with params {params}")
    cached_response = s.cache.get_response(
        s.cache.create_key(requests.Request(
            method="GET",
            url=url,
            params=params,
            headers={
                "X-API-Key":API_TOKEN,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "Accept": "application/json"
            }
        ).prepare()), False)
    if cached_response:
        logger.info(f"Found request in cache, no request created")
        return cached_response.json()
    time.sleep(DELAY_SECONDS)
    try:
        r = s.get(
            url=url,
            expire_after=ttl,
            params=params,
            headers={
                "X-API-Key": API_TOKEN,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "Accept": "application/json"
            }
        )
    except RequestException as e:
        logger.error("Request failed")
        raise WarEraApiException("Request failed") from e
    try:
        return_data = r.json()
    except (ValueError, json.JSONDecodeError) as e:
        logger.error("Bad JSON in response")
        raise WarEraApiException("Bad JSON in response") from e
    if 200 <= r.status_code <= 299:
        logger.info("Success!")
        return return_data
    elif r.status_code == 429:
        limits_reset = int(r.headers.get('Ratelimit-Reset', 60)) + 1
        logger.warning(f"API returned 429: Too much requests. Retrying in: {limits_reset}")
        time.sleep(limits_reset)
        return send_request(endpoint, data, ttl)
    elif r.status_code == 401 and return_data.get("error", {}).get("message", False) == "API token required":
        logger.error(f"Please specify api-token with wareraapi.update_api_token(<YOUR_TOKEN>)")
    logger.error(f"{r.status_code}: {r.reason}")
    raise WarEraApiException(f"{r.status_code}: {r.reason}")


def save_cache_manually(endpoint: str, params: dict, data: dict, ttl: int):
    logger.info(f"Saving cache for endpoint {endpoint}, params {params}, ttl {ttl}")
    # We need that fake response to search for it (or store it) in the cache via requests_cache module
    fake_req = requests.PreparedRequest()
    fake_req.prepare(
        method="GET",
        url=f"https://api2.warera.io/trpc{endpoint}",
        headers={
            "X-API-Key": API_TOKEN,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "Accept": "application/json"
        },
        params={"input": json.dumps(params)} if params else None
    )
    # If already cached and not expired then do nothing
    if s.cache.contains(request=fake_req):
        logger.info("Tried to create a manual cache from batch, but data is already cached. Terminated")
        return False

    fake_resp = Response()
    fake_resp.status_code = 200
    fake_resp._content = json.dumps(data).encode("utf-8")
    fake_resp.headers["Content-Type"] = "application/json"
    fake_resp.request = fake_req
    fake_resp.url = fake_req.url

    class FakeRaw:
        def __init__(self, url):
            self._request_url = url

    fake_resp.raw = FakeRaw(fake_req.url)

    expire_date = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=ttl)

    s.cache.save_response(response=fake_resp, expires=expire_date)
    logger.info("Succesfully created manual cache")


def clean(dictionary: dict) -> dict:  # This method was made with ChatGPT :( Shame on me
    return {k: v for k, v in dictionary.items() if v not in (None, "")}


def company_get_by_id(company_id: str) -> EndpointCall:
    """Retrieves detailed information about a specific company"""
    payload = {
        "companyId": company_id
    }
    return EndpointCall(endpoint_path="/company.getById", payload=payload)



def company_get_companies(user_id: str = None, org_id: str = None, cursor: str = None, per_page: int = 10) -> EndpointCall:
    """Retrieves a paginated list of companies with optional filtering
    :param user_id: Optional user ID filter
    :param org_id: Optional organization ID filter
    :param cursor: Optional pagination cursor
    :param per_page: Minimum 1, maximum 100. Default 10
    :return: Tuple(list of items, next cursor as str or None if no more pages)
    """
    per_page = min(max(1, per_page), 100)
    payload = clean({
        "userId": user_id,
        "orgId": org_id,
        "cursor": cursor,
        "perPage": per_page
    })
    return EndpointCall(endpoint_path="/company.getCompanies",
                        payload=payload,
                        response_type=ResponseType.PAGINATED_LIST)


def event_get_events_paginated(country_id: str = None, event_types: list[str] = None, cursor: str = None, limit: int = 10) -> EndpointCall:
    """Retrieves a paginated list of events with optional country and event type filters
    :return: Tuple(list of items, next cursor as str or None if no more pages)
    """
    limit = min(max(1, limit), 100)
    payload = clean({
        "countryId": country_id,
        "eventTypes": event_types,
        "cursor": cursor,
        "limit": limit
    })
    return EndpointCall(endpoint_path="/event.getEventsPaginated",
                        payload=payload,
                        cache_tll=60,
                        response_type=ResponseType.PAGINATED_LIST)


def country_get_country_by_id(country_id: str) -> EndpointCall:
    """Retrieves detailed information about a specific country"""
    payload = {
        "countryId": country_id
    }
    return EndpointCall(endpoint_path="/country.getCountryById", payload=payload)


def country_get_all_countries() -> EndpointCall:
    """Retrieves a list of all available countries"""
    return EndpointCall(endpoint_path="/country.getAllCountries")


def government_get_by_country_id(country_id: str) -> EndpointCall:
    """Retrieves government information for a specific country"""
    payload = {
        "countryId": country_id
    }
    return EndpointCall(endpoint_path="/government.getByCountryId", payload=payload)


def region_get_by_id(region_id: str) -> EndpointCall:
    """Retrieves detailed information about a specific region"""
    payload = {
        "regionId": region_id
    }
    return EndpointCall(endpoint_path="/region.getById", payload=payload, cache_tll=3600)


def region_get_regions_object() -> EndpointCall:
    """Retrieves a complete object containing all available regions"""
    return EndpointCall(endpoint_path="/region.getRegionsObject", cache_tll=3600)


def battle_get_by_id(battle_id: str) -> EndpointCall:
    """Retrieves detailed information about a specific battle"""
    payload = {
        "battleId": battle_id
    }
    return EndpointCall(endpoint_path="/battle.getById", payload=payload, cache_tll=60)


def battle_get_live_battle_data(battle_id: int, round_number: int = 0) -> EndpointCall:
    """Retrieves real-time battle data including current round information"""
    payload = clean({
        "battleId": battle_id,
        "roundNumber": round_number
    })
    return EndpointCall(endpoint_path="/battle.getLiveBattleData", payload=payload, cache_tll=0)


def battle_get_battles(is_active: bool = True,
                       limit: int = 10,
                       cursor: str = None,
                       direction: Literal["forward", "backward"] = "forward",
                       filter: Literal["all", "yourCountry", "yourEnemies"] = "all",
                       defender_region_id: str = None,
                       war_id: str = None,
                       country_id: str = None) -> EndpointCall:
    """Retrieves a list of battles
    :param is_active: Whether to return active battles. Default is True
    :param limit: The limit of battles to get. Minumum 1, maximum 100. Default 10
    :param cursor: Optional pagination cursor
    :param direction: The direction to get the battles. Default is 'forward'
    :param filter: Type of battles. Default is 'all'
    :param defender_region_id: Optional defender region filter
    :param war_id: Optional war filter
    :param country_id: Optional country filter
    :return: Tuple(list of items, next cursor as str or None if no more pages)
    """
    limit = min(max(1, limit), 100)
    payload = clean({
        "isActive": is_active,
        "limit": limit,
        "cursor": cursor,
        "direction": direction,
        "filter": filter,
        "defenderRegionId": defender_region_id,
        "warId": war_id,
        "countryId": country_id
    })
    return EndpointCall(endpoint_path="/battle.getBattles",
                        payload=payload,
                        cache_tll=60,
                        response_type=ResponseType.PAGINATED_LIST)


def round_get_by_id(round_id: str) -> EndpointCall:
    """Retrieves detailed information about a specific battle round"""
    payload = {
        "roundId": round_id
    }
    return EndpointCall(endpoint_path="/round.getById", payload=payload, cache_tll=60)


def round_get_last_hits(round_id: str) -> EndpointCall:
    """Retrieves the most recent hits/damages in a specific battle round"""
    payload = {
        "roundId": round_id
    }
    return EndpointCall(endpoint_path="/round.getLastHits", payload=payload, cache_tll=5)


def battle_ranking_get_ranking(data_type: Literal["damage", "points", "money"],
                               type: Literal["user", "country", "mu"],
                               side: Literal["attacker", "defender"],
                               battle_id: str | None = None,
                               round_id: str | None = None,
                               war_id: str | None = None) -> EndpointCall:
    """Retrieves damage, ground, or money rankings for users or countries in battles, rounds, or wars"""
    payload = clean({
        "battleId": battle_id,
        "roundId": round_id,
        "warId": war_id,
        "dataType": data_type,
        "type": type,
        "side": side
    })
    return EndpointCall(endpoint_path="/battleRanking.getRanking", payload=payload, cache_tll=60)


def item_trading_get_prices(forced_request=False) -> EndpointCall:
    """Retrieves current market prices for all tradeable items
    :return: Dict{id of resource: average price of resource}"""
    return EndpointCall(endpoint_path="/itemTrading.getPrices", cache_tll=60)


def trading_order_get_top_orders(item_code: str, limit:int = 10) -> EndpointCall:
    """Retrieves the best orders for an item
    :param limit: Minimum 1, maximum 100. Default 10
    :return: Tuple(buy orders, sell orders)
    """
    limit = min(max(1, limit), 100)
    payload = clean({
        "itemCode": item_code,
        "limit": limit
    })
    return EndpointCall(endpoint_path="/tradingOrder.getTopOrders", payload=payload, cache_tll=5)


def item_offer_get_by_id(item_offer_id: str) -> EndpointCall:
    """Retrieves detailed information about a specific item offer"""
    payload = {
        "itemOfferId": item_offer_id
    }
    return EndpointCall(endpoint_path="/itemOffer.getById", payload=payload, cache_tll=5)


def work_offer_get_by_id(work_offer_id: str) -> EndpointCall:
    """Retrieves detailed information about a specific work offer"""
    payload = {
        "workOfferId": work_offer_id
    }
    return EndpointCall(endpoint_path="/workOffer.getById", payload=payload)


def work_offer_get_work_offer_by_company_id(company_id: str) -> EndpointCall:
    """Retrieves work offer for a specific company"""
    payload = {
        "companyId": company_id
    }
    return EndpointCall(endpoint_path="/workOffer.getWorkOfferByCompanyId", payload=payload)


def work_offer_get_work_offers_paginated(user_id: str = None, region_id: str = None, cursor: str = None, energy: int = 0, production: int = 0, limit: int = 10):
    """Retrieves a paginated list of work offers with optional user and region filtering
    :return: Tuple(list of work offers, next cursor in str or None if not available)"""
    limit = min(max(1, limit), 100)
    payload = clean({
        "userId": user_id,
        "regionId": region_id,
        "energy": energy,
        "production": production,
        "cursor": cursor,
        "limit": limit
    })
    return EndpointCall(endpoint_path="/workOffer.getWorkOffersPaginated",
                        payload=payload,
                        cache_tll=60,
                        response_type=ResponseType.PAGINATED_LIST)


def ranking_get_ranking(ranking_type: Literal["weeklyCountryDamages","weeklyCountryDamagesPerCitizen","countryRegionDiff","countryDevelopment","countryActivePopulation","countryDamages","countryWealth","countryProductionBonus","weeklyUserDamages","userDamages","userWealth","userLevel","userReferrals","userSubscribers","userTerrain","userPremiumMonths","userPremiumGifts","muWeeklyDamages","muDamages","muTerrain","muWealth"]) -> EndpointCall:
    """Retrieves ranking data for the specified ranking type and optional year-week filter"""
    payload = {
        "rankingType": ranking_type
    }
    return EndpointCall(endpoint_path="/ranking.getRanking", payload=payload, cache_tll=1200)


def search_anything(search_text: str) -> EndpointCall:
    """Performs a global search across users, companies, articles, and other entities"""
    payload = {
        "searchText": search_text
    }
    return EndpointCall(endpoint_path="/search.searchAnything", payload=payload)


def game_config_get_dates(forced_request=False) -> EndpointCall:
    """Retrieves game-related dates and timings"""
    return EndpointCall(endpoint_path="/gameConfig.getDates", cache_tll=3600)


def game_config_get_game_config(forced_request=False) -> EndpointCall:
    """Retrieves static game configuration"""
    return EndpointCall(endpoint_path="/gameConfig.getGameConfig", cache_tll=86400)


def user_get_user_lite(user_id: str) -> EndpointCall:
    """Retrieves basic public information about a user including username, skills, and rankings"""
    payload = {
        "userId": user_id
    }
    return EndpointCall(endpoint_path="/user.getUserLite",
                        payload=payload,
                        response_type=ResponseType.PAGINATED_LIST)


def user_get_users_by_country(country_id: str, limit: int = 10, cursor: str = None) -> EndpointCall:
    """Retrieves a list of users by country
    :return: Tuple(list of items, next cursor in str or None if not available)"""
    limit = min(max(1, limit), 100)
    payload = clean({
        "countryId": country_id,
        "limit": limit,
        "cursor": cursor
    })
    return EndpointCall(endpoint_path="/user.getUsersByCountry",
                        payload=payload,
                        response_type=ResponseType.PAGINATED_LIST)


def article_get_article_by_id(article_id: str) -> EndpointCall:
    """Retrieves detailed information about a specific article"""
    payload = {
        "articleId": article_id
    }
    return EndpointCall(endpoint_path="/article.getArticleById", payload=payload, cache_tll=3600)


def article_get_articles_paginated(type: Literal["weekly", "top", "my", "subscriptions", "last"], limit: int = 10, cursor: str = None, user_id: str = None, categories: list[str] = None, languages: list[str] = None) -> EndpointCall:
    """Retrieves a paginated list of articles"""
    limit = min(max(1, limit), 100)
    payload = clean({
        "type": type,
        "limit": limit,
        "cursor": cursor,
        "userId": user_id,
        "categories": categories,
        "languages": languages
    })
    return EndpointCall(endpoint_path="/article.getArticlesPaginated",
                        payload=payload,
                        cache_tll=3600,
                        response_type=ResponseType.PAGINATED_LIST)


def mu_get_by_id(mu_id: str) -> EndpointCall:
    """Retrieves detailed information about a specific military unit"""
    payload = clean({
        "muId": mu_id,
    })
    return EndpointCall(endpoint_path="/mu.getById", payload=payload)


def mu_get_many_paginated(limit: int = 20, cursor: str = None, user_id: str = None, member_id: str = None, org_id: str = None, search: str = None) -> EndpointCall:
    """Retrieves a paginated list of military units with optional filters"""
    limit = min(max(1, limit), 100)
    payload = clean({
      "limit": limit,
      "cursor": cursor,
      "memberId": member_id,
      "userId": user_id,
      "orgId": org_id,
      "search": search
    })
    return EndpointCall(endpoint_path="/mu.getManyPaginated",
                        payload=payload,
                        response_type=ResponseType.PAGINATED_LIST)


def transaction_get_paginated_transactions(limit: int = 10, cursor: str = None, user_id: str = None, mu_id: str = None, country_id: str = None, item_code: str = None, transaction_type: str = None) -> EndpointCall:
    """Retrieves a paginated list of transactions"""
    limit = min(max(1, limit), 100)
    payload = clean({
        "limit": limit,
        "cursor": cursor,
        "userId": user_id,
        "muId": mu_id,
        "countryId": country_id,
        "itemCode": item_code,
        "transactionType": transaction_type
    })
    return EndpointCall(endpoint_path="/transaction.getPaginatedTransactions",
                        payload=payload,
                        cache_tll=60,
                        response_type=ResponseType.PAGINATED_LIST)


def upgrade_get_upgrade_by_type_and_entity(upgrade_type: Literal["bunker", "base", "storage", "automatedEngine", "breakRoom", "headquarters", "dormitories"], region_id: str = None, company_id: str = None, mu_id: str = None) -> EndpointCall:
    """Retrieves upgrade information for a specific upgrade type and entity (region, company, or military unit)"""
    payload = clean({
        "upgradeType": upgrade_type,
        "regionId": region_id,
        "companyId": company_id,
        "muId": mu_id
    })
    return EndpointCall(endpoint_path="/upgrade.getUpgradeByTypeAndEntity", payload=payload)


def worker_get_workers(user_id: str = None, company_id: str = None) -> EndpointCall:
    """Get workers for a company or user"""
    if user_id is None and company_id is None:
        raise WarEraApiException("No parameters were specified in worker_get_workers()")
    payload = clean({
        "userId": user_id,
        "companyId": company_id
    })
    return EndpointCall(endpoint_path="/worker.getWorkers", payload=payload)


def worker_get_total_workers_count(user_id: str) -> EndpointCall:
    """Get total workers count for a user"""
    payload = clean({
        "userId": user_id
    })
    return EndpointCall(endpoint_path="/worker.getTotalWorkersCount", payload=payload)