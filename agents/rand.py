"""
A checkers agent that picks a random move
"""

import random


class RandomPlayer():
    def best_move(self, board):
        return random.choice(board.get_moves())
