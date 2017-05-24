"""
Helpers and evaluation funcions.
"""

import sys

# Constants
from functools import reduce

BLACK, WHITE = 0, 1
VALID_SQUARES = 0x7FBFDFEFF

INF = sys.maxsize


# Feature functions

# Advancement
def adv(board):
    """
    The parameter is credited with 1 for each passive man in the
    fifth and sixth rows (counting in passive's direction) and
    debited with 1 for each passive man in the third and fourth
    rows.
    """
    passive = board.passive

    rows_3_and_4 = 0x1FE00
    rows_5_and_6 = 0x3FC0000
    if passive == WHITE:
        rows_3_and_4, rows_5_and_6 = rows_5_and_6, rows_3_and_4

    bits_3_and_4 = rows_3_and_4 & board.pieces[passive]
    bits_5_and_6 = rows_5_and_6 & board.pieces[passive]
    return bin(bits_5_and_6).count("1") - bin(bits_3_and_4).count("1")


# Back Row Bridge
def back(board):
    """
    The parameter is credited with 1 if there are no active kings
    on the board and if the two bridge squares (1 and 3, or 30 and
    32) in the back row are occupied by passive pieces.
    """
    active = board.active
    passive = board.passive
    if active == BLACK:
        if board.backward[BLACK] != 0:
            return 0
        back_row_bridge = 0x480000000
    else:
        if board.forward[WHITE] != 0:
            return 0
        back_row_bridge = 0x5

    if bin(back_row_bridge & board.pieces[passive]).count('1') == 2:
        return 1
    return 0


# Center Control I
def cent(board):
    """
    The parameter is credited with 1 for each of the following
    squares: 11, 12, 15, 16, 20, 21, 24, 25 which is occupied by
    a passive man.
    """
    passive = board.passive
    if passive == WHITE:
        center_pieces = 0xA619800
    else:
        center_pieces = 0xCC3280

    return bin(board.pieces[passive] & center_pieces).count("1")


# Center Control II
def cntr(board):
    """
    The parameter is credited with 1 for each of the following
    squares: 11, 12, 15, 16, 20, 21, 24, 25 that is either
    currently occupied by an active piece or to which an active
    piece can move.
    """
    active = board.active
    if active == BLACK:
        center_pieces = 0xA619800
    else:
        center_pieces = 0xCC3280

    moves = board.get_moves()
    if moves[0] < 0:
        moves = map(lambda x: x*(-1), moves)

    destinations = reduce(
        lambda x, y: x|y, [
            (m & (m ^ board.pieces[active]))
            for m in moves
        ]
    )

    active_center_count = bin(board.pieces[active] & center_pieces).count("1")
    active_near_center_count = bin(destinations & center_pieces).count("1")
    return active_center_count + active_near_center_count


# Denial of Occupancy
def deny(board):
    """
    The parameter is credited 1 for each square defined in MOB if
    on the next move a piece occupying this square could be
    captured without exchange.
    """
    rf = board.right_forward()
    lf = board.left_forward()
    rb = board.right_backward()
    lb = board.left_backward()

    moves = [0x11 << i for (i, bit) in enumerate(bin(rf)[::-1]) if bit == '1']
    moves += [0x21 << i for (i, bit) in enumerate(bin(lf)[::-1]) if bit == '1']
    moves += [0x11 << i - 4 for (i, bit) in enumerate(bin(rb)[::-1]) if bit == '1']
    moves += [0x21 << i - 5 for (i, bit) in enumerate(bin(lb)[::-1]) if bit == '1']

    destinations = [0x10 << i for (i, bit) in enumerate(bin(rf)[::-1]) if bit == '1']
    destinations += [0x20 << i for (i, bit) in enumerate(bin(lf)[::-1]) if bit == '1']
    destinations += [0x1 << i - 4 for (i, bit) in enumerate(bin(rb)[::-1]) if bit == '1']
    destinations += [0x1 << i - 5 for (i, bit) in enumerate(bin(lb)[::-1]) if bit == '1']

    denials = []

    for move, dst in zip(moves, destinations):
        B = board.peek_move(move)
        active = B.active
        ms_taking = []
        ds = []

        if (B.forward[active] & (dst >> 4)) != 0 and (B.empty & (dst << 4)) != 0:
            ms_taking.append((-1)*((dst >> 4) | (dst << 4)))
            ds.append(dst << 4)

        if (B.forward[active] & (dst >> 5)) != 0 and (B.empty & (dst << 5)) != 0:
            ms_taking.append((-1)*((dst >> 5) | (dst << 5)))
            ds.append(dst << 5)

        if (B.backward[active] & (dst << 4)) != 0 and (B.empty & (dst >> 4)) != 0:
            ms_taking.append((-1)*((dst << 4) | (dst >> 4)))
            ds.append(dst >> 4)

        if (B.backward[active] & (dst << 5)) != 0 and (B.empty & (dst >> 5)) != 0:
            ms_taking.append((-1)*((dst << 5) | (dst >> 5)))
            ds.append(dst >> 5)

        if not ms_taking:
            continue
        else:
            for m, d in zip(ms_taking, ds):
                C = B.peek_move(m)
                if C.active == active:
                    if dst not in denials:
                        denials.append(dst)
                    continue
                if not C.takeable(d):
                    if not dst in denials:
                        denials.append(dst)

    return len(denials)


# King Center Control
def kcent(board):
    """
    The parameter is credited with 1 for each of the following
    squares: 11, 12, 15, 16, 20, 21, 24, and 25 which is occupied
    by a passive king.
    """
    passive = board.passive
    if passive == WHITE:
        center_pieces = 0xA619800
        passive_kings = board.forward[WHITE]
    else:
        center_pieces = 0xCC3280
        passive_kings = board.backward[BLACK]

    return bin(passive_kings & center_pieces).count("1")


# Total Mobility
def mob(board):
    """
    The parameter is credited with 1 for each square to which the
    active side could move one or more pieces in the normal fashion
    disregarding the fact that jump moves may or may not be
    available.
    """
    rf = board.right_forward()
    lf = board.left_forward()
    rb = board.right_backward()
    lb = board.left_backward()

    destinations = [0x10 << i for (i, bit) in enumerate(bin(rf)[::-1]) if bit == '1']
    destinations += [0x20 << i for (i, bit) in enumerate(bin(lf)[::-1]) if bit == '1']
    destinations += [0x1 << i - 4 for (i, bit) in enumerate(bin(rb)[::-1]) if bit == '1']
    destinations += [0x1 << i - 5 for (i, bit) in enumerate(bin(lb)[::-1]) if bit == '1']

    if not destinations:
        return 0
    return bin(reduce(lambda x, y: x|y, destinations)).count("1")


# Undenied Mobility
def mobil(board):
    """
    The parameter is credited with the difference between MOB and
    DENY.
    """
    return mob(board) - deny(board)


# Move
def mov(board):
    """
    The parameter is credited with 1 if pieces are even with a
    total piece count (2 for men, and 3 for kings) of less than 24,
    and if an odd number of pieces are in the move system, defined
    as those vertical files starting with squares 1, 2, 3, and 4.
    """
    black_men = bin(board.forward[BLACK]).count("1")
    black_kings = bin(board.backward[BLACK]).count("1")
    black_score = 2 * black_men + 3 * black_kings
    white_men = bin(board.backward[WHITE]).count("1")
    white_kings = bin(board.forward[WHITE]).count("1")
    white_score = 2 * white_men + 3 * white_kings

    if white_score < 24 and black_score == white_score:
        pieces = board.pieces[BLACK] | board.pieces[WHITE]
        if board.active == BLACK:
            move_system = 0x783c1e0f
        else:
            move_system = 0x783c1e0f0
        if bin(move_system & pieces).count("1") % 2 == 1:
            return 1

    return 0


# Threat
def thret(board):
    """
    The parameter is credited with 1 for each square to which an
    active piece may be moved and in doing so threaten to capture
    a passive piece on a subsequent move.
    """
    moves = board.get_moves()
    destinations = map(lambda x: (x ^ board.pieces[board.active]) & x, moves)
    origins = [x ^ y for (x, y) in zip(moves, destinations)]

    jumps = []
    for dst, orig in zip(destinations, origins):
        if board.active == BLACK:
            rfj = (board.empty >> 8) & (board.pieces[board.passive] >> 4) & dst
            lfj = (board.empty >> 10) & (board.pieces[board.passive] >> 5) & dst

            # piece is king
            if orig & board.backward[board.active]:
                rbj = (board.empty << 8) & (board.pieces[board.passive] << 4) & dst
                lbj = (board.empty << 10) & (board.pieces[board.passive] << 5) & dst
            else:
                rbj, lbj = 0, 0
        else:
            rbj = (board.empty << 8) & (board.pieces[board.passive] << 4) & dst
            lbj = (board.empty << 10) & (board.pieces[board.passive] << 5) & dst

            # piece at square is a king
            if dst & board.forward[board.active]:
                rfj = (board.empty >> 8) & (board.pieces[board.passive] >> 4) & dst
                lfj = (board.empty >> 10) & (board.pieces[board.passive] >> 5) & dst
            else:
                rfj, lfj = 0, 0

        if (rfj | lfj | rbj | lbj) != 0:
            jumps += [-0x101 << i for (i, bit) in enumerate(bin(rfj)[::-1]) if bit == '1']
            jumps += [-0x401 << i for (i, bit) in enumerate(bin(lfj)[::-1]) if bit == '1']
            jumps += [-0x101 << i - 8 for (i, bit) in enumerate(bin(rbj)[::-1]) if bit == '1']
            jumps += [-0x401 << i - 10 for (i, bit) in enumerate(bin(lbj)[::-1]) if bit == '1']

    return len(jumps)


def piece_score_diff(board, player):
    black_men = bin(board.forward[BLACK]).count("1")
    black_kings = bin(board.backward[BLACK]).count("1")
    black_score = 2 * black_men + 3 * black_kings
    white_men = bin(board.backward[WHITE]).count("1")
    white_kings = bin(board.forward[WHITE]).count("1")
    white_score = 2 * white_men + 3 * white_kings

    return black_score - white_score if player == BLACK else white_score - black_score


def position_score(board, player):
    scores = [0x88000, 0x1904c00, 0x3A0502E0, 0x7C060301F]
    total = 0
    for i, score in enumerate(scores, start=1):
        total = i * bin(board.pieces[player] & score).count("1")
    return total


class Player():
    search_methods = ['min_max', 'alpha_beta', 'nega_max']
    search_method_name = search_methods[-1]

    def __init__(self, depth=5, search_with='nega_max'):
        self.depth = depth
        self.search_method_name = search_with

    def best_move(self, board):
        def search(move):
            board_new = board.peek_move(move)
            color = 1 if board_new.active == board.active else -1
            attributes = [board, board_new, self.depth, color]
            if self.search_method_name in ('alpha_beta', 'nega_max'):
                attributes += [-INF, INF]
            return getattr(self, self.search_method_name)(*attributes)

        return max(board.get_moves(), key=search)

    def evaluate(self, board_old, board_new):
        raise NotImplementedError

    def min_max(self, board_old, board_new, depth, color):
        if depth == 0 or board_new.is_over():
            return self.evaluate(board_old, board_new) * color

        best_value = -INF if color == 1 else INF

        for move in board_new.get_moves():
            board = board_new.peek_move(move)
            if board.active != board_new.active:
                val = self.min_max(board_new, board, depth - 1, -color)
            else:
                val = self.min_max(board_new, board, depth,  color)

            if color == 1:
                best_value = max(val, best_value)
            else:
                best_value = min(val, best_value)

        return best_value

    def alpha_beta(self, board_old, board_new, depth, color, alpha, beta):
        if depth == 0 or board_new.is_over():
            return self.evaluate(board_old, board_new) * color

        best_value = -INF if color == 1 else INF

        for move in board_new.get_moves():
            board = board_new.peek_move(move)
            if board.active != board_new.active:
                val = self.alpha_beta(board_new, board, depth - 1, -color, -alpha, -beta)
            else:
                val = self.alpha_beta(board_new, board, depth, color, alpha, beta)

            if color == 1:
                best_value = max(val, best_value)
                alpha = max(best_value, alpha)
            else:
                best_value = min(val, best_value)
                beta = min(best_value, beta)

            if alpha >= beta:
                break

        return best_value

    def nega_max(self, board_old, board_new, depth, color, alpha, beta):
        if depth == 0 or board_new.is_over():
            return self.evaluate(board_old, board_new) * color

        best_value = -INF

        for move in board_new.get_moves():
            board = board_new.peek_move(move)
            if board.active != board_new.active:
                val = -self.nega_max(board_new, board, depth - 1, -color, -beta, -alpha)
            else:
                val = self.nega_max(board_new, board, depth, color, alpha, beta)

            best_value = max(best_value, val)
            alpha = max(alpha, val)
            if alpha >= beta:
                break

        return best_value


def get_move_strings(board):
    rfj = board.right_forward_jumps()
    lfj = board.left_forward_jumps()
    rbj = board.right_backward_jumps()
    lbj = board.left_backward_jumps()

    if (rfj | lfj | rbj | lbj) != 0:
        rfj = [
            (1 + i - i//9, 1 + (i + 8) - (i + 8)//9)
            for (i, bit) in enumerate(bin(rfj)[::-1])
            if bit == '1'
        ]
        lfj = [
            (1 + i - i//9, 1 + (i + 10) - (i + 8)//9)
            for (i, bit) in enumerate(bin(lfj)[::-1])
            if bit == '1'
        ]
        rbj = [
            (1 + i - i//9, 1 + (i - 8) - (i - 8)//9)
            for (i, bit) in enumerate(bin(rbj)[::-1])
            if bit == '1'
        ]
        lbj = [
            (1 + i - i//9, 1 + (i - 10) - (i - 10)//9)
            for (i, bit) in enumerate(bin(lbj)[::-1])
            if bit == '1'
        ]

        if board.active == BLACK:
            regular_moves = ["%i to %i" % (orig, dst) for (orig, dst) in rfj + lfj]
            reverse_moves = ["%i to %i" % (orig, dst) for (orig, dst) in rbj + lbj]
            return regular_moves + reverse_moves
        else:
            reverse_moves = ["%i to %i" % (orig, dst) for (orig, dst) in rfj + lfj]
            regular_moves = ["%i to %i" % (orig, dst) for (orig, dst) in rbj + lbj]
            return reverse_moves + regular_moves

    rf = board.right_forward()
    lf = board.left_forward()
    rb = board.right_backward()
    lb = board.left_backward()

    rf = [
        (1 + i - i//9, 1 + (i + 4) - (i + 4)//9)
        for (i, bit) in enumerate(bin(rf)[::-1])
        if bit == '1'
    ]
    lf = [
        (1 + i - i//9, 1 + (i + 5) - (i + 5)//9)
        for (i, bit) in enumerate(bin(lf)[::-1])
        if bit == '1'
    ]
    rb = [
        (1 + i - i//9, 1 + (i - 4) - (i - 4)//9)
        for (i, bit) in enumerate(bin(rb)[::-1])
        if bit == '1'
    ]
    lb = [
        (1 + i - i//9, 1 + (i - 5) - (i - 5)//9)
        for (i, bit) in enumerate(bin(lb)[::-1])
        if bit == '1'
    ]

    if board.active == BLACK:
        regular_moves = ["%i to %i" % (orig, dst) for (orig, dst) in rf + lf]
        reverse_moves = ["%i to %i" % (orig, dst) for (orig, dst) in rb + lb]
        return regular_moves + reverse_moves
    else:
        regular_moves = ["%i to %i" % (orig, dst) for (orig, dst) in rb + lb]
        reverse_moves = ["%i to %i" % (orig, dst) for (orig, dst) in rf + lf]
        return reverse_moves + regular_moves
