from fantasycalc_api import fetch_player_values, parse_players
from sleeper_api import get_leagues, get_rosters, get_users, get_players
from league_builder import build_all_teams, LINEUP
from league_analysis import compute_league_averages, identify_weaknesses, print_weaknesses, print_team_overview
from trade_finder import find_trades, find_package_trades, print_trade_proposals


def prompt(label, default=None, cast=str):
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{label}{suffix}: ").strip()
        if not raw and default is not None:
            return default
        if not raw:
            print("  This field is required.")
            continue
        try:
            return cast(raw)
        except ValueError:
            print(f"  Expected a {cast.__name__}, try again.")


def pick_league(leagues):
    print()
    for i, league in enumerate(leagues, 1):
        print(f"  {i}. {league['name']}")
    while True:
        raw = input(f"\nSelect a league (1-{len(leagues)}): ").strip()
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(leagues):
                return leagues[idx]
        except ValueError:
            pass
        print(f"  Enter a number between 1 and {len(leagues)}.")


print("=" * 50)
print("       Fantasy Football Trade Finder")
print("=" * 50)
print()

# ── User & league selection ───────────────────────────────────────────────────
username = prompt("Sleeper username")

print("\nFetching your leagues...")
leagues = get_leagues(username)
if not leagues:
    raise ValueError(f"No leagues found for '{username}'")

league = pick_league(leagues)
league_id   = league["league_id"]
league_name = league["name"]

# ── Derive settings from league data ─────────────────────────────────────────
num_teams  = league["settings"]["num_teams"]
ppr        = league.get("scoring_settings", {}).get("rec", 1)
is_dynasty = league["settings"].get("type", 0) == 2
num_qbs    = 2 if "SUPER_FLEX" in league.get("roster_positions", []) else 1

top_trades        = prompt("\nHow many trade proposals to show", default=10, cast=int)
fairness_max      = prompt("Max trade value imbalance % (e.g. 10 = within 10%)", default=10, cast=int)
fairness_threshold = fairness_max / 100

# ── Fetch & build ─────────────────────────────────────────────────────────────
print()
print("Fetching player values from FantasyCalc...")
raw_values = fetch_player_values(is_dynasty, num_qbs, num_teams, ppr)
fantasycalc_players = parse_players(raw_values)

print("Fetching league data from Sleeper...")
rosters = get_rosters(league_id)
users = get_users(league_id)
sleeper_players = get_players()

print("Building all teams...")
all_teams = build_all_teams(users, rosters, sleeper_players, fantasycalc_players, LINEUP)

my_team = all_teams.get(username)
if not my_team:
    raise ValueError(f"Could not find team for '{username}' in league '{league_name}'")

# ── Output ────────────────────────────────────────────────────────────────────
print(f"\n=== MY TEAM ===\n")
print(my_team)

league_averages = compute_league_averages(all_teams)
weaknesses = identify_weaknesses(my_team, league_averages)
print_weaknesses(weaknesses, league_averages)

proposals = find_trades(my_team, all_teams, weaknesses, league_averages, top_n=top_trades, fairness_threshold=fairness_threshold)
print_trade_proposals(proposals, header="1-FOR-1 TRADE PROPOSALS", my_team=my_team, all_teams=all_teams)

package_proposals = find_package_trades(my_team, all_teams, weaknesses, league_averages, top_n=top_trades, fairness_threshold=fairness_threshold)
print_trade_proposals(package_proposals, header="PACKAGE TRADE PROPOSALS (2-for-1 / 1-for-2)", my_team=my_team, all_teams=all_teams)

print_team_overview(weaknesses)
