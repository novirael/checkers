#!/usr/bin/python

from datetime import datetime

from checkers import CheckerBoard, BLACK, WHITE
from agents.arthur import ArthurPlayer
from agents.rand import RandomPlayer

filename = "logs/{timestamp}.log".format(
    timestamp=datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
)
log_file = open(filename, 'w')


class TestAnalyzer():
    def __init__(self, agent1, agent2, games=100):
        self.players = {
            BLACK: agent1,
            WHITE: agent2,
        }
        self.games_count = games

    def run(self):
        played_rounds = 0
        winners = []

        try:
            for number in range(1, self.games_count + 1):
                print("Game: %d" % number)
                log_file.write("########### GAME %3d ###########\n" % number)
                winner, rounds = self.run_single_game()
                winners.append(winner)
                played_rounds += rounds
        except KeyboardInterrupt:
            print("Test interrupted on" % number)

        summary = "Average played rounds: {}\nBlack/White: {}/{}".format(
            played_rounds / self.games_count,
            winners.count(BLACK),
            winners.count(WHITE)
        )
        print(summary)
        log_file.write(summary)

    def run_single_game(self):
        board = CheckerBoard()
        turn = 0

        while not board.is_over():
            turn += 1

            log_file.write("#### Turn %3d\n" % turn)
            log_file.write(str(board))
            log_file.flush()

            if turn % 100 == 0:
                print("Over %d turns played" % turn)

            for color, agent in self.players.items():
                while not board.is_over() and board.active == color:
                    board.update(agent.best_move(board))

            if turn > 1000:
                break

        log_file.write("#### Summary\n")
        log_file.write("## Winner: %s\n" % board.winner)
        log_file.write("## Total rounds: %s\n" % turn)

        return board.winner, turn


if '__main__' == __name__:
    test = TestAnalyzer(RandomPlayer(), ArthurPlayer())
    test.run()
