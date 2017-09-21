import random
import copy
import logging
from collections import Counter
import pprint

logging.basicConfig(format='%(message)s', level=logging.DEBUG)
log = logging


class Role(object):

    def __init__(self, name, game):
        self.name = name
        self.game = game
        self.configure_role()

    def configure_role(self):
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
        return False

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


class Civil(Role):
    side = "Civil"
    role = "Citizen"

    def day_vote(self):
        return random.choice(self.game.list_players(skip=self.name))


class Sheriff(Civil):
    role = "Sheriff"

    def configure_role(self):
        self.trusted = set([self.name])
        self.known_mafia = set([])

    def check_player(self):
        candidates = self.game.list_players(
            skip=self.trusted & self.known_mafia
        )
        candidate = random.choice(candidates)
        if not candidate:
            candidate = self.name
        return candidate

    def get_check_result(self, player_id, status):
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
            candidates.remove(self.name)
        candidate = random.choice(candidates)
        if candidate == self.name:
            self.healed = True
        return candidate


class Mafia(Role):
    side = "Mafia"
    role = "Mafia"

    def day_vote(self):
        return random.choice(self.game.list_players(skip=self.name))

    def mafia_night_meet(self, mafia):
        self.mafia = [m.name for m in mafia]

    def night_vote(self):
        return self.game.list_players(skip=self.mafia)[0]


class Game(object):
    def __init__(
            self,
            civil_count=7,
            mafia_count=3,
            sheriff=True,
            doctor=True
    ):
        self.civil_count = civil_count
        self.mafia_count = mafia_count
        self.total_players = civil_count + mafia_count
        self.create_roles(sheriff, doctor)
        self.players.sort(key=lambda player: player.name)
        self.dead = []

    def create_roles(self, sheriff, doctor):
        self.players = []
        need_to_create = self.total_players
        names = ['player ' + str(y) for y in range(1, need_to_create + 1)]
        random.shuffle(names)
        namegen = (name for name in names)
        if sheriff:
            self.players.append(Sheriff(name=namegen.next(), game=self))
            need_to_create -= 1
        if doctor:
            self.players.append(Doctor(name=namegen.next(), game=self))
            need_to_create -= 1
        for count in range(self.mafia_count):
            self.players.append(Mafia(name=namegen.next(), game=self))
            need_to_create -= 1
        for count in range(need_to_create):
            self.players.append(Civil(name=namegen.next(), game=self))

    def list_players(self, skip=[]):
        return [player.name for player in self.players if player.name not in skip]

    def _find_player_by_id(self, player_id):
        for player in self.players:
            if player.name == player_id:
                return player
        raise Exception("Player %s not found" % str(player_id))

    def _find_players_by_type(self, player_type):
        result = []
        for player in self.players:
            if isinstance(player, player_type):
                result.append(player)
        return result

    def kill(self, player_id):
        player = self._find_player_by_id(player_id)
        self.players.remove(player)
        self.dead.append(player)
        return type(player)

    def check_player(self, player_id):
        player = self._find_player_by_id(player_id)
        if isinstance(player, Civil):
            return Civil
        elif isinstance(player, Mafia):
            return Mafia
        raise Exception("Unknown player type %s" % str(type(player)))

    def mafia(self):
        return self._find_players_by_type(Mafia)

    def civils(self):
        return self._find_players_by_type(Civil)

    def sheriff(self):
        sheriffs = self._find_players_by_type(Sheriff)
        if sheriffs:
            return sheriffs[0]

    def doctor(self):
        doctors = self._find_players_by_type(Doctor)
        if doctors:
            return doctors[0]

    def players(self):
        self._find_players_by_type(Role)

    def ended(self):
        print("mafia", len(self.mafia()))
        print("civils", len(self.civils()))
        if len(self.mafia()) >= len(self.civils()):
            return Mafia
        elif len(self.mafia()) == 0:
            return Civil
        else:
            return None
    def result(self):
        winner = self.ended().role
        alive_players = [{player.name: player.role} for player in self.players]
        dead_players = [{player.name: player.role} for player in self.dead]
        return {'winner': winner, 'alive_players': alive_players, 'dead_players': dead_players}

class Play(object):
    def __init__(
        self, civil_count=7, mafia_count=3,
        sheriff=True, doctor=True
    ):
        self.game = Game(civil_count, mafia_count, sheriff, doctor)
        self.turn = 0

    def start(self):
        log.info('Game started')
        for mafioso in self.game.mafia():
            mafioso.mafia_night_meet(self.game.mafia())
        while not self.game.ended():
            self.turn += 1
            log.info("Day %s" % self.turn)
            self.day()
            if self.game.ended():
                break
            log.info("Night %s" % self.turn)
            self.night()
        return self.game.result()

    def day(self):
        self.everybody_speaks()
        kill_list = self.voting()
        log.info("Day %s, results of voting: %s players removed", self.turn, len(kill_list))
        self.kill(kill_list)

    def night(self):
        victim_id = self.mafia_turn()
        self.sheriff_turn()
        healed_id = self.doctor_turn()
        if victim_id != healed_id:
            self.kill([victim_id])

    def doctor_turn(self):
        doctor = self.game.doctor()
        if doctor:
            log.info("Doctor turn")
            return doctor.heal()

    def sheriff_turn(self):
        sheriff = self.game.sheriff()
        if sheriff:
            pending_id = sheriff.check_player()
            role_type = self.game.check_player(pending_id)
            sheriff.get_check_result(pending_id, role_type)
            log.info("Sheriff turn")

    def mafia_turn(self):
        log.info("Mafia turn")
        for mafioso in self.game.mafia():
            victim_name = mafioso.night_say()
            self.broadcast("mafia say", mafioso.name, victim_name, "")
        votes = []
        for mafioso in self.game.mafia():
            votes.append(mafioso.night_vote())
            results = Counter(votes)
            for victim, score in results.items():
                if score > len(self.game.mafia())/2:
                    return victim
        raise Exception("Mafia unable to deside. Votes: %s" % votes)


    def broadcast(
        self, speech_type, speaker_id, target_id=None,
        speech=None, recievers=None
    ):
        if not recievers:
            recievers = self.game.list_players()
        for reciver in recievers:
            self.game._find_player_by_id(reciver).listen(
                speech_type, speaker_id, target_id, speech
            )

    def kill(self, kill_list):
        for victim in kill_list:
            role_type = self.game.kill(victim)
            log.info("%s was %s" % (victim, role_type.role))
            for player in self.game.players:
                player.get_kill_notice(victim, role_type)

    def everybody_speaks(self):
        for speaker in self.game.players:
            speech = speaker.day_say()
            self.broadcast(speech, "day", speaker.name, None, speech)

    def voting(self):
        votes = {}
        winners = {}
        iteration = 0
        new_votes = self.gather_votes()
        new_winners = self.get_winners(new_votes)
        while winners.keys() != new_winners.keys():
            log.info("Voting, turn %s" % iteration)
            iteration += 1
            winners = copy.copy(new_winners)
            votes = copy.copy(new_votes)
            for winner_id in winners:
                defence = self.game._find_player_by_id(winner_id).day_defence()
                self.broadcast("defence", winner_id, None, defence)
            new_votes = self.move_votes(votes, winners)
            new_winners = self.get_winners(new_votes)
        if len(winners) > 1:
            return self.autocatastrophy(votes, winners)
        return winners.keys()

    def autocatastrophy(self, votes, winners):
        voters = self.game.list_players()
        for winner in winners.keys():
            voters.remove(winner)
        yay_nay_list = map(lambda p: self.game._find_player_by_id(p).kill_many_players(winners.keys()),
                           voters
                           )
        yay_count = sum(yay_nay_list)
        if yay_count < len(voters):
            return {}
        else:
            return winners.keys()

    def move_votes(self, old_votes, winners):
        new_votes = copy.copy(old_votes)
        for winner_id, his_voters in winners.items():
            for voter in his_voters:
                new_winner_id = voter.move_vote(winner_id)
                if new_winner_id:
                    new_votes[winner_id].remove(voter)
                    new_votes[new_winner_id].append(voter)
                    self.broadcast("move vote", voter.name, new_winner_id)
        return new_votes

    def get_winners(self, votes):
        max_score = 0
        winners = {}
        for victim, votes in votes.items():
            if len(votes) > max_score:
                max_score = len(votes)
                winners = {victim: votes}
            elif len(votes) == max_score:
                winners[victim] = votes
        return winners

    def gather_votes(self):
        votes = {}
        for voter in self.game.players:
            vote_against = voter.day_vote()
            log.info("Day %s. %s voted against %s." % (
                self.turn, voter.name, vote_against
            ))
            self.broadcast("day_vote", voter.name, vote_against, None)
            votes[vote_against] = votes.get(vote_against, []) + [voter]
        return votes


def main():
    play = Play()
    result = play.start()
    print("\nGame end")
    pprint.pprint(result)
    if result == Mafia:
        raise SystemExit(1)
    else:
        raise SystemExit(0)


if __name__ == '__main__':
    main()
