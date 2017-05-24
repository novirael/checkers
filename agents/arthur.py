"""
A checkers agent implementation based on Arthur Samuel's historic program.
"""
from utils import (
    INF, adv, cent, cntr, deny, kcent, mob, mov, thret, back, piece_score_diff,
    position_score, Player,
)


class ArthurPlayer(Player):

    def evaluate(self, board_old, board_new):
        if board_old.is_over():
            return -INF
        if board_new.is_over():
            return INF

        _adv = adv(board_new) - adv(board_old)
        _back = adv(board_new) - back(board_old)
        _cent = cent(board_new) - cent(board_old)
        _cntr = cntr(board_new) - cntr(board_old)
        _deny = deny(board_new) - deny(board_old)
        _kcent = kcent(board_new) - kcent(board_old)
        _mob = mob(board_new) - mob(board_old)
        _mobil = _mob - _deny
        _mov = mov(board_new) - mov(board_old)
        _thret = thret(board_new) - thret(board_old)

        undenied_mobility = 1 if _mobil > 0 else 0
        total_mobility = 1 if _mob > 0 else 0
        denial_of_occ = 1 if _deny > 0 else 0
        control = 1 if _cent > 0 else 0

        _demmo = 1 if denial_of_occ and not total_mobility else 0
        _mode_2 = 1 if undenied_mobility and not denial_of_occ else 0
        _mode_3 = 1 if not undenied_mobility and denial_of_occ else 0
        _moc_2 = 1 if not undenied_mobility and control else 0
        _moc_3 = 1 if undenied_mobility and not control else 0
        _moc_4 = 1 if not undenied_mobility and not control else 0

        return sum([
            _moc_2 * (-1) * (2**18),
            _kcent * (2**16),
            _moc_4 * (-1) * (2**14),
            _mode_3 * (-1) * (2**13),
            _demmo * (-1) * (2**11),
            _mov * (2 ** 8),
            _adv * (-1) * (2**8),
            _mode_2 * (-1) * (2**8),
            _back * (-1) * (2**6),
            _cntr * (2**5),
            _thret * (2**5),
            _moc_3 * (2**4),
            piece_score_diff(board_new, board_old.active) * (2**20),
            position_score(board_new, board_old.active) * (2**14),
        ])
