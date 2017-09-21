import sys
import random
import copy
import logging
from collections import Counter
import pprint

logging.basicConfig(format='%(message)s', level=logging.DEBUG)
log = logging.getLogger('mafia')


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

    def get_kill_notice(self, player_id, role_type):
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
        return self.game.list_players(skip=self.mafia)[0]

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
        self.turn = 0

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
        return [
            player.name for player in
            self.players if player.name not in skip
        ]

    def _find_player_by_id(self, player_id):
        for player in self.players:
            if player.name == player_id:
                return player
        import pdb
        pdb.set_trace()
        raise Exception("Player %s not found, existing players" % str(
            player_id
        ), str(self.players))

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

    def new_day(self):
        self.turn += 1
        player = self.players.pop(0)
        self.players.append(player)

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
        return {
            'winner': winner,
            'alive_players': alive_players,
            'dead_players': dead_players
        }


class Play(object):
    def __init__(
        self, civil_count=7, mafia_count=3,
        sheriff=True, doctor=True
    ):
        self.game = Game(civil_count, mafia_count, sheriff, doctor)

    def new_day(self):
        self.game.new_day()
        log.info("Day %s" % self.game.turn)
        for player in self.game.players:
            player.new_day_notice()

    def start(self):
        log.info('Game started')
        for mafioso in self.game.mafia():
            mafioso.mafia_night_meet(self.game.mafia())
        while not self.game.ended():
            self.game.new_day()
            self.new_day()
            self.day()
            if self.game.ended():
                break
            log.info("Night %s" % self.game.turn)
            self.night()
        return self.game.result()

    def day(self):
        self.everybody_speaks()
        kill_list = self.voting()
        log.info("Day %s, results of voting: %s players removed",
                 self.game.turn, len(kill_list)
                 )
        self.kill(kill_list)

    def night(self):
        victim_id = self.mafia_turn()
        self.sheriff_turn()
        healed_id = self.doctor_turn()
        if victim_id != healed_id:
            self.kill([victim_id])
        else:
            log.info("No one was killed at this night")

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
        while set(winners.keys()) != set(new_winners.keys()):
            iteration += 1
            log.info("Voting, turn %s" % iteration)
            winners = copy.copy(new_winners)
            votes = copy.copy(new_votes)
            for winner_id in winners.keys():
                defence = self.game._find_player_by_id(winner_id).day_defence()
                self.broadcast("defence", winner_id, None, defence)
            new_votes = self.move_votes(votes, winners)
            new_winners = self.get_winners(new_votes)
        if len(winners) > 1:
            return self.autocatastrophe(votes, winners)
        return winners.keys()

    def autocatastrophe(self, votes, winners):
        log.info("autocatastrophe: %s players has %s voices each" % (
            len(winners), len(winners.values()[0]))
        )
        voters = self.game.list_players()
        for winner in winners.keys():
            voters.remove(winner)
        yay_nay_list = [
            self.game._find_player_by_id(voter).kill_many_players(
                winners.keys()
            ) for voter in voters
        ]
        log.info("Vote to remove players: %s" % str(yay_nay_list))
        yay_count = sum(yay_nay_list)
        if yay_count < len(voters)/2:
            log.info("Players voted against players removal")
            return []
        else:
            log.info("%s will be removed" % winners.keys())
            return winners.keys()

    def move_votes(self, old_votes, winners):
        new_votes = copy.copy(old_votes)
        for winner_id, his_voters in winners.items():
            for voter in his_voters:
                new_winner_id = voter.move_vote(winner_id)
                if new_winner_id:
                    log.info("%s moved voice to %s" % (
                        voter.name,
                        new_winner_id
                    ))
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
                self.game.turn, voter.name, vote_against
            ))
            self.broadcast("day_vote", voter.name, vote_against, None)
            votes[vote_against] = votes.get(vote_against, []) + [voter]
        return votes


def game():
    play = Play()
    result = play.start()
    print("\nGame end")
    pprint.pprint(result)
    if result['winner'] == 'Mafia':
        return 1
    else:
        return 0


def main():
    if len(sys.argv) < 2:
        print("Single game mode")
        result = game()
        SystemExit(result)
    else:
        print("Statistics mode")
        mafia_count = 0
        total_games = int(sys.argv[1])
        for g in range(total_games):
            mafia_count += game()
        print("Played %s games, mafia won %s times (%s %%)" % (
            total_games, mafia_count, float(mafia_count)*100/total_games
        ))


if __name__ == '__main__':
    main()
