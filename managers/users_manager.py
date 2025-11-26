import time
import json
import wareraapi

def cache(key, value, ttl):
    with open("cache.json", "r+") as f:
        cache = json.load(f)
        cache[key] = (value, time.monotonic() + ttl)
        f.truncate(0)
        json.dump(cache, f)

def read_cache(key):
    with open("cache.json", "r+") as f:
        try:
            cache = json.load(f)
            if key in cache:
                if time.monotonic() < cache[key][1]:
                    return cache[key][0]
                else:
                    cache.pop(key)
                    json.dump(cache, f)
        except json.JSONDecodeError:
            pass
        return False


def get_nickname_by_id(id: str) -> str:
    cached_name = read_cache(id)
    if cached_name:
        return cached_name
    else:
        name = wareraapi.user_get_user_lite(id)["username"]
        cache(id, name, 15)
        return name

print(get_nickname_by_id("68ab62c37bb43c01d17dacc7"))
