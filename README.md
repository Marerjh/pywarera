License: GNU General Public License v3.0

**pywarera** is a wrapper for WarEra API. 

API documentation is available at https://api2.warera.io/docs/.

## Features
- no need to work with raw API responds
- caching
- batching

## How to install
Requires Python 3.10+
```bash 
pip install pywarera
```

## Examples
```python
import pywarera
import random

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
romania_citizens = pywarera.get_country_citizens_by_name("Romania")
random_citizen = random.choice(romania_citizens)
print(random_citizen.wealth)
```