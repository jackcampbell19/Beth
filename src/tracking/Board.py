import numpy as np
import math
from src.misc.Exceptions import BoardPieceViolation, NoMoveFound, InvalidMove
from src.misc.Log import log
from stockfish import Stockfish


class Board:
    """
    {Board} represents the chess board. Tracks all fid associations and where the pieces are.
    """

    def __init__(self, fid_to_piece_map, a1_position, h1_position, a8_position, h8_position):
        self.fid_to_piece_map = fid_to_piece_map
        self.piece_fids = list(fid_to_piece_map.keys())
        self.a1_position = np.array(a1_position)
        self.h1_position = np.array(h1_position)
        self.a8_position = np.array(a8_position)
        self.h8_position = np.array(h8_position)

    def translate_fid_to_piece(self, fid):
        if fid not in self.fid_to_piece_map:
            raise BoardPieceViolation(f"Unknown piece {fid} detected on board.")
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
            return [int(x), int(y)]
        log.error(f"Square ID \"{sid}\" is out of bounds. Returning (0, 0).")
        return [0, 0]

    @staticmethod
    def board_state_to_fen(square_ids):
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
    def generate_chess_engine_instance():
        return Stockfish('/home/pi/stockfish')

    @staticmethod
    def fen_to_board_state(fen):
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
    def get_move_from_board_states(board_state_before, board_state_after, previous_moves, chess_engine: Stockfish):
        """
        Determine the move given the state before the move and the state after the move.
        """
        # Determine the sids in the prev state that differ in the current state
        changed_before = [sid for sid in board_state_before
                          if sid not in board_state_after or board_state_after[sid] != board_state_before[sid]]
        # Determine the sids in the current state that differ from the prev state
        changed_after = [sid for sid in board_state_after
                         if sid not in board_state_before or board_state_after[sid] != board_state_before[sid]]
        # Check for promoted pieces
        promoted_piece = None
        pieces_before = ''.join(sorted([p for p in board_state_before.values() if p in Board.get_white_pieces()]))
        pieces_after = ''.join(sorted([p for p in board_state_after.values() if p in Board.get_white_pieces()]))
        if pieces_before != pieces_after:
            differing_pieces = pieces_before + pieces_after
            for p in pieces_before:
                if p in pieces_after:
                    differing_pieces.replace(p, '', 2)
            log.info(f"Found differing pieces between states: {differing_pieces}")
            potential_piece = differing_pieces.replace('p', '')
            if len(differing_pieces) != 2 or 'p' not in differing_pieces or len(potential_piece) != 1:
                raise InvalidMove('Piece promotion is invalid.')
            promoted_piece = potential_piece
        # If no change raise exception
        if len(changed_before) == 0 or len(changed_after) == 0:
            raise NoMoveFound()
        # If more than one sid was changed in the after board state this could be a castling move
        if len(changed_after) != 1:
            # Construct a set of all the pieces involved in the move
            pieces_moved = set(
                [board_state_before[k] for k in changed_before] + [board_state_after[k] for k in changed_after]
            )
            # Check if the move is a castling move
            is_castling_move = len(pieces_moved) == 2 and (
                    ('r' in pieces_moved and 'k' in pieces_moved) or ('R' in pieces_moved and 'K' in pieces_moved)
            )
            # If it is a castling move, filter out board state changes that are not related to the king
            if is_castling_move:
                log.info('Castling move detected.')
                board_state_before = {k: board_state_before[k] for k in board_state_before
                                      if (board_state_before[k] == 'k' or board_state_before[k] == 'K')}
                board_state_after = {k: board_state_after[k] for k in board_state_after
                                     if (board_state_after[k] == 'k' or board_state_after[k] == 'K')}
                changed_before = [sid for sid in board_state_before
                                  if sid not in board_state_after or board_state_after[sid] != board_state_before[sid]]
                changed_after = [sid for sid in board_state_after
                                 if sid not in board_state_before or board_state_after[sid] != board_state_before[sid]]
            else:
                raise InvalidMove('Move affected too many sids.')
        # Get the move end sid
        e_sid = changed_after[0]
        piece_moved = board_state_after[e_sid] if promoted_piece is None else promoted_piece
        # Find the move start sid
        s_sid = None
        for sid in changed_before:
            if board_state_before[sid] == piece_moved:
                s_sid = sid
        if s_sid is None:
            raise InvalidMove('Could not find move start.')
        move = f"{s_sid}{e_sid}{promoted_piece if promoted_piece is not None else ''}"
        # Verify that the move is valid
        chess_engine.set_position(previous_moves)
        if not chess_engine.is_move_correct(move):
            raise InvalidMove(f"Move {move} is invalid.")
        return move

    @staticmethod
    def get_starting_board_state():
        return Board.fen_to_board_state('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')

    @staticmethod
    def get_all_sids():
        sids = []
        for l in 'abcdefgh':
            for n in range(1, 9):
                sids.append(f"{l}{n}")
        return sids

    @staticmethod
    def get_white_pieces():
        return 'PRNBQK'

    @staticmethod
    def get_full_white_pieces():
        return 'PPPPPPPPRRNNBBQQK'

    @staticmethod
    def get_black_pieces():
        return Board.get_white_pieces().lower()

    @staticmethod
    def get_full_black_pieces():
        return Board.get_full_white_pieces().lower()

    @staticmethod
    def get_all_pieces():
        return Board.get_white_pieces() + Board.get_black_pieces()

    @staticmethod
    def get_surrounding_sids(sid):
        col, row = list(sid)
        col, row = ord(col), int(row)
        a, h = ord('a'), ord('h')
        surrounding = []
        if col > a:
            surrounding.append(f"{chr(col - 1)}{row}")
        if col < h:
            surrounding.append(f"{chr(col + 1)}{row}")
        if row > 1:
            surrounding.append(f"{chr(col)}{row - 1}")
        if row < 8:
            surrounding.append(f"{chr(col)}{row + 1}")
        return surrounding


class KeyPosition:

    def __init__(self, position, sid_centers, sid_fid_mapping, x_range, y_range):
        self.gantry_position = position
        self.sid_centers = sid_centers
        self.sid_fid_mapping = sid_fid_mapping
        self.x_range = x_range
        self.y_range = y_range

    def get_closest_sid(self, pos):
        """
        Returns the SID of the square that is closest to the position.
        """
        x, y = pos
        closest_sid = list(self.sid_centers.keys())[0]
        closest_distance = math.inf
        for sid in self.sid_centers:
            sid_x, sid_y = self.sid_centers[sid]
            distance = np.linalg.norm(np.array([sid_x, sid_y]) - np.array([x, y]))
            if closest_distance > distance:
                closest_distance = distance
                closest_sid = sid
        return closest_sid
