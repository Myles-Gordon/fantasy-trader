import requests
from requests_cache import CachedSession

BASE_URL = "https://api.sleeper.app/v1"

'''
Gets user id given sleeper username
'''
def get_user_id(username):
    url = f"{BASE_URL}/user/{username}"
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    return data["user_id"]

'''
Gets all leagues user is in
'''
def get_leagues(username, season=2025):
    user_id = get_user_id(username)
    url = f"{BASE_URL}/user/{user_id}/leagues/nfl/{season}"

    response = requests.get(url)
    response.raise_for_status()
    return response.json()

'''
Gets specific league id given name
'''
def get_league_id_by_name(username, league_name, season=2025):
    leagues = get_leagues(username, season)

    for league in leagues:
        if league["name"] == league_name:
            return league["league_id"]

    raise ValueError(f"League '{league_name}' not found")

'''
Gets specific league given id
'''
def get_league(league_id):
    url = f"{BASE_URL}/league/{league_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

'''
Gets all rosters in a league
'''
def get_rosters(league_id):
    url = f"{BASE_URL}/league/{league_id}/rosters"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

'''
Gets all users in a league
'''
def get_users(league_id):
    url = f"{BASE_URL}/league/{league_id}/users"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

'''
Cache players to reduce API calls
'''
players_url = "https://api.sleeper.app/v1/players/nfl"
session = CachedSession(
  cache_name='cache/sleeper_players',
  expire_after=60*60*24
)
'''
Get players from sleeper api
'''
def get_players():
    response = session.get(players_url)
    response.raise_for_status()
    return response.json()