"""
This module defines the CheckerBoard class.
"""

from copy import deepcopy

# CONSTANTS

# Black moves "forward", white moves "backward"
BLACK, WHITE = 0, 1

# The IBM704 had 36-bit words. Arthur Samuel used the extra bits to
# ensure that every normal move could be performed by flipping the
# original bit and the bit either 4 or 5 bits away, in the cases of
# moving right and left respectively.

UNUSED_BITS = 0b100000000100000000100000000100000000


class CheckerBoard:
    def __init__(self):
        """
        Initiates board via new_game().
        """
        self.forward = [None, None]
        self.backward = [None, None]
        self.pieces = [None, None]
        self.new_game()

    def new_game(self):
        """
        Resets current state to new game.
        """
        self.active = BLACK
        self.passive = WHITE

        self.forward[BLACK] = 0x1eff
        self.backward[BLACK] = 0
        self.pieces[BLACK] = self.forward[BLACK] | self.backward[BLACK]

        self.forward[WHITE] = 0
        self.backward[WHITE] = 0x7fbc00000
        self.pieces[WHITE] = self.forward[WHITE] | self.backward[WHITE]

        self.empty = UNUSED_BITS ^ (2**36 - 1) ^ (self.pieces[BLACK] | self.pieces[WHITE])

        self.jump = 0
        self.mandatory_jumps = []

    def update(self, move):
        """
        Updates the game state to reflect the effects of the input
        move.

        A legal move is represented by an integer with exactly two
        bits turned on: the old position and the new position.
        """
        active, passive = self.active, self.passive
        if move < 0:
            move *= -1
            taken_piece = int(1 << sum(i for (i, b) in enumerate(bin(move)[::-1]) if b == '1')/2)
            self.pieces[passive] ^= taken_piece
            if self.forward[passive] & taken_piece:
                self.forward[passive] ^= taken_piece
            if self.backward[passive] & taken_piece:
                self.backward[passive] ^= taken_piece
            self.jump = 1

        self.pieces[active] ^= move
        if self.forward[active] & move:
            self.forward[active] ^= move
        if self.backward[active] & move:
            self.backward[active] ^= move

        destination = move & self.pieces[active]
        self.empty = UNUSED_BITS ^ (2**36 - 1) ^ (self.pieces[BLACK] | self.pieces[WHITE])

        if self.jump:
            self.mandatory_jumps = self.jumps_from(destination)
            if self.mandatory_jumps:
                return

        if active == BLACK and (destination & 0x780000000) != 0:
            self.backward[BLACK] |= destination
        elif active == WHITE and (destination & 0xf) != 0:
            self.forward[WHITE] |= destination

        self.jump = 0
        self.active, self.passive = self.passive, self.active

    def peek_move(self, move):
        """
        Updates the game state to reflect the effects of the input
        move.

        A legal move is represented by an integer with exactly two
        bits turned on: the old position and the new position.
        """
        board = deepcopy(self)
        active, passive = board.active, board.passive

        if move < 0:
            move *= -1
            taken_piece = int(1 << sum(i for (i, b) in enumerate(bin(move)[::-1]) if b == '1')/2)
            board.pieces[passive] ^= taken_piece
            if board.forward[passive] & taken_piece:
                board.forward[passive] ^= taken_piece
            if board.backward[passive] & taken_piece:
                board.backward[passive] ^= taken_piece
            board.jump = 1

        board.pieces[active] ^= move
        if board.forward[active] & move:
            board.forward[active] ^= move
        if board.backward[active] & move:
            board.backward[active] ^= move

        destination = move & board.pieces[active]
        board.empty = UNUSED_BITS ^ (2**36 - 1) ^ (board.pieces[BLACK] | board.pieces[WHITE])

        if board.jump:
            board.mandatory_jumps = board.jumps_from(destination)
            if board.mandatory_jumps:
                return board

        if active == BLACK and (destination & 0x780000000) != 0:
            board.backward[BLACK] |= destination
        elif active == WHITE and (destination & 0xf) != 0:
            board.forward[WHITE] |= destination

        board.jump = 0
        board.active, board.passive = board.passive, board.active

        return board

    # These methods return an integer whose active bits are those squares
    # that can make the move indicated by the method name.
    def right_forward(self):
        return (self.empty >> 4) & self.forward[self.active]

    def left_forward(self):
        return (self.empty >> 5) & self.forward[self.active]

    def right_backward(self):
        return (self.empty << 4) & self.backward[self.active]

    def left_backward(self):
        return (self.empty << 5) & self.backward[self.active]

    def right_forward_jumps(self):
        return (self.empty >> 8) & (self.pieces[self.passive] >> 4) & self.forward[self.active]

    def left_forward_jumps(self):
        return (self.empty >> 10) & (self.pieces[self.passive] >> 5) & self.forward[self.active]

    def right_backward_jumps(self):
        return (self.empty << 8) & (self.pieces[self.passive] << 4) & self.backward[self.active]

    def left_backward_jumps(self):
        return (self.empty << 10) & (self.pieces[self.passive] << 5) & self.backward[self.active]

    def get_moves(self):
        """
        Returns a list of all possible moves.

        A legal move is represented by an integer with exactly two
        bits turned on: the old position and the new position.

        Jumps are indicated with a negative sign.
        """
        # First check if we are in a jump sequence
        if self.jump:
            return self.mandatory_jumps

        # Next check if there are jumps
        jumps = self.get_jumps()
        if jumps:
            return jumps

        # If not, then find normal moves
        rf = self.right_forward()
        lf = self.left_forward()
        rb = self.right_backward()
        lb = self.left_backward()

        moves = [0x11 << i for (i, bit) in enumerate(bin(rf)[::-1]) if bit == '1']
        moves += [0x21 << i for (i, bit) in enumerate(bin(lf)[::-1]) if bit == '1']
        moves += [0x11 << i - 4 for (i, bit) in enumerate(bin(rb)[::-1]) if bit == '1']
        moves += [0x21 << i - 5 for (i, bit) in enumerate(bin(lb)[::-1]) if bit == '1']

        return moves

    def get_jumps(self):
        """
        Returns a list of all possible jumps.

        A legal move is represented by an integer with exactly two
        bits turned on: the old position and the new position.

        Jumps are indicated with a negative sign.
        """
        rfj = self.right_forward_jumps()
        lfj = self.left_forward_jumps()
        rbj = self.right_backward_jumps()
        lbj = self.left_backward_jumps()

        moves = []

        if (rfj | lfj | rbj | lbj) != 0:
            moves += [-0x101 << i for (i, bit) in enumerate(bin(rfj)[::-1]) if bit == '1']
            moves += [-0x401 << i for (i, bit) in enumerate(bin(lfj)[::-1]) if bit == '1']
            moves += [-0x101 << i - 8 for (i, bit) in enumerate(bin(rbj)[::-1]) if bit == '1']
            moves += [-0x401 << i - 10 for (i, bit) in enumerate(bin(lbj)[::-1]) if bit == '1']

        return moves

    def jumps_from(self, piece):
        """
        Returns list of all possible jumps from the piece indicated.

        The argument piece should be of the form 2**n, where n + 1 is
        the square of the piece in question (using the internal numeric
        representation of the board).
        """
        if self.active == BLACK:
            rfj = (self.empty >> 8) & (self.pieces[self.passive] >> 4) & piece
            lfj = (self.empty >> 10) & (self.pieces[self.passive] >> 5) & piece

            # piece at square is a king
            if piece & self.backward[self.active]:
                rbj = (self.empty << 8) & (self.pieces[self.passive] << 4) & piece
                lbj = (self.empty << 10) & (self.pieces[self.passive] << 5) & piece
            else:
                rbj = 0
                lbj = 0
        else:
            rbj = (self.empty << 8) & (self.pieces[self.passive] << 4) & piece
            lbj = (self.empty << 10) & (self.pieces[self.passive] << 5) & piece

            # piece at square is a king
            if piece & self.forward[self.active]:
                rfj = (self.empty >> 8) & (self.pieces[self.passive] >> 4) & piece
                lfj = (self.empty >> 10) & (self.pieces[self.passive] >> 5) & piece
            else:
                rfj = 0
                lfj = 0

        moves = []
        if (rfj | lfj | rbj | lbj) != 0:
            moves += [-0x101 << i for (i, bit) in enumerate(bin(rfj)[::-1]) if bit == '1']
            moves += [-0x401 << i for (i, bit) in enumerate(bin(lfj)[::-1]) if bit == '1']
            moves += [-0x101 << i - 8 for (i, bit) in enumerate(bin(rbj)[::-1]) if bit == '1']
            moves += [-0x401 << i - 10 for (i, bit) in enumerate(bin(lbj)[::-1]) if bit == '1']

        return moves

    def takeable(self, piece):
        """
        Returns true of the passed piece can be taken by the active player.
        """
        active = self.active
        if (self.forward[active] & (piece >> 4)) != 0 and (self.empty & (piece << 4)) != 0:
            return True
        if (self.forward[active] & (piece >> 5)) != 0 and (self.empty & (piece << 5)) != 0:
            return True
        if (self.backward[active] & (piece << 4)) != 0 and (self.empty & (piece >> 4)) != 0:
            return True
        if (self.backward[active] & (piece << 5)) != 0 and (self.empty & (piece >> 5)) != 0:
            return True
        return False

    def is_over(self):
        return not len(self.get_moves())

    @property
    def winner(self):
        """
        Returns id of player or None when game is not finished.
        """
        if not self.is_over():
            return None

        if self.active == WHITE:
            return BLACK
        return WHITE

    def get_board(self):
        """
        Returns representation of current state in list of list object.
        """
        black_king = self.backward[BLACK]
        black_men = self.forward[BLACK] ^ black_king
        white_king = self.forward[WHITE]
        white_men = self.backward[WHITE] ^ white_king

        fields = [1 << x for i, x in enumerate(range(35), start=1) if i % 9 != 0]
        grouped_fields = [fields[i:i+4] for i in range(0, len(fields), 4)]

        board = []
        for row in grouped_fields[::-1]:
            board_rows = []
            for cell in row[::-1]:
                if cell & black_men:
                    item = "b"
                elif cell & white_men:
                    item = "w"
                elif cell & black_king:
                    item = "B"
                elif cell & white_king:
                    item = "W"
                else:
                    item = " "
                board_rows.append(item)
            board.append(board_rows)

        return board

    def __str__(self):
        """
        Prints out ASCII art representation of board.
        """
        board = self.get_board()
        representation = "-----------------------------------------------\n"

        for i, row in enumerate(board):
            representation += "  "
            representation += "   |  " if i % 2 == 0 else ""
            representation += "  |     |  ".join(row)
            representation += "  |" if i % 2 != 0 else ""
            representation += "\n"
            representation += "-----------------------------------------------\n"
        return representation
