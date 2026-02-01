from collections import defaultdict
from copy import deepcopy

class Team:
    def __init__(self, name, roster, lineup):
        self.roster = roster
        self.name = name
        self.lineup = lineup

    def players_by_position(self):
        positions = defaultdict(list)

        for player in self.roster:
            positions[player.position].append(player)

        return positions
    
    def sorted_positions(self):
        positions = {}

        for player in self.roster:
            positions.setdefault(player.position, []).append(player)

        for pos in positions:
            positions[pos].sort(key=lambda p: p.value, reverse=True)

        return positions

    def team_by_value(self):
        return sorted(self.roster, key=lambda p: p.value, reverse=True)

    def starters(self):
        starters = []
        positions = self.sorted_positions()

        for pos, count in self.lineup.items():
            starters.extend(positions.get(pos, [])[:count])

        flex_candidates = (
            positions.get("RB", [])[self.lineup.get("RB", 0):] +
            positions.get("WR", [])[self.lineup.get("WR", 0):] +
            positions.get("TE", [])[self.lineup.get("TE", 0):]
        )

        flex_candidates.sort(key=lambda p: p.value, reverse=True)
        starters.extend(flex_candidates[:self.lineup.get("FLEX", 0)])

        return starters

    def bench(self):
        starters = set(self.starters())
        bench = []
        for player in self.roster:
            if player not in starters:
                bench.append(player)
        return bench

    def total_starter_value(self):
        return sum(p.value for p in self.starters())
    
    def total_bench_value(self):
        return sum(p.value for p in self.bench())

    def total_value(self):
        return sum(p.value for p in self.roster)

    def position_value(self, position):
        return sum(p.value for p in self.roster if p.position == position)

    def with_trade(self, outgoing, incoming):
        new_roster = self.roster.copy()

        for player in outgoing:
            if player not in new_roster:
                raise ValueError(f"{player.name} not on roster")
            new_roster.remove(player)

        new_roster.extend(incoming)
        return Team(self.name, new_roster, self.lineup)
    
    def trade_difference(self, outgoing, incoming):
        new_team = self.with_trade(outgoing, incoming)
        return self.total_starter_value() - new_team.total_starter_value()

    def __str__(self):
        result = ""
        sorted = self.team_by_value()
        self.total_value()
        for player in sorted:
            result+=str(player) + "\n"
        
        return f"{self.name} - ({self.total_value()})\n" + result