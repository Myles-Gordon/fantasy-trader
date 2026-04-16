from collections import defaultdict

SCORED_POSITIONS = ["QB", "RB", "WR", "TE"]

def compute_league_averages(teams: dict) -> dict:
    """
    For each position, compute the average starter value across all teams.
    Returns { position: average_value }
    """
    position_totals = defaultdict(float)
    position_counts = defaultdict(int)

    for team in teams.values():
        starters = team.starters()
        by_pos = defaultdict(list)
        for p in starters:
            by_pos[p.position].append(p)

        for pos in SCORED_POSITIONS:
            for player in by_pos.get(pos, []):
                position_totals[pos] += player.value
                position_counts[pos] += 1

    averages = {}
    for pos in SCORED_POSITIONS:
        count = position_counts[pos]
        averages[pos] = position_totals[pos] / count if count else 0

    return averages


def identify_weaknesses(my_team, league_averages: dict) -> list:
    """
    Compares each of my_team's starter positions (+ next bench player) vs league average.
    Returns a list of dicts sorted by how far below average, worst first:
    [
        {
            "position": "RB",
            "my_value": 1200,
            "league_avg": 1600,
            "deficit": 400,
            "starters": [...],
            "next_bench": Player or None
        },
        ...
    ]
    """
    weaknesses = []
    sorted_pos = my_team.sorted_positions()
    starters = my_team.starters()
    starter_set = set(id(p) for p in starters)

    for pos in SCORED_POSITIONS:
        avg = league_averages.get(pos, 0)
        all_at_pos = sorted_pos.get(pos, [])

        # Starters at this position
        my_starters = [p for p in all_at_pos if id(p) in starter_set]
        my_value = sum(p.value for p in my_starters)

        # Scale average to how many starters I have at this position
        num_starters = len(my_starters)
        scaled_avg = avg * num_starters

        # Next bench player at this position
        bench_at_pos = [p for p in all_at_pos if id(p) not in starter_set]
        next_bench = bench_at_pos[0] if bench_at_pos else None

        # Effective value includes next bench player (depth consideration)
        effective_value = my_value + (next_bench.value if next_bench else 0)
        effective_avg = scaled_avg + avg  # one extra bench slot worth of avg

        deficit = effective_avg - effective_value

        weaknesses.append({
            "position": pos,
            "my_starter_value": my_value,
            "my_effective_value": effective_value,
            "league_avg_per_starter": avg,
            "scaled_avg": scaled_avg,
            "effective_avg": effective_avg,
            "deficit": deficit,
            "starters": my_starters,
            "next_bench": next_bench,
        })

    # Sort by deficit descending (biggest weakness first)
    weaknesses.sort(key=lambda x: x["deficit"], reverse=True)
    return weaknesses


def print_weaknesses(weaknesses: list, league_averages: dict):
    print("\n=== POSITION WEAKNESSES (vs League Average) ===\n")
    for w in weaknesses:
        pos = w["position"]
        indicator = "⚠️ " if w["deficit"] > 0 else "✅ "
        print(f"{indicator}{pos}")
        print(f"   Starters: {', '.join(p.name + f' ({p.value})' for p in w['starters']) or 'None'}")
        if w["next_bench"]:
            print(f"   Next bench: {w['next_bench'].name} ({w['next_bench'].value})")
        else:
            print(f"   Next bench: None")
        print(f"   Effective value: {w['my_effective_value']:.0f}  |  League avg (scaled): {w['effective_avg']:.0f}  |  Deficit: {w['deficit']:.0f}")
        print()