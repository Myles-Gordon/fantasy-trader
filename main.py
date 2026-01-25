from fantasycalc_api import fetch_player_values, parse_players
from sleeper_api import get_user_id, get_leagues, get_league_id_by_name, get_league, get_rosters, get_users

raw = fetch_player_values()
players = parse_players(raw)

username="mwexg"
league_id = get_league_id_by_name("mwexg", "Sci")
league = get_league(league_id)
roster = get_rosters(league_id)


if roster:
  print(roster)

print(players[0])