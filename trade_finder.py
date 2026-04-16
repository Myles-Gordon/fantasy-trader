from itertools import combinations
from collections import defaultdict

FAIRNESS_THRESHOLD = 0.10  # 10% value difference tolerance


def find_trades(my_team, all_teams: dict, weaknesses: list, top_n: int = 10):
    """
    For each weakness position, scan other teams for players that would upgrade
    my starters. Proposes 1-for-1 trades within the fairness threshold.

    Returns a list of trade proposals sorted by improvement, best first:
    [
        {
            "partner": "OtherTeamName",
            "give": Player,
            "receive": Player,
            "position_improved": "RB",
            "my_value_before": float,
            "my_value_after": float,
            "improvement": float,
            "value_sent": float,
            "value_received": float,
            "fairness_pct": float,
        },
        ...
    ]
    """
    proposals = []
    my_starters = my_team.starters()
    my_starter_set = set(id(p) for p in my_starters)

    # Only look at genuine weaknesses (deficit > 0)
    weak_positions = [w for w in weaknesses if w["deficit"] > 0]

    for weakness in weak_positions:
        pos = weakness["position"]
        my_starters_at_pos = weakness["starters"]

        if not my_starters_at_pos:
            continue

        # Worst starter at this position is the most tradeable
        worst_starter = min(my_starters_at_pos, key=lambda p: p.value)

        for team_name, other_team in all_teams.items():
            if team_name == my_team.name:
                continue

            other_starters = other_team.starters()
            other_starter_ids = set(id(p) for p in other_starters)

            # Look at all players on their roster at this position
            other_pos_players = [
                p for p in other_team.roster
                if p.position == pos and p.value > worst_starter.value
            ]

            for candidate in other_pos_players:
                # Try trading worst_starter for candidate
                value_sent = worst_starter.value
                value_received = candidate.value

                if value_sent == 0 and value_received == 0:
                    continue

                # Fairness check: neither side gets more than 10% extra value
                max_val = max(value_sent, value_received)
                if max_val == 0:
                    continue
                fairness_pct = abs(value_sent - value_received) / max_val

                if fairness_pct > FAIRNESS_THRESHOLD:
                    continue

                # Calculate improvement to my starter value at this position
                before = weakness["my_starter_value"]
                after = before - worst_starter.value + candidate.value
                improvement = after - before

                if improvement <= 0:
                    continue

                proposals.append({
                    "partner": team_name,
                    "give": worst_starter,
                    "receive": candidate,
                    "position_improved": pos,
                    "my_value_before": before,
                    "my_value_after": after,
                    "improvement": improvement,
                    "value_sent": value_sent,
                    "value_received": value_received,
                    "fairness_pct": fairness_pct,
                    "they_are_starter": id(candidate) in other_starter_ids,
                })

    # Sort by improvement descending
    proposals.sort(key=lambda x: x["improvement"], reverse=True)
    return proposals[:top_n]


def print_trade_proposals(proposals: list):
    if not proposals:
        print("\n No fair trade proposals found.\n")
        return

    print("\n=== TRADE PROPOSALS ===\n")
    for i, p in enumerate(proposals, 1):
        starter_tag = " (their starter)" if p["they_are_starter"] else " (their bench)"
        print(f"  Trade #{i} — Improve {p['position_improved']}")
        print(f"   📤 Give:    {p['give'].name} ({p['give'].position}) — value {p['value_sent']}")
        print(f"   📥 Receive: {p['receive'].name} ({p['receive'].position}){starter_tag} — value {p['value_received']}")
        print(f"   🤝 Partner: {p['partner']}")
        print(f"   📈 Starter value change: {p['my_value_before']:.0f} → {p['my_value_after']:.0f} (+{p['improvement']:.0f})")
        print(f"   ⚖️  Value difference: {p['fairness_pct']*100:.1f}%")
        print()