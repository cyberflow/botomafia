import random


class Role(object):

    def __init__(self, name, game):
        self.name = name
        self.game = game
        self.configure_role()

    def __str__(self):
        return self.name

    def __repr__(self):
        return "%s [%s]" % (self.name, self.role)

    def configure_role(self):
        pass

    def new_day_notice(self):
        pass

    def day_say(self):
        return None

    def day_vote(self):
        pass

    def day_defence(self):
        pass

    def move_vote(self, player_id):
        return None

    def kill_many_players(self, kill_list):
        return True

    def listen(self, speech_type, speaker_id, target_id, speech):
        pass

    def get_kill_notice(self, initiator, player_id, role_type):
        pass

    def night_say(self):
        pass

    def night_vote(self):
        pass

    def check_player(self):
        pass

    def get_check_result(self, player, status):
        pass

    def heal(self):
        pass


class Civil(Role):
    side = "Civil"
    role = "Citizen"

    def day_vote(self):
        return random.choice(self.game.list_players(skip=self.name))
        # return self.game.list_players(skip=self.name)[0]


class Sheriff(Civil):
    role = "Sheriff"

    def configure_role(self):
        self.trusted = [self.name]
        self.known_mafia = []

    def check_player(self):
        candidates = self.game.list_players(
            skip=self.trusted + self.known_mafia
        )
        if not candidates:
            candidate = self.name
        else:
            candidate = random.choice(candidates)
        return candidate

    def get_kill_notice(self, player_id, initiator, role_type):
        if player_id in self.known_mafia:
            self.known_mafia.remove(player_id)

    def day_vote(self):
        if self.known_mafia:
            return self.known_mafia[0]
        return random.choice(self.game.list_players(skip=self.trusted))

    def get_check_result(self, player_id, status):
        if status == Civil:
            self.trusted.append(player_id)
        elif status == Mafia:
            self.known_mafia.append(player_id)


class Doctor(Civil):
    role = "Doctor"

    def configure_role(self):
        self.healed = False
        self.night_heal = None
        self.trusted = [self.name]

    def heal(self):
        candidates = self.game.list_players()
        if self.healed:
            candidates.remove(self.name)
        candidate = random.choice(candidates)
        if candidate == self.name:
            self.healed = True
        else:
            self.night_heal = candidate
        return candidate

    def day_vote(self):
        return random.choice(self.game.list_players(skip=self.trusted))

    def get_kill_notice(self, player_id, initiator, role_type):
        if (initiator is Mafia):
            if not player_id and self.night_heal:
                self.trusted.append(self.night_heal)
            self.night_heal = None


class Mafia(Role):
    side = "Mafia"
    role = "Mafia"

    def configure_role(self):
        self.night_kill = None

    def day_vote(self):
        return random.choice(self.game.list_players(skip=self.mafia))

    def mafia_night_meet(self, mafia):
        self.mafia = [m.name for m in mafia]

    def night_say(self):
        if not self.night_kill:
            self.night_kill = random.choice(
                self.game.list_players(skip=self.mafia)
            )
        return self.night_kill

    def listen(self, speech_type, speaker_id, target_id, speech):
            if speech_type == "mafia say":
                if target_id:
                    self.night_kill = target_id

    def night_vote(self):
        return self.night_kill

    def new_day_notice(self):
        self.night_kill = None
