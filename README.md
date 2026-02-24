**This package is EXPERIMENTAL, NOT stable and  NOT intended for use in anything other than your own private projects.**

**pywarera** is a simple Python wrapper for the WarEra API. 
It provides high-level classes for working with game models and a low-level `wareraapi` module for making raw API requests.

API documentation is available at https://api2.warera.io/docs/.

License: GNU General Public License v3.0

## Features
- high-level classes to work with API models
- ability to manually send API requests
- caching (x5 - x20 less requests!)
- batching
- delays
- exceptions

## Supported models
- 🟢 the wrapper can reliably reproduce this model from the get request
- 🟡 the wrapper can reproduce most properties, but reliability has not been tested
- 🔴 the wrapper is not yet able to work with this model, so you will have to process the response from the API yourself


- 🟡company
- 🟡country
- 🔴event
- 🟡government
- 🟡region
- 🔴battle
- 🔴round
- 🔴battleRanking
- 🔴itemTrading
- 🔴tradingOrder
- 🔴workOffer
- 🔴ranking
- 🔴search
- 🔴gameConfig
- 🟡user
- 🔴article
- 🟡mu
- 🔴transaction
- 🔴upgrade
- 🟡workers
- 🟡party


## How to install
Requires Python 3.10+
```bash 
pip install pywarera
```

## Examples
```python
import pywarera

s = pywarera.WarEraSession(api_token="xxx")

# Returns country id
country_id = s.get_country_id_by_name("Ukraine")
print(country_id)

# I want to know if Ukraine has a president
government = s.get_government(country_id)

is_there_a_president = government.has_president()

if is_there_a_president:
    president_id = government.president
    print(president_id)

# Let's check the wealth of a random citizen
import random

romania_citizens = s.get_country_citizens_by_name("Romania")
random_citizen = random.choice(romania_citizens)
print(random_citizen.wealth)
```

## Example of a manual API request
```python
from pywarera import wareraapi

api_s = wareraapi.WarEraApiSession(api_token="xxx")

# Regular request, will be cached
user_response = wareraapi.user_get_user_lite(user_id="123456").execute(api_s)

# Batched request, will be cached
from pywarera.wareraapi import BatchSession

with BatchSession(api_s) as batch:
    batch.add(wareraapi.user_get_user_lite(user_id="123456"))
    batch.add(wareraapi.user_get_user_lite(user_id="7891011"))

print(batch.responses)
```
## Functions
### General
- clear_cache()
- update_api_token(new_api_token)

### Region
- get_region(region_id) -> returns instance of Region class

### Items
- get_items() -> access to resources and products
- get_item(item_code)
- get_trading_prices()
- get_item_price(item_code)

### User
- get_user(user_id) -> returns instance of User class
- get_users(user_ids) -> returns list with instances of User class
- get_user_wage(user_id)

### Government
- get_government(country_id) -> returns instance of Government clas

### Country
- get_country(country_id) -> returns instance of Country class
- get_all_countries(return_list: bool) -> returns dict with instances of Country object, where key is country's ID
- get_country_id_by_name(country_name)
- get_country_citizens_ids(country_id)
- get_country_citizens(country_id) -> returns list with instances of User class
- get_country_citizens_ids_by_name(country_name)
- get_country_citizens_by_name(country_name) -> returns list with instances of User class

### Company
- get_user_company_ids(user_id)
- get_users_company_ids(user_ids: list[str])
- get_country_citizens_company_ids(country_id)
- get_company(company_id) -> returns instance of Company class
- get_companies(company_ids: list[str]) -> returns list with instances of Company class
- get_country_citizens_companies(country_id) -> returns list with instances of Company class

### MUs
- get_military_unit(mu_id) -> returns instance of MilitaryUnit class
- get_military_units_from_paginated(items: list) -> to work with mu.getManyPaginated request

### Parties
- get_party(party_id)
- get_parties(party_ids)
