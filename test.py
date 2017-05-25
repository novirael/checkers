#!/usr/bin/python
import time
from datetime import datetime

from checkers import CheckerBoard, BLACK, WHITE
from agents.arthur import ArthurPlayer
from agents.rand import RandomPlayer

filename = "logs/{timestamp}.log".format(
    timestamp=datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
)
log_file = open(filename, 'w')


class TestAnalyzer():
    """
    Test class
    """
    summary_text = """
        Average played rounds: {rounds_average}
        Black wins: {score_black}
        White wins: {score_white}
        Unresolved games: {score_unresolved}
        Black thinking time (avg): {time_black}
        White thinking time (avg): {time_white}
    """

    def __init__(self, black_agent, white_agent, games=100):
        self.players = {
            BLACK: black_agent,
            WHITE: white_agent,
        }
        self.games_count = games
        self.stats = {
            "played_rounds": 0,
            "score": [],
            "thinking_time": {BLACK: [], WHITE: []},
        }

    def run(self):
        try:
            for number in range(1, self.games_count + 1):
                print("Game: %d" % number)
                log_file.write("########### GAME %3d ###########\n" % number)
                self.run_single_game()
        except KeyboardInterrupt:
            print("Test interrupted on %d" % number)

        self.print_summary()

    def run_single_game(self):
        board = CheckerBoard()
        turn = 0
        unresolved = False

        while not board.is_over():
            turn += 1

            log_file.write("#### Turn %3d\n" % turn)
            log_file.write(str(board))
            log_file.flush()

            if turn % 100 == 0:
                print("Over %d turns played" % turn)

            for player, agent in self.players.items():
                while not board.is_over() and board.active == player:
                    print("Player %d is making a decision" % player)
                    start_time = time.time()
                    move = agent.best_move(board)
                    self.stats["thinking_time"][player].append(time.time() - start_time)
                    board.update(move)

            if turn > 200:
                unresolved = True
                break

        self.stats["score"].append(board.winner if not unresolved else -1)
        self.stats["played_rounds"] += turn

    def print_summary(self):
        score = self.stats["score"]
        thinking_time = self.stats["thinking_time"]

        summary = self.summary_text.format(
            rounds_average=self.stats["played_rounds"] / self.games_count,
            score_black=score.count(BLACK),
            time_black=sum(thinking_time[BLACK]) / len(thinking_time[BLACK]),
            score_white=score.count(WHITE),
            time_white=sum(thinking_time[WHITE]) / len(thinking_time[WHITE]),
            score_unresolved=score.count(-1),
        )
        print(summary)
        log_file.write(summary)


if '__main__' == __name__:
    test = TestAnalyzer(RandomPlayer(), ArthurPlayer())
    test.run()
