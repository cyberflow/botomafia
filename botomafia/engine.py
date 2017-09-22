import random
from roles import Sheriff, Doctor, Civil, Mafia
import copy
from collections import Counter
import logging


class Game(object):
    def __init__(
            self,
            civil_count=7,
            mafia_count=3,
            sheriff=True,
            doctor=True,
            do_logging=True
    ):

        self.civil_count = civil_count
        self.mafia_count = mafia_count
        self.total_players = civil_count + mafia_count
        self.create_roles(sheriff, doctor)
        self.players.sort(key=lambda player: player.name)
        self.dead = []
        self.turn = 0
        self.log = self.init_logging()

    @staticmethod
    def init_logging():
        log = logging.getLogger('botomafia')
        log.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        ch.setFormatter(formatter)
        log.addHandler(ch)
        return log

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

    def get_status(self):
        return {
            "turn": self.turn,
            "civils": len(self.civils()),
            "mafia": len(self.mafia()),
            "alive": len(self.players),
            "dead": len(self.dead)
        }

    def new_day(self):
        self.turn += 1
        player = self.players.pop(0)
        self.players.append(player)

    def ended(self):
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
        res = {
            'winner': winner,
            'alive_players': alive_players,
            'dead_players': dead_players
        }
        self.log.info(res)
        return res


class Play(object):
    def __init__(
        self, civil_count=7, mafia_count=3,
        sheriff=True, doctor=True, silent=False
    ):

        self.game = Game(civil_count, mafia_count, sheriff, doctor)
        if silent:
            self.game.log.setLevel(logging.ERROR)

    def new_day(self):
        self.game.new_day()
        self.game.log.info("Day %s" % self.game.turn)
        for player in self.game.players:
            player.new_day_notice()

    def start(self):
        self.game.log.info('Game started')
        for mafioso in self.game.mafia():
            mafioso.mafia_night_meet(self.game.mafia())
        while not self.game.ended():
            self.new_day()
            self.day()
            if self.game.ended():
                break
            self.game.log.info("Night %s" % self.game.turn)
            self.night()
        return self.game.result()

    def day(self):
        self.everybody_speaks()
        kill_list = self.voting()
        self.game.log.info("Day %s, results of voting: %s players removed",
                           self.game.turn, len(kill_list))
        self.kill(Civil, kill_list)

    def night(self):
        victim_id = self.mafia_turn()
        self.sheriff_turn()
        healed_id = self.doctor_turn()
        if victim_id != healed_id:
            self.kill(Mafia, [victim_id])
        else:
            self.game.log.info("No one was killed at this night")
            self.kill(Mafia, [])

    def doctor_turn(self):
        doctor = self.game.doctor()
        if doctor:
            self.game.log.info("Doctor turn")
            return doctor.heal()

    def sheriff_turn(self):
        sheriff = self.game.sheriff()
        if sheriff:
            pending_id = sheriff.check_player()
            role_type = self.game.check_player(pending_id)
            sheriff.get_check_result(pending_id, role_type)
            self.game.log.info("Sheriff turn")

    def mafia_turn(self):
        self.game.log.info("Mafia turn")
        for mafioso in self.game.mafia():
            target_id = mafioso.night_say()
            self.broadcast("mafia say", mafioso.name, target_id, "")
        for attempt in range(10):
            votes = []
            for mafioso in self.game.mafia():
                votes.append(mafioso.night_vote())
                results = Counter(votes)
            for victim, score in results.items():
                if score > len(self.game.mafia())/2:
                    return victim
        else:
            raise Exception("Mafia unable to deside in 1000 interation."
                            " Votes: %s" % votes)

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

    def kill(self, initiator, kill_list):
        if kill_list:
            for victim in kill_list:
                role_type = self.game.kill(victim)
                self.game.log.info("%s was %s [killed by %s's]" % (
                    victim, role_type.role, initiator.role
                ))
                for player in self.game.players:
                    player.get_kill_notice(victim, initiator, role_type)
        else:
            for player in self.game.players:
                player.get_kill_notice(None, initiator, None)

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
            self.game.log.info("Voting, turn %s" % iteration)
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
        self.game.log.info("autocatastrophe: %s players has %s voices each" % (
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
        self.game.log.info("Vote to remove players: %s" % str(yay_nay_list))
        yay_count = sum(yay_nay_list)
        if yay_count < len(voters)/2:
            self.game.log.info("Players voted against players removal")
            return []
        else:
            self.game.log.info("%s will be removed" % winners.keys())
            return winners.keys()

    def move_votes(self, old_votes, winners):
        new_votes = copy.copy(old_votes)
        for winner_id, his_voters in winners.items():
            for voter in his_voters:
                new_winner_id = voter.move_vote(winner_id)
                if new_winner_id:
                    self.game.log.info("%s moved voice to %s" % (
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
            if voter.name == vote_against:
                raise Exception("Player %s voting against %s" % (
                                voter, vote_against
                ))
            self.game.log.info("Day %s. %s voted against %s." % (
                self.game.turn, voter.name, vote_against
            ))
            self.broadcast("day_vote", voter.name, vote_against, None)
            votes[vote_against] = votes.get(vote_against, []) + [voter]
        return votes
