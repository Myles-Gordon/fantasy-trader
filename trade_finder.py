from itertools import combinations
from collections import defaultdict
from league_analysis import identify_weaknesses, SCORED_POSITIONS

FAIRNESS_THRESHOLD = 0.10  # 10% value difference tolerance
MAX_SURPLUS_PLAYERS = 3    # Cap per position to limit combinatorial explosion


def _position_map(weaknesses: list) -> dict:
    return {w["position"]: w for w in weaknesses}


def _tradeable_players(team, pos: str, weakness_map: dict) -> list:
    """Players at a surplus position the team can afford to give up."""
    w = weakness_map.get(pos)
    if not w or w["deficit"] > 0:
        return []
    candidates = []
    if w["starters"]:
        candidates.append(min(w["starters"], key=lambda p: p.value))
    if w["next_bench"]:
        candidates.append(w["next_bench"])
    return candidates[:MAX_SURPLUS_PLAYERS]


def _all_tradeable_players(team, weakness_map: dict) -> list:
    candidates = []
    for pos in SCORED_POSITIONS:
        candidates.extend(_tradeable_players(team, pos, weakness_map))
    return candidates


def _upgrades_available(other_team, pos: str, their_weakness_map: dict, min_value: float) -> list:
    """Players on the other team at a surplus position that exceed min_value."""
    w = their_weakness_map.get(pos)
    if not w or w["deficit"] > 0:
        return []
    all_at_pos = other_team.sorted_positions().get(pos, [])
    return [p for p in all_at_pos if p.value > min_value][:MAX_SURPLUS_PLAYERS]


def _all_upgrades_available(other_team, their_weakness_map: dict, min_value: float) -> list:
    candidates = []
    for pos in SCORED_POSITIONS:
        candidates.extend(_upgrades_available(other_team, pos, their_weakness_map, min_value))
    return candidates


def _net_starter_improvement(team, outgoing: list, incoming: list) -> float:
    """
    Net change in total starter value after a trade.
    Removes outgoing by name to avoid object identity issues.
    """
    outgoing_names = {p.name for p in outgoing}
    new_roster = [p for p in team.roster if p.name not in outgoing_names]
    new_roster.extend(incoming)
    new_team = team.__class__(team.name, new_roster, team.lineup)
    return new_team.total_starter_value() - team.total_starter_value()


def _check_flex_degradation(team, outgoing: list, incoming: list, avg_flex_value: float) -> list:
    """
    Simulates the trade and returns a list of FLEX starters in the new lineup
    whose value falls below the league average FLEX value.
    """
    outgoing_names = {p.name for p in outgoing}
    new_roster = [p for p in team.roster if p.name not in outgoing_names]
    new_roster.extend(incoming)
    new_team = team.__class__(team.name, new_roster, team.lineup)

    lineup = team.lineup
    rb_count = lineup.get("RB", 0)
    wr_count = lineup.get("WR", 0)
    te_count = lineup.get("TE", 0)
    flex_count = lineup.get("FLEX", 0)

    if flex_count == 0:
        return []

    by_pos = defaultdict(list)
    for p in new_team.starters():
        by_pos[p.position].append(p)

    # Sort each position by value desc so we can slice off named starters
    for pos in by_pos:
        by_pos[pos].sort(key=lambda p: p.value, reverse=True)

    flex_starters = (
        by_pos.get("RB", [])[rb_count:] +
        by_pos.get("WR", [])[wr_count:] +
        by_pos.get("TE", [])[te_count:]
    )
    flex_starters.sort(key=lambda p: p.value, reverse=True)
    flex_starters = flex_starters[:flex_count]

    return [p for p in flex_starters if p.value < avg_flex_value]


def _fairness_pct(value_sent: float, value_received: float) -> float:
    max_val = max(value_sent, value_received)
    if max_val == 0:
        return float("inf")
    return abs(value_sent - value_received) / max_val


def _dedup_and_trim(proposals: list, top_n: int) -> list:
    proposals.sort(key=lambda x: x["combined_improvement"], reverse=True)
    seen = set()
    deduped = []
    for p in proposals:
        give_names = tuple(sorted(pl.name for pl in p["give"]))
        receive_names = tuple(sorted(pl.name for pl in p["receive"]))
        key = (p["partner"], give_names, receive_names)
        if key not in seen:
            seen.add(key)
            deduped.append(p)
    return deduped[:top_n]


def debug_trade_search(my_team, all_teams: dict, my_weaknesses: list, league_averages: dict):
    """Traces why proposals are or aren't being generated."""
    my_weakness_map = _position_map(my_weaknesses)
    my_weak_positions = [w["position"] for w in my_weaknesses if w["deficit"] > 0]
    my_surplus_positions = [w["position"] for w in my_weaknesses if w["deficit"] <= 0]

    print(f"\n[DEBUG] My weak positions:    {my_weak_positions}")
    print(f"[DEBUG] My surplus positions: {my_surplus_positions}")
    print(f"[DEBUG] My tradeable chips:   {[p.name + '(' + p.position + ')' for p in _all_tradeable_players(my_team, my_weakness_map)]}")

    for team_name, other_team in all_teams.items():
        if team_name == my_team.name:
            continue

        their_weaknesses = identify_weaknesses(other_team, league_averages)
        their_weakness_map = _position_map(their_weaknesses)
        their_weak_positions = [w["position"] for w in their_weaknesses if w["deficit"] > 0]
        their_surplus_positions = [w["position"] for w in their_weaknesses if w["deficit"] <= 0]

        they_have_my_need = [p for p in my_weak_positions if p in their_surplus_positions]
        i_have_their_need = [p for p in their_weak_positions if p in my_surplus_positions]

        if not they_have_my_need and not i_have_their_need:
            continue

        print(f"\n[DEBUG] --- {team_name} ---")
        print(f"  Their weak:    {their_weak_positions}")
        print(f"  Their surplus: {their_surplus_positions}")
        print(f"  They have what I need at: {they_have_my_need}")
        print(f"  I have what they need at: {i_have_their_need}")

        for my_weak_pos in my_weak_positions:
            my_w = my_weakness_map[my_weak_pos]
            my_starters_at_pos = my_w["starters"]
            if not my_starters_at_pos:
                print(f"  [SKIP] No starters at my weak pos {my_weak_pos}")
                continue
            worst_my_starter = min(my_starters_at_pos, key=lambda p: p.value)

            their_w_at_my_weak = their_weakness_map.get(my_weak_pos)
            if not their_w_at_my_weak or their_w_at_my_weak["deficit"] > 0:
                print(f"  [SKIP] {team_name} is also weak at {my_weak_pos}, can't offer upgrade")
                continue

            their_offers = _upgrades_available(other_team, my_weak_pos, their_weakness_map, worst_my_starter.value)
            print(f"  Upgrades they offer at {my_weak_pos} (vs my worst starter val {worst_my_starter.value}): {[p.name + ' ' + str(p.value) for p in their_offers]}")

            my_chips = _all_tradeable_players(my_team, my_weakness_map)
            for give in my_chips:
                for receive in their_offers:
                    if give.position == receive.position:
                        continue
                    fp = _fairness_pct(give.value, receive.value)
                    my_imp = _net_starter_improvement(my_team, [give], [receive])
                    their_imp = _net_starter_improvement(other_team, [receive], [give])
                    print(f"    give={give.name}({give.position},{give.value}) receive={receive.name}({receive.position},{receive.value}) fairness={fp:.2f} my_imp={my_imp:.0f} their_imp={their_imp:.0f}")


def find_trades(my_team, all_teams: dict, my_weaknesses: list, league_averages: dict, top_n: int = 10):
    """Finds 1-for-1 cross-position trades where both teams improve."""
    proposals = []
    my_weakness_map = _position_map(my_weaknesses)
    my_weak_positions = [w["position"] for w in my_weaknesses if w["deficit"] > 0]
    my_chips = _all_tradeable_players(my_team, my_weakness_map)
    avg_flex_value = league_averages.get("FLEX", 0)

    for team_name, other_team in all_teams.items():
        if team_name == my_team.name:
            continue

        their_weaknesses = identify_weaknesses(other_team, league_averages)
        their_weakness_map = _position_map(their_weaknesses)
        their_weak_positions = [w["position"] for w in their_weaknesses if w["deficit"] > 0]

        for my_weak_pos in my_weak_positions:
            my_w = my_weakness_map[my_weak_pos]
            my_starters_at_pos = my_w["starters"]
            if not my_starters_at_pos:
                continue
            worst_my_starter = min(my_starters_at_pos, key=lambda p: p.value)

            their_w_at_my_weak = their_weakness_map.get(my_weak_pos)
            if not their_w_at_my_weak or their_w_at_my_weak["deficit"] > 0:
                continue

            # Find upgrades they can offer at my weak position (they must be surplus there)
            their_offers = _upgrades_available(other_team, my_weak_pos, their_weakness_map, worst_my_starter.value)
            if not their_offers:
                continue

            # I can offer any of my surplus chips regardless of whether they're
            # weak at that position — value fairness is the filter
            for give in my_chips:
                for receive in their_offers:
                    if give.value == 0 or receive.value == 0:
                        continue
                    if give.position == receive.position:
                        continue  # Skip same-position trades
                    fp = _fairness_pct(give.value, receive.value)
                    if fp > FAIRNESS_THRESHOLD:
                        continue

                    my_improvement = _net_starter_improvement(my_team, [give], [receive])
                    if my_improvement <= 0:
                        continue

                    # Must close at least 20% of the deficit at the weak position
                    min_improvement = 0.20 * my_w["deficit"]
                    if my_improvement < min_improvement:
                        continue

                    # Primary check: does their net starter value improve?
                    their_net = _net_starter_improvement(other_team, [receive], [give])

                    # Fallback: does my player upgrade their worst starter at that position?
                    their_pos_improvement = 0
                    their_w_at_give_pos = their_weakness_map.get(give.position)
                    if their_w_at_give_pos and their_w_at_give_pos["deficit"] > 0:
                        their_weak_starters = their_w_at_give_pos["starters"]
                        their_worst = min(their_weak_starters, key=lambda p: p.value) if their_weak_starters else None
                        if their_worst and give.value > their_worst.value:
                            their_pos_improvement = give.value - their_worst.value

                    if their_net <= 0 and their_pos_improvement <= 0:
                        continue

                    their_improvement = their_net if their_net > 0 else their_pos_improvement

                    # Check if trading give would drop that position into weakness
                    give_pos_w = my_weakness_map.get(give.position)
                    give_pos_new_value = (give_pos_w["my_starter_value"] if give_pos_w else 0) - (give.value if give in (give_pos_w["starters"] if give_pos_w else []) else 0)
                    drops_into_weakness = (
                        give_pos_w is not None and
                        give_pos_w["deficit"] <= 0 and
                        give_pos_new_value < give_pos_w["scaled_avg"]
                    )

                    their_starters = set(id(p) for p in other_team.starters())
                    degraded_flex = _check_flex_degradation(my_team, [give], [receive], avg_flex_value)
                    proposals.append({
                        "type": "1-for-1",
                        "partner": team_name,
                        "give": [give],
                        "receive": [receive],
                        "my_weak_pos": my_weak_pos,
                        "their_weak_pos": give.position,
                        "my_improvement": my_improvement,
                        "their_improvement": their_improvement,
                        "combined_improvement": my_improvement + their_improvement,
                        "value_sent": give.value,
                        "value_received": receive.value,
                        "fairness_pct": fp,
                        "receive_is_their_starter": [id(receive) in their_starters],
                        "drops_into_weakness": drops_into_weakness,
                        "give_pos": give.position,
                        "degraded_flex": degraded_flex,
                    })

    return _dedup_and_trim(proposals, top_n)


def find_package_trades(my_team, all_teams: dict, my_weaknesses: list, league_averages: dict, top_n: int = 10):
    """
    Finds 2-for-1 and 1-for-2 cross-position package trades where both teams
    net improve their total starter value (loose mutual benefit check).
    """
    proposals = []
    my_weakness_map = _position_map(my_weaknesses)
    my_weak_positions = [w["position"] for w in my_weaknesses if w["deficit"] > 0]
    avg_flex_value = league_averages.get("FLEX", 0)

    for team_name, other_team in all_teams.items():
        if team_name == my_team.name:
            continue

        their_weaknesses = identify_weaknesses(other_team, league_averages)
        their_weakness_map = _position_map(their_weaknesses)

        their_starters = set(id(p) for p in other_team.starters())

        # ── 2-for-1: I send two, I receive one ───────────────────────────────
        my_chips = _all_tradeable_players(my_team, my_weakness_map)

        for my_weak_pos in my_weak_positions:
            my_w = my_weakness_map[my_weak_pos]
            my_starters_at_pos = my_w["starters"]
            if not my_starters_at_pos:
                continue
            worst_my_starter = min(my_starters_at_pos, key=lambda p: p.value)

            their_singles = _upgrades_available(
                other_team, my_weak_pos, their_weakness_map, worst_my_starter.value
            )
            if not their_singles:
                continue

            for give_pair in combinations(my_chips, 2):
                p1, p2 = give_pair
                if p1.position == p2.position or p1 is p2:
                    continue
                value_sent = p1.value + p2.value
                if value_sent == 0:
                    continue

                for receive in their_singles:
                    if receive.value == 0:
                        continue
                    fp = _fairness_pct(value_sent, receive.value)
                    if fp > FAIRNESS_THRESHOLD:
                        continue
                    my_improvement = _net_starter_improvement(my_team, list(give_pair), [receive])
                    their_improvement = _net_starter_improvement(other_team, [receive], list(give_pair))
                    if my_improvement <= 0 or their_improvement <= 0:
                        continue

                    # Must close at least 20% of the deficit at the weak position
                    if my_improvement < 0.20 * my_w["deficit"]:
                        continue

                    # Check if either given player drops their position into weakness
                    drops = []
                    for gp in give_pair:
                        gp_w = my_weakness_map.get(gp.position)
                        if gp_w and gp_w["deficit"] <= 0:
                            new_val = gp_w["my_starter_value"] - (gp.value if gp in gp_w["starters"] else 0)
                            if new_val < gp_w["scaled_avg"]:
                                drops.append(gp.position)

                    degraded_flex = _check_flex_degradation(my_team, list(give_pair), [receive], avg_flex_value)
                    proposals.append({
                        "type": "2-for-1",
                        "partner": team_name,
                        "give": list(give_pair),
                        "receive": [receive],
                        "my_weak_pos": my_weak_pos,
                        "their_weak_pos": f"{p1.position}+{p2.position}",
                        "my_improvement": my_improvement,
                        "their_improvement": their_improvement,
                        "combined_improvement": my_improvement + their_improvement,
                        "value_sent": value_sent,
                        "value_received": receive.value,
                        "fairness_pct": fp,
                        "receive_is_their_starter": [id(receive) in their_starters],
                        "drops_into_weakness": len(drops) > 0,
                        "give_pos": "+".join(drops) if drops else None,
                        "degraded_flex": degraded_flex,
                    })

        # ── 1-for-2: I send one, I receive two ───────────────────────────────
        their_chips = _all_upgrades_available(other_team, their_weakness_map, min_value=0)

        for their_chip_pair in combinations(their_chips, 2):
            t1, t2 = their_chip_pair
            if t1.position == t2.position or t1 is t2:
                continue
            value_received = t1.value + t2.value
            if value_received == 0:
                continue

            my_singles = _all_tradeable_players(my_team, my_weakness_map)
            for give in my_singles:
                if give.value == 0:
                    continue
                fp = _fairness_pct(give.value, value_received)
                if fp > FAIRNESS_THRESHOLD:
                    continue
                my_improvement = _net_starter_improvement(my_team, [give], list(their_chip_pair))
                their_improvement = _net_starter_improvement(other_team, list(their_chip_pair), [give])
                if my_improvement <= 0 or their_improvement <= 0:
                    continue

                my_gains = {}
                for pos in my_weak_positions:
                    incoming_at_pos = [p for p in their_chip_pair if p.position == pos]
                    if incoming_at_pos:
                        my_gains[pos] = sum(p.value for p in incoming_at_pos)
                primary_gain_pos = max(my_gains, key=my_gains.get) if my_gains else None

                # Must close at least 20% of the primary weak position's deficit
                primary_w = my_weakness_map.get(primary_gain_pos) if primary_gain_pos else None
                if not primary_w or my_improvement < 0.20 * primary_w["deficit"]:
                    continue

                # Check if given player drops their position into weakness
                give_pos_w = my_weakness_map.get(give.position)
                drops_into_weakness = (
                    give_pos_w is not None and
                    give_pos_w["deficit"] <= 0 and
                    (give_pos_w["my_starter_value"] - (give.value if give in give_pos_w["starters"] else 0)) < give_pos_w["scaled_avg"]
                )

                degraded_flex = _check_flex_degradation(my_team, [give], list(their_chip_pair), avg_flex_value)
                proposals.append({
                    "type": "1-for-2",
                    "partner": team_name,
                    "give": [give],
                    "receive": list(their_chip_pair),
                    "my_weak_pos": primary_gain_pos or "multiple",
                    "their_weak_pos": give.position,
                    "my_improvement": my_improvement,
                    "their_improvement": their_improvement,
                    "combined_improvement": my_improvement + their_improvement,
                    "value_sent": give.value,
                    "value_received": value_received,
                    "fairness_pct": fp,
                    "receive_is_their_starter": [id(p) in their_starters for p in their_chip_pair],
                    "drops_into_weakness": drops_into_weakness,
                    "give_pos": give.position if drops_into_weakness else None,
                    "degraded_flex": degraded_flex,
                })

    return _dedup_and_trim(proposals, top_n)


def print_trade_proposals(proposals: list, header: str = "TRADE PROPOSALS", my_team=None, all_teams=None):
    if not proposals:
        print(f"\nNo fair proposals found.\n")
        return

    print(f"\n=== {header} ===\n")
    for i, p in enumerate(proposals, 1):
        partner_team = all_teams.get(p["partner"]) if all_teams else None
        my_total = my_team.total_value() if my_team else 0
        their_total = partner_team.total_value() if partner_team else 0

        give_str_parts = []
        for pl in p["give"]:
            share = f" ({pl.value / my_total * 100:.1f}% of my team)" if my_total else ""
            give_str_parts.append(f"{pl.name} ({pl.position}) val:{pl.value}{share}")
        give_str = ", ".join(give_str_parts)

        receive_strs = []
        for j, pl in enumerate(p["receive"]):
            is_starter = p["receive_is_their_starter"][j] if j < len(p["receive_is_their_starter"]) else False
            tag = " (their starter)" if is_starter else " (their bench)"
            share = f" ({pl.value / their_total * 100:.1f}% of their team)" if their_total else ""
            receive_strs.append(f"{pl.name} ({pl.position}) val:{pl.value}{share}{tag}")
        receive_str = ", ".join(receive_strs)

        print(f"  Trade #{i} [{p['type']}]")
        print(f"   📤 Give:    {give_str}")
        print(f"   📥 Receive: {receive_str}")
        print(f"   🤝 Partner: {p['partner']}")
        print(f"   📈 My improvement:    +{p['my_improvement']:.0f} starter value  (at {p['my_weak_pos']})")
        print(f"   📈 Their improvement: +{p['their_improvement']:.0f} starter value")
        print(f"   ⚖️  Value difference: {p['fairness_pct']*100:.1f}%")
        if p.get("drops_into_weakness"):
            print(f"   ⚠️  Warning: trading away {p['give_pos']} would drop that position below league average")
        if p.get("degraded_flex"):
            for dp in p["degraded_flex"]:
                print(f"   ⚠️  Warning: {dp.name} ({dp.position}, val:{dp.value}) would fill a FLEX slot below league average FLEX value")
        print()