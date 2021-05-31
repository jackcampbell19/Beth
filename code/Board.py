from Marker import Marker


class Board:
    """
    {Board} represents the chess board. Tracks all fid associations and where the pieces are.
    """

    def __init__(self, corner_fids, fid_to_piece_map):
        # Define all components
        self.tl_fid, self.tr_fid, self.bl_fid, self.br_fid = corner_fids
        self.fid_to_piece_map = fid_to_piece_map


class Square:

    def __init__(self, identifier, corners):
        self.id = identifier
        self.corners = corners


class KeyPosition:

    def __init__(self, position, visible_squares):
        self.gantry_position = position
        self.visible_squares = visible_squares
