from stockfish import Stockfish
from Board import Board

stockfish = Stockfish()

print(stockfish.get_board_visual())

fen = Board.get_fen_position({'c4': 'P', 'g4': 'N', 'e5': 'Q', 'e3': 'K', 'a3': 'B', 'h3': 'R', 'd7': 'k'})
print(fen)

stockfish.set_fen_position(fen)
print(stockfish.get_board_visual())

move = stockfish.get_best_move_time(3000)
print(f"Move: {move}")


