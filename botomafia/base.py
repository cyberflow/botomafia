import random
import copy


class Action(object):
    def __init__(self, player_id):
        self.player = player_id


class Heal(Action):
    pass


class Kill(Action):
    pass


class CheckSide(Action):
    pass


class Guilty(Action):
    pass


class Role(object):

    def __init__(self, name, game):
        self.name = name
        self.game_rules = game
        self.configure_role()

    def configure_role(self):
        pass

    def day_say(self, mode):
        return None

    def day_vote(self):
        pass

    def remove_vote(self, player_id):
        return None

    def kill_both_players(self):
        return False

    def listen_for_day_talk(self, player, speech):
        pass

    def listen_for_vote(self, source_player, victim_player):
        pass

    def listen_for_day_verdict(self, kill_list):
        pass

    def listen_for_morning_update(self, kill_list):
        pass

    def listen_for_night_talk(self, source_player, victim_player, sign):
        pass

    def listen_for_postmortem(self):
        pass

    def mafia_night_meet(self, mafia):
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
        return random.choose(self.game.list_players(skip=self.name))


class Sheriff(Civil):
    role = "Sheriff"

    def configure_role(self):
        self.trusted = set([self.name])
        self.known_mafia = set([])

    def check_player(self):
        candidates = self.game.list_players(skip=self.trusted & self.known_mafia)
        candidate = random.choose(candidates)
        if not candidate:
            candidate = self.name
        return candidate

    def get_check_results(self, player_id, status):
        if status == Civil:
            self.trusted.add(player_id)
        elif status == Mafia:
            self.known_mafia.add(player_id)


class Doctor(Civil):
    role = "Doctor"

    def configure_role(self):
        self.healed = False

    def heal(self):
        candidates = self.game.list_players()
        if self.healed:
            candidates = candidates - set([self.name])
        candidate = random.choose(candidates)
        if candidate == self.name:
            self.healed = True
        return candidate


class Mafia(Role):
    side = "Mafia"
    role = "Mafia"

    def mafia_night_meet(self, mafia):
        self.mafia = copy.deepcopy(mafia)

    def night_vote(self):
        return random.choice(skip=self.mafia)


class Game(object):
    def __init__(self, civil_count=7, mafia_count=3, sheriff=True, doctor=True):
        self.civil_count = civil_count
        self.mafia_count = mafia_count
        self.total_players = civil_count + mafia_count
        self.create_roles(sheriff, doctor)
        self.players.sort(key=lambda player: player.name)

    def create_roles(self):
        self.players = []
        need_to_create = self.total_count
        names = ['player ' + str(y) for y in range(1, need_to_create + 1)]
        random.shuffle(names)
        namegen = (name for name in names)
        if self.sheriff:
            self.players.append(self.Sheriff(name=namegen.next()))
            need_to_create -= 1
        if self.doctor:
            self.civils.append(Doctor(name=namegen.next()))
            need_to_create -= 1
        for count in range(self.mafia_count):
            self.players.append(Mafia(name=namegen.next()))
            need_to_create -= 1
        for count in need_to_create:
            self.players.append(Civil(name=namegen.next()))

    def list_players(self):
        return [player.name for player in self.players]

    def _find_player_by_id(self, player_id):
        for player in self.players:
            if player.name == player_id:
                self.players.remove(player)
                return player
        raise Exception("Player %s not found" % player_id)

    def _find_players_by_type(self, player_type):
        result = []
        for player in self.players:
            if isinstance(player, player_type):
                result.append(player)
        return result

    def kill(self, player_id):
        player = self._find_player_by_id(player_id)
        self.players.remove(player)
        return type(player)

    def check_player(self, player_id):
        player = self._find_player_by_id(player_id)
        if isinstance(player, Civil):
            return Civil
        elif isinstance(player, Mafia):
            return Mafia
        raise Exception("Unknown player type %s" % str(type(player)))

    def _get_mafia(self):
        return self._find_players_by_type(Mafia)

    def _get_civils(self):
        return self._find_players_by_type(Civil)

    def _get_sherif(self):
        sheriffs = self._find_players_by_type(Sheriff)
        if sheriffs:
            return sheriffs[0]

    def _get_doctor(self):
        doctors = self._find_players_by_type(Doctor)
        if doctors:
            return doctors[0]

    def is_end(self):
        if len(self._get_mafia) >= len(self._get_civils):
            return Mafia
        elif len(self._get_mafia) == 0:
            return Civil
        else:
            return None

    def day_next_player(self):
        for player in self.players:
            yield player

    def night_next_player(self):
        for mafia in self._get_mafia:
            yield mafia
        sheriff = self._get_sherif()
        if sheriff:
            yield sheriff
        doctor = self._get_doctor()
        if doctor:
            yield doctor


class Play(object):
    def __init__(self, civil_count=7, mafia_count=3, sheriff=True, doctor=True):
        self.game = Game(civil_count, mafia_count, sheriff, doctor)

    def start(self):
        while not self.game.is_end():
            self.day()
            if self.game.is_end():
                break
            self.night()
