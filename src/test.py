from stockfish import Stockfish
from tracking.Board import Board

stockfish = Stockfish()

moves = []
while True:
    fen = stockfish.get_fen_position()
    move = stockfish.get_best_move_time(200)
    moves.append(move)
    if move is None:
        break
    stockfish.set_position(moves)
    fen_2 = stockfish.get_fen_position()
    print()
    print(move)
    print(Board.get_move_from_fen_positions(fen, fen_2))
