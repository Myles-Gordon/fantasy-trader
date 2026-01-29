from models import Player

def map_roster_to_players(roster, sleeper_players, fantasycalc_players):
    players = []
    print(roster)
    for id in roster:
        player = sleeper_players.get(id)
        team = player.get("team")
        position = player.get("position")
        name = ""
        if position == "DEF":
            name = player.get("first_name") + " " + player.get("last_name")
        else:
            name = player.get("full_name")
        
        status = player.get("status")
        value = fantasycalc_players.get(name, 0)

        player = Player(name, position, value, status, team)
        players.append(player)

    return players