from fantasycalc_api import fetch_player_values, parse_players
from sleeper_api import get_user_id, get_leagues, get_league_id_by_name, get_league, get_rosters, get_users, get_players
from player_mapper import map_roster_to_players


raw_values = fetch_player_values(False, 1, 10, 1)
fantasycalc_players = parse_players(raw_values)

username="mwexg"
league_id = get_league_id_by_name("mwexg", "SCI")
#print(league_id)
league = get_league(league_id)
roster = get_rosters(league_id)
sleeper_players = get_players()

#if roster:
  #print(roster)
#print(roster[4])
users = get_users(league_id)
team0 = map_roster_to_players("mwexg", users, roster, sleeper_players, fantasycalc_players)

for item in team0:
    print(item)