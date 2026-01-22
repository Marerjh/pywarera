**This package is EXPERIMENTAL, NOT stable and  NOT intended for use in anything other than your own private projects.**

**pywarera** is a simple Python wrapper for the WarEra API. 
It provides high-level classes for working with game models and a low-level `wareraapi` module for making raw API requests.

API documentation is available at https://api2.warera.io/docs/.

License: GNU General Public License v3.0

## Features
- high-level classes to work with API models
- ability to manually send API requests
- caching (x2 - x5 less requests!)
- batching
- delays

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


## How to install
Requires Python 3.10+
```bash 
pip install pywarera
```

## Examples
```python
import pywarera

pywarera.update_api_token("<YOUR_API_TOKEN>")

# Returns country id
country_id = pywarera.get_country_id_by_name("Ukraine")
print(country_id)

# I want to know if Ukraine has a president
government = pywarera.get_government(country_id)

is_there_a_president = government.has_president()

if is_there_a_president:
    president_id = government.president
    print(president_id)

# Let's check the wealth of a random citizen
import random

romania_citizens = pywarera.get_country_citizens_by_name("Romania")
random_citizen = random.choice(romania_citizens)
print(random_citizen.wealth)
```

## Example of a manual API request
```python
from pywarera import wareraapi

wareraapi.update_api_token("<YOUR_API_TOKEN>")

# Regular request, will be cached
user_response = wareraapi.user_get_user_lite(user_id="123456").execute()

# Batched request, will be cached
from pywarera.wareraapi import BatchSession

with BatchSession() as batch:
    batch.add(wareraapi.user_get_user_lite(user_id="123456"))
    batch.add(wareraapi.user_get_user_lite(user_id="7891011"))

print(batch.responses)
```