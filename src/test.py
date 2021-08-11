from stockfish import Stockfish

import pathlib
from sys import path

src = pathlib.Path(__file__).parent.absolute()
path.append(str(src.parent.absolute()))

from src.tracking.Board import Board

stockfish = Stockfish()


# stockfish.set_fen_position('rnbqkbnr/ppppp1pp/8/5p2/4P3/8/PPPP1PP1/RNBQKBNR b - - 0 1')
stockfish.set_fen_position('rnbqkb1r/ppppp1pp/8/2n5/4K3/8/8/R7 b - - 0 1')
print(stockfish.get_board_visual())
move = stockfish.get_best_move_time(1000)
print(move)


# moves = []
# while True:
#     fen = stockfish.get_fen_position()
#     move = stockfish.get_best_move_time(200)
#     moves.append(move)
#     if move is None:
#         break
#     stockfish.set_position(moves)
#     fen_2 = stockfish.get_fen_position()
#     print()
#     print(move)
#     print(Board.get_move_from_fen_positions(fen, fen_2))
