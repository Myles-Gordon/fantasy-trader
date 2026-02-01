class Player:
    def __init__(self, name, position, value = 0, status="Active", team=None,):
        self.name = name
        self.position = position
        self.value = value
        self.team = team
        self.status = status
    
    def __str__(self):
        return f"{self.name} ({self.position}) - {self.value}"
    
