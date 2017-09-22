import sys
from engine import Play


def one_game(silent=False):
    play = Play(silent=silent)
    result = play.start()
    if result['winner'] == 'Mafia':
        return 1
    else:
        return 0


def main():
    if len(sys.argv) < 2:
        print("Single game mode")
        result = one_game()
        SystemExit(result)
    else:
        print("Statistics mode")
        mafia_count = 0
        total_games = int(sys.argv[1])
        for g in range(total_games):
            mafia_count += one_game(silent=True)
        print("Played %s games, mafia won %s times" % (
            total_games, mafia_count
        ))
        print("Statistics: %s %% for mafia, %s %% for civils." % (
            round(float(mafia_count)*100/total_games, 2),
            100 - round(float(mafia_count)*100/total_games, 2)
        ))


if __name__ == '__main__':
    main()
