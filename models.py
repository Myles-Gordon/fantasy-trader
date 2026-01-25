class Player:
    def __init__(self, name, position, value, team=None):
        self.name = name
        self.position = position
        self.value = value
        self.team = team
    
    def __str__(self):
        return f"{self.name} ({self.position}) - {self.value}"
    
class Team:
    def __init__(self, roster):
        self.roster = roster
    
    