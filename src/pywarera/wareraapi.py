import math
import logging
from enum import Enum
import requests

import requests_cache
from requests_cache import CachedSession, OriginalResponse, CachedResponse
from requests import RequestException, Response
import datetime
import json
import time
from typing import Literal, Callable

logger = logging.getLogger(__name__)

RANKING_TYPES = Literal["weeklyCountryDamages", "weeklyCountryDamagesPerCitizen", "countryRegionDiff",
                        "countryDevelopment", "countryActivePopulation", "countryDamages", "countryWealth",
                        "countryProductionBonus", "weeklyUserDamages", "userDamages", "userWealth", "userLevel",
                        "userReferrals", "userSubscribers", "userTerrain", "userPremiumMonths", "userPremiumGifts",
                        "muWeeklyDamages", "muDamages", "muTerrain", "muWealth"]

DELAY_SECONDS: float = 0.25
BATCH_DELAY: float = 0.25
BATCH_LIMIT: int = 100

DEFAULT_CACHE_TTL: int = 600

_already_cached: int = 0


class ResponseType(Enum):
    PAGINATED_LIST = "paginated_list"
    REGULAR = "regular"


class WarEraApiException(Exception):
    pass


class WarEraUnauthorized(WarEraApiException):
    """401"""
    pass


class WarEraNotFound(WarEraApiException):
    """404"""
    pass


class WarEraInternalServerError(WarEraApiException):
    """500"""
    pass


class WarEraBadRequest(WarEraApiException):
    """400"""
    pass


class WarEraServiceUnavailable(WarEraApiException):
    """503"""
    pass


class WarEraForbidden(WarEraApiException):
    """403"""
    pass


class WarEraTooMuchRequests(WarEraApiException):
    """429"""

    def __init__(self, message, retry_after):
        super().__init__(message)
        self.retry_after = retry_after


class WarEraApiSession:
    def __init__(self, api_token: str = None):
        self.api_token = api_token
        self.session = CachedSession("wareraapi_cache", use_temp=True, ignored_parameters=["X-API-KEY"])
        self.session.cache.delete(expired=True)
        logger.warning("Expired cache entries were deleted")

    def update_api_token(self, new_api_token: str) -> None:
        """Updates global API_TOKEN value"""
        if new_api_token and type(new_api_token) is str:
            self.api_token = new_api_token
            return
        logger.error("Bad API_TOKEN were provided by user")
        raise WarEraApiException("Bad API_TOKEN were provided by user")


    def send_request(self, endpoint: str, data: dict | None = None, ttl: int = 0) -> OriginalResponse | CachedResponse:
        """Prepares request to game server, checks if it is cached and sends request if it is not"""
        url = f"https://api2.warera.io/trpc{endpoint}"
        params = {"input": json.dumps(data)} if data else None
        request = requests_cache.Request(
                method="GET",
                url=url,
                params=params,
                headers={
                    "X-API-Key": self.api_token,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                    "Accept": "application/json"
                }
            ).prepare()
        cache_key = self.session.cache.create_key(request)
        cached_response = self.session.cache.get_response(cache_key)
        if cached_response and not cached_response.is_expired:
            return cached_response
        time.sleep(DELAY_SECONDS)

        try:
            r = self.session.send(request, expire_after=ttl)
            time_elapsed = r.elapsed.total_seconds() * 1000
            if time_elapsed > 70:
                logger.warning("Request took more than expected (%s ms. > 70 ms)", round(time_elapsed, 1))
            logger.debug("Request took %s ms.", time_elapsed)
        except RequestException as e:
            logger.error("RequestException. Request failed, probably due to network error", e)
            raise WarEraApiException("RequestException. Request failed, probably due to network error") from e

        try:
            return self._handle_response_codes(r, endpoint, data)
        except WarEraTooMuchRequests as e:
            if self.api_token is None:
                logger.warning("Consider adding API_TOKEN with wareraapi.update_token(). You're limited to 100 requests/min "
                               "right now")
            time.sleep(e.retry_after)
            return self.send_request(endpoint, data, ttl)


    def _codes_handler_helper(self, response: OriginalResponse, log_method: Callable, logger_message: str, exception_message: str, exception: type[WarEraApiException], *args, **kwargs) -> None:
        """Helper function to handle request's response codes.
        This one is for exceptions. It logs exception and prepares exception message"""
        log_method(logger_message)

        try:
            msg = response.json().get('error', {}).get('message')
        except requests.JSONDecodeError:
            msg = None

        if not msg:
            msg = f"The server didn't provide a reason.\nResponse: {response.text}"

        if exception == WarEraTooMuchRequests:
            raise exception(f"{exception_message}. Reason: {msg}", kwargs["retry_after"])
        else:
            raise exception(f"{exception_message}. Reason: {msg}")


    def _handle_response_codes(self, response: OriginalResponse, endpoint, data) -> OriginalResponse | None:
        """Function to handle request's response codes

        :return: Response if code is 2xx, calls helper function to raise custom Exception otherwise"""
        match response.status_code:
            case code if 200 <= code <= 299:
                logger.debug("Successful request, returning response")
                return response
            case 503:
                self._codes_handler_helper(response,
                                      logger.critical,
                                      "Server returned 503: Service Unavailable. Server mad be down or overloaded, try again later",
                                      "Server returned 503: Service Unavailable",
                                      WarEraServiceUnavailable)
            case 500:
                self._codes_handler_helper(response,
                                      logger.error,
                                      "Server returned 500: Internal Server Error | endpoint = {} | payload = {} | response = {}".format(endpoint, data, response.text),
                                      "Server returned 500: Internal Server Error",
                                      WarEraInternalServerError)
            case 429:
                limits_reset = int(response.headers.get('Ratelimit-Reset', 60)) + 1
                self._codes_handler_helper(response,
                                      logger.warning,
                                      "Server returned 429: Too much requests. Retrying in: {} s".format(limits_reset),
                                      "Server returned 429: Too much requests. Retrying in: {} s".format(limits_reset),
                                      WarEraTooMuchRequests,
                                      retry_after=limits_reset)
            case 404:
                self._codes_handler_helper(response,
                                      logger.error,
                                      "Server returned 404: Not Found | endpoint = {} | payload = {} \
                                      | response = {} | possible causes: invalid input, non-existent resource, or wrong \
                                      endpoint".format(endpoint, data, response.text),
                                      "Server returned 404: Not Found",
                                      WarEraNotFound)
            case 403:
                self._codes_handler_helper(response,
                                      logger.error,
                                      "Server returned 403: Forbidden | endpoint = {} | payload = {}".format(endpoint, data),
                                      "Server returned 403: Forbidden. You don't have access to requested data",
                                      WarEraForbidden)
            case 401:
                data = response.json().get("error", {}).get("data", {})
                if data.get("code") == "UNAUTHORIZED":
                    logger.error(f"Server returned 401: UNAUTHORIZED")
                    raise WarEraUnauthorized(f"{response.status_code}: UNAUTHORIZED, check if API_TOKEN is valid or \
                                            set your API_TOKEN with wareraapi.update_api_token(<YOUR_TOKEN>)")
                try:
                    msg = response.json().get('error').get('message')
                except (ValueError, AttributeError):
                    msg = f"The server didn't provide a reason.\nRespond: {response.text}"
                raise WarEraUnauthorized(f"{response.status_code}: {msg}")
            case 400:
                self._codes_handler_helper(response,
                                      logger.error,
                                      "Server returned 400: Bad Request | endpoint = {} | payload = {} | respond = {}".format(endpoint, data, response.text),
                                      "Server returned 400: Bad Request",
                                      WarEraBadRequest)
                logger.error("Server returned 400: Bad Request | endpoint = {} | payload = {} | respond = {}", endpoint, data, response.text)
            case _:
                logger.error(f"{response.status_code}: {response.reason}")
                raise WarEraApiException(f"{response.status_code}: {response.reason}")

class EndpointCall:
    def __init__(self, endpoint_path: str, cache_tll: int = DEFAULT_CACHE_TTL, response_type: ResponseType = ResponseType.REGULAR, payload: dict = None, ):
        self.endpoint_path: str = endpoint_path
        self.payload: dict = payload
        self.cache_ttl: int = cache_tll
        self.response_type: ResponseType = response_type

    def execute(self, session: WarEraApiSession) -> dict | tuple[dict, (str | None)]:
        """Executes request and returns data (or items)"""
        response = session.send_request(endpoint=self.endpoint_path, data=self.payload, ttl=self.cache_ttl)
        try:
            data = response.json().get("result", {}).get("data")
        except AttributeError as e:
            logger.error("API responded with weird data | response = {}".format(response.text))
            raise WarEraApiException("API responded with weird data | endpoint = {} | data = {} | response = {}".format(self.endpoint_path, self.payload, response.text)) from e
        if self.response_type == ResponseType.REGULAR:
            return data
        elif self.response_type == ResponseType.PAGINATED_LIST:
            return data.get("items"), data.get("nextCursor")


class BatchSession:
    def __init__(self, session: WarEraApiSession, cache_ttl=DEFAULT_CACHE_TTL):
        self.cache_ttl = cache_ttl
        self.responses = None
        self.batched_endpoints = []
        self.batched_payload = []
        self.session = session

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.responses = self.send_batch(self.cache_ttl)

    def add(self, batched_endpoint: EndpointCall) -> None:
        """This method adds instance of EndpointCall to batch, to be worked on later"""
        # These two lists should always be synchronized
        self.batched_endpoints.append((batched_endpoint.endpoint_path, batched_endpoint.cache_ttl))
        self.batched_payload.append(batched_endpoint.payload)

    def _prepare_batch(self, ttl: int = DEFAULT_CACHE_TTL) -> list[dict]:
        """This method splits batches into pieces, makes them understandable by game server and sends requests

        :return: list of responses from the server"""
        logger.debug("Preparing BATCH request")
        batch_limit = BATCH_LIMIT or 9999
        cycle, max_cycle = 0, math.ceil(len(self.batched_endpoints) / batch_limit)  # How much batches to prepare
        data = []
        while cycle < max_cycle:
            cycle += 1
            # /endpoints,endpoint,endpoint?batch=1?input=<payload>
            endpoints_str = "/" + ",".join(
                ep[1:] for ep, _ in self.batched_endpoints[(cycle - 1) * batch_limit:cycle * batch_limit])
            # Input of endpoints
            input_payload = {str(i): p for i, p in
                             enumerate(self.batched_payload[(cycle - 1) * batch_limit:cycle * batch_limit])}
            responses: list[dict] = self.session.send_request(f"{endpoints_str}?batch=1", data=input_payload, ttl=ttl).json()
            data.extend(responses)
            time.sleep(BATCH_DELAY)
        return data

    def _cache_endpoints(self, responses: list[dict]) -> None:
        """This method caches every batched endpoint"""
        global _already_cached

        # Here we cache every response from a batch in case something will be requested independently
        logger.debug(f"Starting to cache batched endpoints independently")
        _already_cached = 0
        for index, response in enumerate(responses):
            save_cache_manually(self.batched_endpoints[index][0], self.batched_payload[index], response,
                                self.batched_endpoints[index][1], api_session=self.session)
        logger.info("Finished endpoints caching. Endpoints: %s, were already cached: %s",
                    len(self.batched_endpoints), _already_cached)

    def send_batch(self, ttl: int = DEFAULT_CACHE_TTL) -> list[dict]:
        """This method splits and sends batched requests, as well as returns and caches batched responses"""
        responses = self._prepare_batch(ttl)
        self._cache_endpoints(responses)
        self.batched_endpoints.clear()
        self.batched_payload.clear()
        return responses


def save_cache_manually(endpoint: str, params: dict, data: dict, ttl: int, api_session: WarEraApiSession) -> None:
    """Creates fake request and saves it to local cache"""
    global _already_cached

    # We need that fake response to search for it (or store it) in the cache via requests_cache module
    fake_req = requests_cache.Request(
        method="GET",
        url=f"https://api2.warera.io/trpc{endpoint}",
        headers={
            "X-API-Key": api_session.api_token,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "Accept": "application/json"
        },
        params={"input": json.dumps(params)} if params else None).prepare()

    # If already cached and not expired then do nothing
    cache_key = api_session.session.cache.create_key(fake_req)
    try:
        if not api_session.session.cache.get_response(cache_key).is_expired:
            _already_cached += 1
            return None
    except AttributeError:
        pass

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

    api_session.session.cache.save_response(response=fake_resp, cache_key=cache_key, expires=expire_date)


def _clean(dictionary: dict) -> dict:  # This method was made with ChatGPT :( Shame on me
    """This function removes all input fields that had no values specified"""
    return {k: v for k, v in dictionary.items() if v not in (None, "")}


def company_get_by_id(company_id: str) -> EndpointCall:
    """Retrieves detailed information about a specific company
    
    :return: instance of EndpointCall that could be either executed or added to batch"""
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
    payload = _clean({
        "userId": user_id,
        "orgId": org_id,
        "cursor": cursor,
        "perPage": per_page
    })
    return EndpointCall(endpoint_path="/company.getCompanies",
                        payload=payload,
                        response_type=ResponseType.PAGINATED_LIST)


def company_get_recommended_region_ids(company_id: str, include_deposit: bool = True) -> EndpointCall:
    payload = _clean({
        "companyId": company_id,
        "includeDeposit": include_deposit
    })
    return EndpointCall(endpoint_path="/company.getRecommendedRegionIds", payload=payload)


def event_get_events_paginated(country_id: str = None, event_types: list[str] = None, cursor: str = None, limit: int = 10) -> EndpointCall:
    """Retrieves a paginated list of events with optional country and event type filters
    :return: Tuple(list of items, next cursor as str or None if no more pages)
    """
    limit = min(max(1, limit), 100)
    payload = _clean({
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
    """Retrieves government information for a specific country
    
    :return: instance of EndpointCall that could be either executed or added to batch"""
    payload = {
        "countryId": country_id
    }
    return EndpointCall(endpoint_path="/government.getByCountryId", payload=payload)


def region_get_by_id(region_id: str) -> EndpointCall:
    """Retrieves detailed information about a specific region
    
    :return: instance of EndpointCall that could be either executed or added to batch"""
    payload = {
        "regionId": region_id
    }
    return EndpointCall(endpoint_path="/region.getById", payload=payload, cache_tll=3600)


def region_get_regions_object() -> EndpointCall:
    """Retrieves a complete object containing all available regions
    
    :return: instance of EndpointCall that could be either executed or added to batch"""
    return EndpointCall(endpoint_path="/region.getRegionsObject", cache_tll=3600)


def battle_get_by_id(battle_id: str) -> EndpointCall:
    """Retrieves detailed information about a specific battle
    
    :return: instance of EndpointCall that could be either executed or added to batch"""
    payload = {
        "battleId": battle_id
    }
    return EndpointCall(endpoint_path="/battle.getById", payload=payload, cache_tll=60)


def battle_get_live_battle_data(battle_id: int, round_number: int = 0) -> EndpointCall:
    """Retrieves real-time battle data including current round information
    
    :return: instance of EndpointCall that could be either executed or added to batch"""
    payload = _clean({
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
    :param limit: The limit of battles to get. Minimum 1, maximum 100. Default 10
    :param cursor: Optional pagination cursor
    :param direction: The direction to get the battles. Default is 'forward'
    :param filter: Type of battles. Default is 'all'
    :param defender_region_id: Optional defender region filter
    :param war_id: Optional war filter
    :param country_id: Optional country filter
    :return: Tuple(list of items, next cursor as str or None if no more pages)
    """
    limit = min(max(1, limit), 100)
    payload = _clean({
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
    payload = _clean({
        "battleId": battle_id,
        "roundId": round_id,
        "warId": war_id,
        "dataType": data_type,
        "type": type,
        "side": side
    })
    return EndpointCall(endpoint_path="/battleRanking.getRanking", payload=payload, cache_tll=60)


def item_trading_get_prices() -> EndpointCall:
    """Retrieves current market prices for all tradeable items
    :return: Dict{id of resource: average price of resource}"""
    return EndpointCall(endpoint_path="/itemTrading.getPrices", cache_tll=60)


def trading_order_get_top_orders(item_code: str, limit: int = 10) -> EndpointCall:
    """Retrieves the best orders for an item
    :param limit: Minimum 1, maximum 100. Default 10
    :return: Tuple(buy orders, sell orders)
    """
    limit = min(max(1, limit), 100)
    payload = _clean({
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
    payload = _clean({
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


def ranking_get_ranking(ranking_type: RANKING_TYPES) -> EndpointCall:
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


def game_config_get_dates() -> EndpointCall:
    """Retrieves game-related dates and timings"""
    return EndpointCall(endpoint_path="/gameConfig.getDates", cache_tll=3600)


def game_config_get_game_config() -> EndpointCall:
    """Retrieves static game configuration"""
    return EndpointCall(endpoint_path="/gameConfig.getGameConfig", cache_tll=86400)


def user_get_user_lite(user_id: str) -> EndpointCall:
    """Retrieves basic public information about a user including username, skills, and rankings"""
    payload = {
        "userId": user_id
    }
    return EndpointCall(endpoint_path="/user.getUserLite",
                        payload=payload,
                        response_type=ResponseType.REGULAR)


def user_get_users_by_country(country_id: str, limit: int = 10, cursor: str = None) -> EndpointCall:
    """Retrieves a list of users by country
    :return: Tuple(list of items, next cursor in str or None if not available)"""
    limit = min(max(1, limit), 100)
    payload = _clean({
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
    payload = _clean({
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
    payload = _clean({
        "muId": mu_id,
    })
    return EndpointCall(endpoint_path="/mu.getById", payload=payload)


def mu_get_many_paginated(limit: int = 20, cursor: str = None, user_id: str = None, member_id: str = None, org_id: str = None, search: str = None) -> EndpointCall:
    """Retrieves a paginated list of military units with optional filters"""
    limit = min(max(1, limit), 100)
    payload = _clean({
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
    payload = _clean({
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
    payload = _clean({
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
    payload = _clean({
        "userId": user_id,
        "companyId": company_id
    })
    return EndpointCall(endpoint_path="/worker.getWorkers", payload=payload)


def worker_get_total_workers_count(user_id: str) -> EndpointCall:
    """Get total workers count for a user"""
    payload = _clean({
        "userId": user_id
    })
    return EndpointCall(endpoint_path="/worker.getTotalWorkersCount", payload=payload)


def party_get_by_id(party_id: str) -> EndpointCall:
    payload = _clean({
        "partyId": party_id
    })
    return EndpointCall(endpoint_path="/party.getById", payload=payload)


def party_get_many_paginated(country_id: str = "", limit: int = 10, cursor = None) -> EndpointCall:
    limit = min(max(1, limit), 100)
    payload = _clean({
        "limit": limit,
        "countryId": country_id,
        "cursor": cursor
    })
    return EndpointCall(endpoint_path="/party.getManyPaginated", payload=payload, response_type=ResponseType.PAGINATED_LIST)