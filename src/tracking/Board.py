from src.misc.Exceptions import BoardPieceViolation
import numpy as np
import math

from src.misc.Log import log


class Board:
    """
    {Board} represents the chess board. Tracks all fid associations and where the pieces are.
    """

    def __init__(self, fid_to_piece_map, a1_position, h1_position, a8_position, h8_position):
        self.fid_to_piece_map = fid_to_piece_map
        self.a1_position = np.array(a1_position)
        self.h1_position = np.array(h1_position)
        self.a8_position = np.array(a8_position)
        self.h8_position = np.array(h8_position)

    def translate_fid_to_piece(self, fid):
        if fid not in self.fid_to_piece_map:
            raise BoardPieceViolation(f"Unknown piece ({fid}) detected on board.")
        return self.fid_to_piece_map[fid]

    def get_square_location(self, sid):
        if len(sid) != 2:
            log.error(f"Square ID \"{sid}\" is invalid. Returning (0, 0).")
            return 0, 0
        col, row = sid
        col, row = int(ord(col) - ord('a')), int(row) - 1
        if 0 <= col < 8 and 0 <= row < 8:
            tx = self.a8_position + (self.h8_position - self.a8_position) * (1 / 7 * col)
            bx = self.a1_position + (self.h1_position - self.a1_position) * (1 / 7 * col)
            x, y = bx + (tx - bx) * (1 / 7 * row)
            return int(x), int(y)
        log.error(f"Square ID \"{sid}\" is out of bounds. Returning (0, 0).")
        return 0, 0

    @staticmethod
    def square_ids_to_fen(square_ids):
        fen = ""
        em_count = 0
        for sid in [f"{c}{r}" for r in range(8, 0, -1) for c in 'abcdefgh']:
            if sid in square_ids:
                if em_count > 0:
                    fen += f"{em_count}"
                    em_count = 0
                fen += square_ids[sid]
            else:
                em_count += 1
            if 'h' in sid:
                if em_count > 0:
                    fen += f"{em_count}"
                    em_count = 0
                fen += '/'
        fen = fen[:-1] + ' b - - 0 1'
        return fen

    @staticmethod
    def fen_to_square_ids(fen):
        board_layout = fen.split()[0]
        for x in range(1, 9):
            board_layout = board_layout.replace(str(x), ''.join(['0' for _ in range(x)]))
        board_layout = board_layout.split('/')
        board_layout = list(map(lambda r: list(r), board_layout))
        square_ids = {}
        letters = list('abcdefgh')
        for i in range(8):
            for j in range(8):
                piece_id = board_layout[i][j]
                if piece_id == '0':
                    continue
                square_ids[f"{letters[j]}{8 - i}"] = piece_id
        return square_ids

    @staticmethod
    def get_move_from_fen_positions(prev_fen, next_fen):
        prev_sids = Board.fen_to_square_ids(prev_fen)
        next_sids = Board.fen_to_square_ids(next_fen)
        changed_prev = [sid for sid in prev_sids if sid not in next_sids or next_sids[sid] != prev_sids[sid]]
        changed_next = [sid for sid in next_sids if sid not in prev_sids or next_sids[sid] != prev_sids[sid]]
        if len(changed_prev) == 0:
            return None
        if len(changed_next) != 1:
            print(prev_fen)
            print(next_fen)
            print(changed_prev)
            print(changed_next)
            raise BoardPieceViolation('Invalid move detected.')
        move_end = changed_next[0]
        piece_moved = next_sids[move_end]
        move_start = None
        for sid in changed_prev:
            if prev_sids[sid] == piece_moved:
                move_start = sid
        if move_start is None:
            raise BoardPieceViolation('Invalid move detected. Could not find move start.')
        move = f"{move_start}{move_end}"
        return move


class KeyPosition:

    def __init__(self, position, sid_centers, sid_fid_mapping):
        self.gantry_position = position
        self.sid_centers = sid_centers
        self.sid_fid_mapping = sid_fid_mapping

    def get_closest_sid(self, pos):
        """
        Returns the SID of the square that is closest to the position.
        """
        x, y = pos
        closest_sid = self.sid_centers.keys()[0]
        closest_distance = math.inf
        for sid in self.sid_centers:
            sid_x, sid_y = self.sid_centers[sid]
            distance = np.linalg.norm(np.array([sid_x, sid_y]) - np.array([x, y]))
            if closest_distance > distance:
                closest_distance = distance
                closest_sid = sid
        return closest_sid
