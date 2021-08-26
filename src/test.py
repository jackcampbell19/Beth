from stockfish import Stockfish
#
import pathlib
from sys import path

src = pathlib.Path(__file__).parent.absolute()
path.append(str(src.parent.absolute()))

from src.tracking.Board import Board

import cv2

# import chess
#
#
# board = chess.Board('rnbqkbnr/ppppp1pp/8/5p2/4P3/8/PPPP1PP1/RNBQKBNR b - - 0 1')
# est_move =


# stockfish = Stockfish()


# stockfish.set_fen_position('rnbqkbnr/ppppp1pp/8/5p2/4P3/8/PPPP1PP1/RNBQKBNR b - - 0 1')
# stockfish.set_fen_position('rnbqkb1r/ppppp1pp/8/2n5/4K3/8/8/R7 b - - 0 1')
# stockfish.set_fen_position('6q1/1P1p2p1/K5p1/8/1Pp2B1P/1b1P4/3nP3/k1b5 w - - 0 1')
# print(stockfish.get_board_visual())
# move = stockfish.get_best_move_time(200)
# print(move)



# moves = []
# while True:
#     fen = stockfish.get_fen_position()
#     move = stockfish.get_best_move_time(500)
#     if move is None:
#         break
#     moves.append(move)
#     stockfish.set_position(moves)
#     fen_2 = stockfish.get_fen_position()
#     calc_move = Board.get_move_from_fen_positions(fen, fen_2)
#     if move != calc_move:
#         print(move, calc_move)
#         print(fen)
#         print(fen_2)
#         print('badmove')
#     else:
#         print(stockfish.get_board_visual())

import time

frame = cv2.imread('~/Desktop/1629996955271-e0.0040-0.004.jpg', cv2.IMREAD_COLOR)
print(frame)
cv2.imshow('frame', frame)
