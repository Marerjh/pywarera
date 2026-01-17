from pathlib import Path
from diskcache import Cache
from src.classes.User import User
from src import wareraapi


cache = Cache(f"{Path(__file__).resolve().parents[2] / '.cache'}")

def get_user(user_id: str) -> User:
    user = User(wareraapi.user_get_user_lite(user_id))
    cache_username(user.id, user.username)
    return user

def get_users(users_ids: list[str]) -> list[User]:
    for user_id in users_ids:
        wareraapi.user_get_user_lite(user_id, do_batch=True)
    users = []
    for user_data in wareraapi.send_batch():
        user = User(user_data["result"]["data"])
        users.append(user)
        cache_username(user.id, user.username)
    return users

def cache_username(user_id, username):
    cache.add(user_id, username, expire=86400)

def get_username_by_id(user_id: str) -> str:
    """Retrieves username from cache if available, else sends requests and caches data"""
    return cache.get(user_id) if user_id in cache else get_user(user_id).username

print(get_username_by_id("686171897e2427d535e30814"))
