from models import Player

def map_roster_to_players(team_name, users, roster, sleeper_players, fantasycalc_players):
    owner_id = get_user_id(team_name, users)
    roster_ids = get_roster(owner_id, roster)

    players = []
    for id in roster_ids:
        player = sleeper_players.get(id)
        if not player:
            continue
        nfl_team = player.get("team")
        position = player.get("position")
        name = ""
        if position == "DEF":
            name = player.get("first_name") + " " + player.get("last_name")
        else:
            name = player.get("full_name")
        
        status = player.get("status")
        value = fantasycalc_players.get(name, 0)

        player = Player(name, position, value, status, nfl_team)
        players.append(player)

    return players

'''
Gets user_id from team_name. Potential error if team_name is wrong
'''
def get_user_id(team_name, users):
    for user in users:
        if(team_name == user["display_name"]):
            return user["user_id"]

'''
Converts owner_ids and returns rosters. Potential errors if owner_id doesn't exist
'''
def get_roster(owner_id, rosters):
    for team in rosters:
        if(owner_id == team["owner_id"]):
            return team["players"]