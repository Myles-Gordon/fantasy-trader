from collections import defaultdict

SCORED_POSITIONS = ["QB", "RB", "WR", "TE"]

def compute_league_averages(teams: dict) -> dict:
    """
    For each position, compute the average starter value across all teams.
    Also computes average FLEX starter value.
    Returns { position: average_value, "FLEX": average_flex_value }
    """
    position_totals = defaultdict(float)
    position_counts = defaultdict(int)
    flex_totals = 0.0
    flex_counts = 0

    for team in teams.values():
        starters = team.starters()
        lineup = team.lineup
        by_pos = defaultdict(list)
        for p in starters:
            by_pos[p.position].append(p)

        for pos in SCORED_POSITIONS:
            for player in by_pos.get(pos, []):
                position_totals[pos] += player.value
                position_counts[pos] += 1

        # FLEX starters: players beyond the named position counts
        flex_count = lineup.get("FLEX", 0)
        if flex_count > 0:
            rb_starters = lineup.get("RB", 0)
            wr_starters = lineup.get("WR", 0)
            te_starters = lineup.get("TE", 0)

            flex_candidates = (
                sorted(by_pos.get("RB", []), key=lambda p: p.value, reverse=True)[rb_starters:] +
                sorted(by_pos.get("WR", []), key=lambda p: p.value, reverse=True)[wr_starters:] +
                sorted(by_pos.get("TE", []), key=lambda p: p.value, reverse=True)[te_starters:]
            )
            flex_candidates.sort(key=lambda p: p.value, reverse=True)
            for p in flex_candidates[:flex_count]:
                flex_totals += p.value
                flex_counts += 1

    averages = {}
    for pos in SCORED_POSITIONS:
        count = position_counts[pos]
        averages[pos] = position_totals[pos] / count if count else 0

    averages["FLEX"] = flex_totals / flex_counts if flex_counts else 0

    return averages


def identify_weaknesses(my_team, league_averages: dict) -> list:
    """
    Compares each of my_team's starter value per position vs league average.
    Deficit is based purely on starter value vs scaled league average — this
    determines whether a team is weak or has surplus at a position for trade logic.

    Next bench player is tracked separately for display and depth context only.
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

        # Deficit based on starter value only — used for surplus/weakness classification
        deficit = scaled_avg - my_value

        # Next bench player tracked for display and depth context
        bench_at_pos = [p for p in all_at_pos if id(p) not in starter_set]
        next_bench = bench_at_pos[0] if bench_at_pos else None

        # Effective value for display purposes includes bench depth
        effective_value = my_value + (next_bench.value if next_bench else 0)
        effective_avg = scaled_avg + avg

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
        print(f"   Starter value: {w['my_starter_value']:.0f}  |  League avg: {w['scaled_avg']:.0f}  |  Deficit: {w['deficit']:.0f}")
        print(f"   Effective value (w/ bench): {w['my_effective_value']:.0f}")
        print()