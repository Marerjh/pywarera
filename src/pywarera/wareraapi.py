import math
import logging

import requests
from requests_cache import CachedSession
from requests import RequestException, PreparedRequest, Response
import datetime
import json
import time
from typing import Literal

# Clearing of expired cache
s = CachedSession(use_temp=True)
s.cache.delete(expired=True)

DELAY_SECONDS = 1
BATCH_DELAY = 5
BATCH_LIMIT = 100

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# These two lists should always be synchronized
batched_endpoints = []
batched_payload = []

class WarEraApiException(Exception):
    pass


def send_request(endpoint, data=None, ttl=0) -> dict | list:
    s.cache.delete(expired=True)  # clearing of expired cache every time request is being prepared
    url = f"https://api2.warera.io/trpc{endpoint}"
    params = {"input": json.dumps(data)} if data else None
    logger.info(f"Creating request: {url} with params {params}")
    cached_response = s.cache.get_response(s.cache.create_key(requests.Request(method="GET", url=url, params=params, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36", "Accept": "application/json"}).prepare()), False)
    if cached_response:
        logger.info(f"Found request in cache, no request created")
        return cached_response.json()
    time.sleep(DELAY_SECONDS)
    try:
        r = s.get(
            url,
            expire_after=ttl,
            params=params,
            headers={
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
    logger.error(f"{r.status_code}: {r.reason}")
    raise WarEraApiException(f"{r.status_code}: {r.reason}")


def save_cache_manually(endpoint: str, params: dict, data: dict, ttl: int):
    logger.info(f"Saving cache for endpoint {endpoint}, params {params}, ttl {ttl}")
    # We need that fake response to search for it (or store it) in the cache via requests_cache module
    fake_req = requests.PreparedRequest()
    fake_req.prepare(method="GET",
        url=f"https://api2.warera.io/trpc{endpoint}",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "Accept": "application/json"
        },
        params={"input": json.dumps(params)} if params else None)
    # If already cached and not expired then do nothing
    if s.cache.contains(request=fake_req) and not s.cache.get_response(key=s.cache.create_key(request=fake_req)).is_expired:
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


def send_batch(ttl=600):
    """This method splits and sends batched requests, as well as returns and caches batched responses"""
    batch_limit = BATCH_LIMIT or 9999
    cycle, max_cycle = 0, math.ceil(len(batched_endpoints) / batch_limit)  # How much batches to prepare
    responses = []
    while cycle < max_cycle:
        # /endpoints,endpoint,endpoint?batch=1?input=<payload>
        endpoints_str = "/" + ",".join(ep[1:] for ep, _ in batched_endpoints[cycle * batch_limit:(cycle + 1) * batch_limit])
        # Input of endpoints
        input_payload = {str(i): p for i, p in enumerate(batched_payload[cycle * batch_limit:(cycle + 1) * batch_limit])}
        responses.extend(send_request(f"{endpoints_str}?batch=1", data=input_payload, ttl=ttl))
        if not cycle + 1 == max_cycle:
            cycle += 1
            time.sleep(BATCH_DELAY)
            continue
        break

    # Here we cache every response from a batch in case something will be requested independently
    for index, response in enumerate(responses):
        save_cache_manually(batched_endpoints[index][0], batched_payload[index], response, batched_endpoints[index][1])

    batched_endpoints.clear()
    batched_payload.clear()
    return responses


def add_to_batch(endpoint, payload, ttl):
    # These two lists should always be synchronized
    batched_endpoints.append((endpoint, ttl))
    batched_payload.append(payload)


def clean(dictionary: dict) -> dict:  # This method was made with ChatGPT :( Shame on me
    return {k: v for k, v in dictionary.items() if v not in (None, "")}


def company_get_by_id(company_id: str, do_batch=False) -> dict:
    """Retrieves detailed information about a specific company"""
    payload = {
        "companyId": company_id
    }
    if not do_batch:
        return send_request("/company.getById", payload, ttl=60)["result"]["data"]
    else:
        add_to_batch("/company.getById", payload, ttl=60)

def company_get_companies(user_id: str = None, org_id: str = None, cursor: str = None, per_page: int = 10) -> tuple[list[str], str | None]:
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
    respond = send_request("/company.getCompanies", payload, ttl=60)["result"]["data"]
    return respond["items"], respond.setdefault("nextCursor", None)


def country_get_country_by_id(country_id: str) -> dict:
    """Retrieves detailed information about a specific country"""
    payload = {
        "countryId": country_id
    }
    return send_request("/country.getCountryById", payload, ttl=60)["result"]["data"]


def country_get_all_countries(forced_request=False) -> dict:
    """Retrieves a list of all available countries"""
    return send_request("/country.getAllCountries", ttl=600)["result"]["data"]


def government_get_by_country_id(country_id: str) -> dict:
    """Retrieves government information for a specific country"""
    payload = {
        "countryId": country_id
    }
    return send_request("/government.getByCountryId", payload, ttl=60)["result"]["data"]


def region_get_by_id(region_id: str) -> dict:
    """Retrieves detailed information about a specific region"""
    payload = {
        "regionId": region_id
    }
    return send_request("/region.getById", payload, ttl=3600)["result"]["data"]


def region_get_regions_object(forced_request=False) -> dict:
    """Retrieves a complete object containing all available regions"""
    return send_request("/region.getRegionsObject", ttl=3600)["result"]["data"]


def battle_get_by_id(battle_id: str) -> dict:
    """Retrieves detailed information about a specific battle"""
    payload = {
        "battleId": battle_id
    }
    return send_request("/battle.getById", payload, ttl=60)["result"]["data"]


def battle_get_live_battle_data(battle_id: int, round_number: int = 0) -> dict:
    """Retrieves real-time battle data including current round information"""
    payload = clean({
        "battleId": battle_id,
        "roundNumber": round_number
    })
    return send_request("/battle.getLiveBattleData", payload, ttl=0)["result"]["data"]


def battle_get_battles(is_active: bool = True, limit: int = 10, cursor: str = None, direction: Literal["forward", "backward"] = "forward", filter: Literal["all", "yourCountry", "yourEnemies"] = "all", defender_region_id: str = None, war_id: str = None, country_id: str = None) -> tuple[list[dict], str | None]:
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
    respond = send_request("/battle.getBattles", payload, ttl=60)["result"]["data"]
    return respond["items"], respond.setdefault("nextCursor", None)


def round_get_by_id(round_id: str) -> dict:
    """Retrieves detailed information about a specific battle round"""
    payload = {
        "roundId": round_id
    }
    return send_request("/round.getById", payload, ttl=60)["result"]["data"]


def round_get_last_hits(round_id: str) -> dict:
    """Retrieves the most recent hits/damages in a specific battle round"""
    payload = {
        "roundId": round_id
    }
    return send_request("/round.getLastHits", payload, ttl=5)["result"]["data"]


def battle_ranking_get_ranking(data_type: Literal["damage", "points", "money"], type: Literal["user", "country", "mu"], side: Literal["attacker", "defender"], battle_id: str | None = None, round_id: str | None = None, war_id: str | None = None) -> list[dict]:
    """Retrieves damage, ground, or money rankings for users or countries in battles, rounds, or wars"""
    payload = clean({
        "battleId": battle_id,
        "roundId": round_id,
        "warId": war_id,
        "dataType": data_type,
        "type": type,
        "side": side
    })
    return send_request("/battleRanking.getRanking", payload, ttl=60)["result"]["data"]["rankings"]


def item_trading_get_prices(forced_request=False) -> dict[str, float]:
    """Retrieves current market prices for all tradeable items
    :return: Dict{id of resource: average price of resource}"""
    return send_request("/itemTrading.getPrices", ttl=5)["result"]["data"]


def trading_order_get_top_orders(item_code: str, limit:int = 10) -> tuple[dict, dict]:
    """Retrieves the best orders for an item
    :param limit: Minimum 1, maximum 100. Default 10
    :return: Tuple(buy orders, sell orders)
    """
    limit = min(max(1, limit), 100)
    payload = clean({
        "itemCode": item_code,
        "limit": limit
    })
    respond = send_request("/tradingOrder.getTopOrders", payload, ttl=5)["result"]["data"]
    return respond["buyOrders"], respond["sellOrders"]


def item_offer_get_by_id(item_offer_id: str) -> dict:
    """Retrieves detailed information about a specific item offer"""
    payload = {
        "itemOfferId": item_offer_id
    }
    return send_request("/tradingOrder.getTopOrders", payload, ttl=5)["result"]["data"]


def work_offer_get_by_id(work_offer_id: str) -> dict:
    """Retrieves detailed information about a specific work offer"""
    payload = {
        "workOfferId": work_offer_id
    }
    return send_request("/workOffer.getById", payload, ttl=5)["result"]["data"]


def work_offer_get_work_offer_by_company_id(company_id: str) -> dict:
    """Retrieves work offer for a specific company"""
    payload = {
        "companyId": company_id
    }
    return send_request("/workOffer.getWorkOfferByCompanyId", payload, ttl=5)["result"]["data"]


def work_offer_get_work_offers_paginated(user_id: str = None, region_id: str = None, cursor: str = None, limit: int = 10):
    """Retrieves a paginated list of work offers with optional user and region filtering
    :return: Tuple(list of work offers, next cursor in str or None if not available)"""
    limit = min(max(1, limit), 100)
    payload = clean({
        "userId": user_id,
        "regionId": region_id,
        "cursor": cursor,
        "limit": limit
    })
    respond = send_request("/workOffer.getWorkOffersPaginated", payload, ttl=5)["result"]["data"]
    return respond["items"], respond.setdefault("nextCursor", None)


def ranking_get_rankings(ranking_type: Literal["weeklyCountryDamages","weeklyCountryDamagesPerCitizen","countryRegionDiff","countryDevelopment","countryActivePopulation","countryDamages","countryWealth","countryProductionBonus","weeklyUserDamages","userDamages","userWealth","userLevel","userReferrals","userSubscribers","userTerrain","userPremiumMonths","userPremiumGifts","muWeeklyDamages","muDamages","muTerrain","muWealth"]) -> dict:
    """Retrieves ranking data for the specified ranking type and optional year-week filter"""
    payload = {
        "rankingType": ranking_type
    }
    return send_request("/ranking.getRanking", payload, ttl=1200)["result"]["data"]


def search_anything(search_text: str) -> dict:
    """Performs a global search across users, companies, articles, and other entities"""
    payload = {
        "searchText": search_text
    }
    return send_request("/search.searchText", payload, ttl=600)["result"]["data"]


def game_config_get_dates(forced_request=False) -> dict:
    """Retrieves game-related dates and timings"""
    return send_request("/gameConfig.getDates", ttl=3600)["result"]["data"]


def game_config_get_game_config(forced_request=False) -> dict:
    """Retrieves static game configuration"""
    return send_request("/gameConfig.getGameConfig", ttl=86400)["result"]["data"]


def user_get_user_lite(user_id: str, do_batch=False) -> dict:
    """Retrieves basic public information about a user including username, skills, and rankings"""
    payload = {
        "userId": user_id
    }
    if not do_batch:
        return send_request("/user.getUserLite", payload, ttl=600)["result"]["data"]
    else:
        add_to_batch("/user.getUserLite", payload, ttl=600)


def user_get_users_by_country(country_id: str, limit: int = 10, cursor: str = None) -> tuple[list, str | None]:
    """Retrieves a list of users by country
    :return: Tuple(list of items, next cursor in str or None if not available)"""
    limit = min(max(1, limit), 100)
    payload = clean({
        "countryId": country_id,
        "limit": limit,
        "cursor": cursor
    })
    respond: dict = send_request("/user.getUsersByCountry", payload, ttl=600)["result"]["data"]
    return respond["items"], respond.setdefault("nextCursor", None)


def article_get_article_by_id(article_id: str) -> dict:
    """Retrieves detailed information about a specific article"""
    payload = {
        "articleId": article_id
    }
    return send_request("/article.getArticleById", payload, ttl=3600)["result"]["data"]


def article_get_articles_paginated(type: Literal["weekly", "top", "my", "subscriptions", "last"], limit: int = 10, cursor: str = None, user_id: str = None, categories: list[str] = None, languages: list[str] = None) -> tuple[dict, str | None]:
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
    respond = send_request("/article.getArticlesPaginated", payload, ttl=3600)["result"]["data"]
    return respond["items"], respond.setdefault("nextCursor", None)


def transaction_get_paginated_transactions(limit: int = 10, cursor: str = None, user_id: str = None, mu_id: str = None, country_id: str = None, item_code: str = None, transaction_type: str = None) -> tuple[list, str | None]:
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
    respond = send_request("/transaction.getPaginatedTransactions", payload, ttl=5)["result"]["data"]
    return respond["items"], respond.setdefault("nextCursor", None)


def upgrade_get_upgrade_by_type_and_entity(upgrade_type: Literal["bunker", "base", "storage", "automatedEngine", "breakRoom", "headquarters", "dormitories"], region_id: str = None, company_id: str = None, mu_id: str = None) -> dict:
    """Retrieves upgrade information for a specific upgrade type and entity (region, company, or military unit)"""
    payload = clean({
        "upgradeType": upgrade_type,
        "regionId": region_id,
        "companyId": company_id,
        "muId": mu_id
    })
    return send_request("/upgrade.getUpgradeByTypeAndEntity", payload, ttl=600)["result"]["data"]