from Marker import Marker


class Board:

    def __init__(self, tl_fid, tr_fid, bl_fid, br_fid, fid_to_piece_map):
        # Define all components
        self.tl_fid = tl_fid
        self.tr_fid = tr_fid
        self.bl_fid = bl_fid
        self.br_fid = br_fid
        self.fid_to_piece_map = fid_to_piece_map
