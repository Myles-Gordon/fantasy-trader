import requests
from models import Player
from requests_cache import CachedSession

BASE_URL = "https://api.fantasycalc.com/values/current"

session = CachedSession(
    cache_name='cache/fantasycalc_players',
    expire_after=60*60*24
)

def fetch_player_values(is_dynasty=False, num_qbs=1, num_teams=12, ppr=1):
    params = {
        "isDynasty": str(is_dynasty).lower(),
        "numQbs": num_qbs,
        "numTeams": num_teams,
        "ppr": ppr
    }

    response = session.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def parse_players(data):
    players = []

    for p in data:
        players.append(
            Player(
                name=p["player"]["name"],
                position=p["player"]["position"],
                value=p["value"],
                team=p["player"]["maybeTeam"]
            )
            
        )
    return players