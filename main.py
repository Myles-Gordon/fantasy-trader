from fantasycalc_api import fetch_player_values, parse_players
from sleeper_api import get_league_id_by_name, get_league, get_rosters, get_users, get_players
from league_builder import build_all_teams, LINEUP
from league_analysis import compute_league_averages, identify_weaknesses, print_weaknesses
from trade_finder import find_trades, print_trade_proposals
from team import Team

# Config
USERNAME = "mwexg"
LEAGUE_NAME = "SCI"
TOP_TRADES = 10 # How many trade proposals to show

print("Fetching player values from FantasyCalc...")
raw_values = fetch_player_values(False, 1, 10, 1)
fantasycalc_players = parse_players(raw_values)

print("Fetching league data from Sleeper...")
league_id = get_league_id_by_name(USERNAME, LEAGUE_NAME)
rosters = get_rosters(league_id)
users = get_users(league_id)
sleeper_players = get_players()

print("Building all teams...")
all_teams = build_all_teams(users, rosters, sleeper_players, fantasycalc_players, LINEUP)

my_team = all_teams.get(USERNAME)
if not my_team:
    raise ValueError(f"Could not find team for '{USERNAME}' in league '{LEAGUE_NAME}'")

# Print my roster 
print(f"\n=== MY TEAM ===\n")
print(my_team)

# League averages & weaknesses 
league_averages = compute_league_averages(all_teams)
weaknesses = identify_weaknesses(my_team, league_averages)
print_weaknesses(weaknesses, league_averages)

# Trade finder
proposals = find_trades(my_team, all_teams, weaknesses, top_n=TOP_TRADES)
print_trade_proposals(proposals)