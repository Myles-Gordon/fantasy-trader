from fantasycalc_api import fetch_player_values, parse_players
from sleeper_api import get_user_id, get_leagues, get_league_id_by_name, get_league, get_rosters, get_users, get_players
from player_mapper import map_roster_to_players
from team import Team


raw_values = fetch_player_values(False, 1, 10, 1)
fantasycalc_players = parse_players(raw_values)

username="mwexg"
league_id = get_league_id_by_name("mwexg", "SCI")
league = get_league(league_id)
roster = get_rosters(league_id)
sleeper_players = get_players()


users = get_users(league_id)
my_roster = map_roster_to_players("mwexg", users, roster, sleeper_players, fantasycalc_players)

LINEUP = {
    "QB": 1,
    "RB": 2,
    "WR": 2,
    "TE": 1,
    "FLEX": 2,
    "K": 1,
    "DEF": 1
}

me = Team("mwexg", my_roster, LINEUP)
t = me.starters()
b = me.bench()
'''for x in t:
    print(x)
print("\n")
for x in b:
    print(x)'''

print(me)
#print(me.total_starter_value())