from team import Team

LINEUP = {
    "QB": 1,
    "RB": 2,
    "WR": 2,
    "TE": 1,
    "FLEX": 2,
    "K": 1,
    "DEF": 1
}

def build_all_teams(users, rosters, sleeper_players, fantasycalc_players, lineup=LINEUP):
    """
    Builds a Team object for every team in the league.
    Returns a dict of { display_name: Team }
    """
    # Build a quick lookup: owner_id -> display_name
    owner_to_name = {u["user_id"]: u["display_name"] for u in users}

    teams = {}
    for roster in rosters:
        owner_id = roster.get("owner_id")
        if not owner_id:
            continue

        display_name = owner_to_name.get(owner_id, f"Unknown ({owner_id})")
        player_ids = roster.get("players") or []

        players = []
        for pid in player_ids:
            player_data = sleeper_players.get(pid)
            if not player_data:
                continue

            position = player_data.get("position")
            nfl_team = player_data.get("team")
            status = player_data.get("status")

            if position == "DEF":
                name = player_data.get("first_name", "") + " " + player_data.get("last_name", "")
            else:
                name = player_data.get("full_name", "")

            value = fantasycalc_players.get(name, 0)

            from player import Player
            players.append(Player(name, position, value, status, nfl_team))

        teams[display_name] = Team(display_name, players, lineup)

    return teams