def find_similar_players(target_player, my_team, all_teams, tolerance=0.20):
    """
    Find players on other teams whose value is within ±tolerance of target_player.
    Returns list of result dicts sorted by closest value first.
    """
    results = []
    for team_name, team in all_teams.items():
        if team_name == my_team.name:
            continue
        starters = {id(p) for p in team.starters()}
        for player in team.roster:
            if player.value == 0:
                continue
            diff_pct = abs(player.value - target_player.value) / max(target_player.value, 1)
            if diff_pct <= tolerance:
                results.append({
                    "player": player,
                    "team": team_name,
                    "is_starter": id(player) in starters,
                    "value_diff": player.value - target_player.value,
                    "value_diff_pct": diff_pct,
                })
    results.sort(key=lambda x: abs(x["value_diff"]))
    return results


def print_similar_players(target_player, results):
    header = f"PLAYERS SIMILAR TO {target_player.name} ({target_player.position}, {target_player.value})"
    print(f"\n=== {header} ===\n")
    if not results:
        print("  No players found within the value range.\n")
        return
    print(f"  {'Player':<25} {'Pos':<5} {'Value':>7} {'Diff':>7}  {'Role':<8}  Team")
    print("  " + "-" * 65)
    for r in results:
        p    = r["player"]
        role = "Starter" if r["is_starter"] else "Bench"
        diff = f"{r['value_diff']:+.0f}"
        print(f"  {p.name:<25} {p.position:<5} {p.value:>7.0f} {diff:>7}  {role:<8}  {r['team']}")
    print()


def pick_player_from_roster(my_team):
    roster = my_team.team_by_value()
    starters = {id(p) for p in my_team.starters()}
    print(f"\n=== YOUR ROSTER ===\n")
    for i, p in enumerate(roster, 1):
        role = "S" if id(p) in starters else "B"
        print(f"  {i:>2}. [{role}] {p.name:<25} {p.position:<5} {p.value:.0f}")
    print()
    while True:
        raw = input(f"Select a player to trade (1-{len(roster)}): ").strip()
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(roster):
                return roster[idx]
        except ValueError:
            pass
        print(f"  Enter a number between 1 and {len(roster)}.")
