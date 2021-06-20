from Exceptions import BoardPieceViolation


class Board:
    """
    {Board} represents the chess board. Tracks all fid associations and where the pieces are.
    """

    def __init__(self, fid_to_piece_map):
        self.fid_to_piece_map = fid_to_piece_map

    def translate_fid_to_piece(self, fid):
        if fid not in self.fid_to_piece_map:
            raise BoardPieceViolation(f"Unknown piece ({fid}) detected on board.")
        return self.fid_to_piece_map[fid]

    @staticmethod
    def get_fen_position(board_positions):
        fen = ""
        em_count = 0
        for sid in [f"{c}{r}" for r in range(8, 0, -1) for c in 'abcdefgh']:
            if sid in board_positions:
                if em_count > 0:
                    fen += f"{em_count}"
                    em_count = 0
                fen += board_positions[sid]
            else:
                em_count += 1
            if 'h' in sid:
                if em_count > 0:
                    fen += f"{em_count}"
                    em_count = 0
                fen += '/'
        fen = fen[:-1] + ' b - - 0 1'
        return fen






class Square:

    def __init__(self, identifier, corners):
        self.id = identifier
        self.corners = corners


class KeyPosition:

    def __init__(self, position, visible_squares):
        self.gantry_position = position
        self.visible_squares = visible_squares
