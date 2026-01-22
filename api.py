import requests

BASE_URL = "https://api.fantasycalc.com/values/current"

def fetch_player_values(is_dynasty=False, num_qbs=1, num_teams=12, ppr=1):
    params = {
        "isDynasty": str(is_dynasty).lower(),
        "numQbs": num_qbs,
        "numTeams": num_teams,
        "ppr": ppr
    }

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()
