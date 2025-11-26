import src.wareraapi as wareraapi
from src.classes.User import User
from src.classes.Country import Country
from src.classes.Company import Company
from src.classes.Government import Government
from typing import Literal
import src.managers.users_manager as users_manager

countries = dict()


def clear_cache():
    wareraapi.s.cache.clear()


def get_government(country_id: str) -> Government:
    return Government(wareraapi.government_get_by_country_id(country_id))


def get_country(country_id: str) -> Country:
    return Country(wareraapi.country_get_country_by_id(country_id))


def get_all_countries(return_list: bool = False) -> list[Country] | dict[str, Country]:
    if return_list:
        return [Country(i) for i in wareraapi.country_get_all_countries()]
    return {i["_id"]: Country(i) for i in wareraapi.country_get_all_countries()}

def get_country_id_by_name(country_name: str) -> str:
    global countries
    if countries:
        for key, value in countries.items():
            if value[0] == country_name:
                return key
    else:
        countries = {i.id: (i.name, i.code) for i in get_all_countries(return_list=True)}
        return get_country_id_by_name(country_name)


def get_all_country_citizens_id(country_id: str) -> list[str]:
    to_return = []
    cursor = ""
    while cursor is not None:
        items, cursor = wareraapi.user_get_users_by_country(country_id, limit=100, cursor=cursor)
        to_return.extend([item["_id"] for item in items])
    return to_return

def get_all_country_citizens(country_id: str) -> list[User]:
    ids = get_all_country_citizens_id(country_id)
    return users_manager.get_users(ids)

def get_country_citizens_ids_by_name(country_name: str) -> list[str]:
    return get_all_country_citizens_id(get_country_id_by_name(country_name))

def get_country_citizens_by_name(country_name: str) -> list[User]:
    ids = get_country_citizens_ids_by_name(country_name)
    return users_manager.get_users(ids)


def get_companies_ids_of_player(user_id: str) -> list[str]:
    to_return = []
    cursor = ""
    while cursor is not None:
        items, cursor = wareraapi.company_get_companies(user_id, per_page=12, cursor=cursor)
        to_return.extend([item for item in items])
    return to_return


def get_all_companies_of_country_citizens(country_id: str) -> list[str]:
    to_return = []
    for i in get_all_country_citizens_id(country_id):
        to_return.extend(get_companies_ids_of_player(i))
    return to_return


def get_company_object(company_id: str | list) -> Company | list[Company]:
    if type(company_id) is list:
        to_return = []
        for id in company_id:
            to_return.append(Company(wareraapi.company_get_by_id(id)))
        return to_return
    else:
        return Company(wareraapi.company_get_by_id(company_id))


def get_users_in_battle_id(battle_id: str, subject: Literal["user", "mu", "country"] = "user") -> tuple[set, set]:
    items_attackers = wareraapi.battle_ranking_get_ranking(type=subject, data_type="damage", battle_id=battle_id, side="attacker")
    items_defenders = wareraapi.battle_ranking_get_ranking(type=subject, data_type="damage", battle_id=battle_id, side="defender")
    items_attackers = set([i[subject] for i in [k for k in items_attackers]] if type(items_attackers) == list else [i[subject] for i in items_attackers])
    items_defenders = set([i[subject] for i in [k for k in items_defenders]] if type(items_defenders) == list else [i[subject] for i in items_defenders])
    return items_attackers, items_defenders



def get_damage_in_battles(battle_id: str | list, side: Literal["attacker", "defender"]):
    if isinstance(battle_id, str):
        data = wareraapi.battle_ranking_get_ranking(type="user", data_type="damage", battle_id=battle_id, side=side)
    else:
        data = []
        for i in battle_id:
            data.append(wareraapi.battle_ranking_get_ranking(type="user", data_type="damage", battle_id=i, side=side))
    to_return = {}
    for i in data:
        if isinstance(data[0], list):  # if 2 or more rounds
            for j in i:
                to_return.setdefault(j["user"], 0)
                to_return[j["user"]] += j["value"]
        else:
            to_return.setdefault(i["user"], 0)
            to_return[i["user"]] += i["value"]
    return to_return
