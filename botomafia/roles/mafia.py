from role import Role

class Mafia(Role):
    side = "Mafia"
    role = "Mafia"

    def day_vote(self):
        return self.game.list_players(skip=self.mafia)[0]

    def mafia_night_meet(self, mafia):
        self.mafia = [m.name for m in mafia]

    def night_vote(self):
        return self.game.list_players(skip=self.mafia)[0]
