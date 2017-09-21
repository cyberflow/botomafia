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

    def get_kill_notice(self, player_id, role_type):
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
