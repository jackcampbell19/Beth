import pathlib
import json
from sys import argv, path

src = pathlib.Path(__file__).parent.absolute()
path.append(str(src.parent.absolute()))

LOG_DIR = str(src.parent.absolute().joinpath('runtime').absolute().joinpath('logs').absolute())

from src.tracking.Board import Board, KeyPosition
from src.tracking.Marker import Marker
from src.mechanical.Camera import Camera
from src.mechanical.Gantry import Gantry
from src.misc.Exceptions import BoardPieceViolation, InvalidMove
from src.misc.Helpers import *
from src.calibration.Calibration import calculate_fid_correction_coefficients
from src.misc.Log import log
from src.audio.Audio import play_audio_ids, AUDIO_IDS
from stockfish import Stockfish


"""
Print out the help message if requested and terminate the program.
"""
if '--help' in argv:
    readme = open(str(src.parent.joinpath('README.md').absolute()))
    print('Flags:')
    for line in readme.readlines():
        if line.startswith('#### `--'):
            print('  • ', line[6:-2])
    exit(0)


"""
Initialize global objects/variables using the config file.
"""
log.info('Initializing components.')
# Read the config file
f = open(str(src.parent.joinpath('config.json').absolute()))
config = json.load(f)
f.close()
# Extract global variables from the config file
fcc_map = config['fid-correction-coefficients']
key_positions = [
    KeyPosition(
        position=kp['gantry-position'],
        sid_centers=kp['sid-centers'],
        sid_fid_mapping=kp['square-calibration-fid-mapping'],
        x_range=kp['x-range'],
        y_range=kp['y-range']
    )
    for kp in config['key-positions']
]
extension_values = config['z-axis-extension']
min_extension = extension_values['min']
max_extension = extension_values['max']
z_axis_extension = {p: max_extension - extension_values[p] for p in 'prnbkq'}
game_options_map = config['game-options']
# Init the camera
camera = Camera(
    camera_index=0,
    frame_size=[config['camera']['width'], config['camera']['height']],
    k=config['camera']['calibration']['k'],
    d=config['camera']['calibration']['d'],
    frame_center=config['camera']['corrected-center']
)
# Init the board
board = Board(
    fid_to_piece_map=config['fid-piece-mapping'],
    a1_position=config['known-square-positions']['a1'],
    h1_position=config['known-square-positions']['h1'],
    a8_position=config['known-square-positions']['a8'],
    h8_position=config['known-square-positions']['h8']
)
# Init the gantry
gantry = Gantry(
    size=(
        config['gantry']['size']['x'],
        config['gantry']['size']['y']
    ),
    stp_pins=(
        config['gantry']['pins']['x']['stp'],
        config['gantry']['pins']['y']['stp'][0],
        config['gantry']['pins']['y']['stp'][1]
    ),
    dir_pins=(
        config['gantry']['pins']['x']['dir'],
        config['gantry']['pins']['y']['dir'][0],
        config['gantry']['pins']['y']['dir'][1]
    ),
    z_sig_pin=config['gantry']['pins']['z']['sig'],
    grip_sig_pin=config['gantry']['pins']['grip']['sig'],
    x_stop_pin=config['gantry']['pins']['stops']['x'],
    y0_stop_pin=config['gantry']['pins']['stops']['y0'],
    y1_stop_pin=config['gantry']['pins']['stops']['y1']
)

"""
Define main functions.
"""


def generate_stockfish_instance():
    return Stockfish('/home/pi/stockfish')


def get_extension_amount(piece):
    piece = piece.lower()
    if piece in z_axis_extension:
        return z_axis_extension[piece]
    else:
        return 1


def make_move(move, board_state):
    if len(move) != 4:
        raise InvalidMove(f"{move}")
    s, e = move[:2], move[2:]
    sx, sy = board.get_square_location(s)
    ex, ey = board.get_square_location(e)
    if e in board_state:
        extension_amount = get_extension_amount(board_state[e])
        gantry.set_position(ex, ey)
        gantry.set_z_position(extension_amount)
        gantry.engage_grip()
        gantry.set_z_position(min_extension)
        gantry.set_position(100, 100)
        gantry.set_z_position(max_extension)
        gantry.release_grip()
        gantry.set_z_position(min_extension)
    gantry.set_position(sx, sy)
    extension_amount = get_extension_amount(board_state[s])
    gantry.set_z_position(extension_amount)
    gantry.engage_grip()
    gantry.set_z_position(min_extension)
    gantry.set_position(ex, ey)
    gantry.set_z_position(extension_amount)
    gantry.release_grip()
    gantry.set_z_position(min_extension)


def adjust_markers(markers):
    """
    Adjusts the markers based on the fid correction coefficient matrix.
    :param markers: {list(markers)} List of markers
    :return: Adjusted markers
    """
    frame_center = np.array([x / 2 for x in camera.frame_size])
    for marker in markers:
        vector = marker.center - frame_center
        coefficient = fcc_map[marker.id] if marker.id in fcc_map else 1
        marker.center = np.array([int(x) for x in frame_center + vector * coefficient])


def filter_markers_by_range(markers, x_range, y_range):
    return list(filter(
        lambda m: (x_range[0] <= m.center[0] <= x_range[1]) and (y_range[0] <= m.center[1] <= y_range[1]),
        markers
    ))


def filter_markers_by_id(markers, valid_ids):
    return list(filter(
        lambda m: m.id in valid_ids,
        markers
    ))


def take_snapshot():
    """
    Captures a frame and returns a map of all markers present in the frame
    as well as the coordinate in the center of the frame.
    :return: [Marker] A list of markers
    """
    log.info('Taking snapshot from camera.')
    frame = camera.capture_frame()
    markers = Marker.extract_markers(frame, marker_family=Marker.FAMILY_tag16h5, scan_for_inverted_markers=True)
    adjust_markers(markers)
    return markers, frame


def get_board_state(save_images=False):
    """
    Analyzes the board to find where all the pieces are.
    For each key position, move the gantry to that position, take a
    snapshot and locate the position of each of the visible pieces.
    :return: [square_id: piece.id] A map of square ids to piece ids.
    """
    log.info('Analyzing board.')
    board_state = {}
    for key_position in key_positions:
        x, y = key_position.gantry_position
        gantry.set_position(x, y)
        markers, frame = take_snapshot()
        markers = filter_markers_by_range(markers, x_range=key_position.x_range, y_range=key_position.y_range)
        markers = filter_markers_by_id(markers, valid_ids=board.piece_fids)
        if save_images:
            draw_markers(frame, markers, board=board)
            save_frame_to_runtime_dir(frame, camera)
        for marker in markers:
            piece_id = board.translate_fid_to_piece(marker.id)
            sid = key_position.get_closest_sid(marker.center)
            if sid in board_state and board_state[sid] != piece_id:
                raise BoardPieceViolation(f"Two pieces ({board_state[sid]}, {piece_id}) found in the same square: {sid}")
            board_state[sid] = piece_id
    log.info(f"Board state: {board_state}")
    return board_state


def setup_board():
    log.info('Setting up board.')
    start_state = Board.get_starting_board_state()
    board_state = get_board_state()
    # For each sid, move a piece that is in an incorrect location to the correct location
    for s_sid, s_piece in start_state.items():
        # Get sids that do not have pieces in them
        free_sids = [sid for sid in Board.get_all_sids() if sid not in board_state]
        # s_piece = correct piece for s_sid, b_piece = current piece in sid
        b_piece = board_state[s_sid] if s_sid in board_state else None
        # If the board piece is the same as the start piece, continue
        if b_piece == s_piece:
            continue
        # If there is an incorrect piece in the sid, move it to a free space
        if b_piece is not None:
            f_sid = free_sids.pop(0)
            make_move(f"{s_sid}{f_sid}", board_state)
            del board_state[s_sid]
            board_state[f_sid] = b_piece
        # Get sids of pieces incorrectly located
        i_sids = [
            sid for sid, piece in board_state.items()
            if piece == s_piece and (sid not in start_state or start_state[sid] != piece)
        ]
        # If there are none on the board, continue
        if len(i_sids) == 0:
            continue
        # Make the move
        i_sid = i_sids[0]
        make_move(f"{i_sid}{s_sid}", board_state)
        del board_state[i_sid]
        board_state[s_sid] = s_piece


def verify_initial_state():
    pass


def wait_for_player_button_press():
    # TODO: replace with proper button
    gantry.x_stop.wait_until_pressed()
    play_audio_ids(AUDIO_IDS.DING)


def play_game():
    """
    Game play logic.
    """
    # Initialize state history, move list, and chess engine. Then verify the board is in starting position.
    state_history = [Board.get_starting_board_state()]
    moves = []
    stockfish = generate_stockfish_instance()
    verify_initial_state()
    # Begin the game
    play_audio_ids(
        AUDIO_IDS.BEFORE_GAME,
        AUDIO_IDS.GOOD_LUCK
    )
    best_player_move = None
    while True:
        log.info('Waiting for player move')
        wait_for_player_button_press()
        # Analyze the board to get the board state. If it fails, retry once before asking for the user
        # to intervene. Repeat until board state can be captured.
        attempts = 0
        should_request_user_intervention = False
        while True:
            attempts += 1
            if should_request_user_intervention:
                should_request_user_intervention = False
                play_audio_ids(AUDIO_IDS.USER_CHECK_BOARD)
                log.info('Requesting user intervention.')
                wait_for_player_button_press()
            try:
                board_state = get_board_state(save_images=True)
                break
            except BoardPieceViolation as error:
                log.error(error)
                if attempts % 2 == 0:
                    should_request_user_intervention = True
        # Get previous state in order to extract the move made by the player and add it to the move list
        previous_state = state_history[-1]
        log.debug(f"Previous state: {Board.board_state_to_fen(previous_state)}")
        log.debug(f"Board state: {Board.board_state_to_fen(board_state)}")
        try:
            detected_move = Board.get_move_from_board_states(previous_state, board_state)
        except InvalidMove:
            log.error('Invalid move detected.')
            play_audio_ids(AUDIO_IDS.INVALID_MOVE)
            continue
        log.info(f"Detected move {detected_move} from player")
        state_history.append(board_state)
        moves.append(detected_move)
        log.debug(f"Previous moves: {','.join(moves)}")
        # Update the chess engine with the latest moves
        stockfish.set_position(moves)
        log.debug(f"Making move from current board:\n{stockfish.get_board_visual()}{stockfish.get_fen_position()}")
        # Generate the best move, append it to the moves list
        generated_move = stockfish.get_best_move_time(2)
        if generated_move is None:
            play_audio_ids(AUDIO_IDS.LOST)
            log.info('Player won.')
            break
        moves.append(generated_move)
        log.info(f"Moves: {','.join(moves)}")
        stockfish.set_position(moves)
        state_history.append(Board.fen_to_board_state(stockfish.get_fen_position()))
        # Generate the best move for the player to take next
        best_player_move = stockfish.get_best_move_time(1)
        if best_player_move is None:
            play_audio_ids(AUDIO_IDS.WON)
            break
        # Make the move
        log.info(f"Making move {generated_move}")
        make_move(generated_move, board_state)
        x, y = key_positions[0].gantry_position
        gantry.set_position(x, y)


def check_for_game_options():
    return
    x, y = key_positions[0].gantry_position
    gantry.set_position(x, y)
    play_audio_ids(AUDIO_IDS.OPTIONS_CHECK)
    wait_for_player_button_press()
    frame = camera.capture_frame()
    markers = Marker.extract_markers(frame, Marker.FAMILY_tag36h11)
    for marker in markers:
        if marker.id in game_options_map:
            option = game_options_map[marker.id]
            log.info(f"Game option found '{option}'")
            if option == 'level-easy':
                pass
            elif option == 'level-medium':
                pass
            elif option == 'level-hard':
                pass
            elif option == 'level-advanced':
                pass


"""
Define exe function.
"""


def exe_capture_calibration_image(name):
    save_frame_to_runtime_dir(camera.capture_frame(), calibration=True, name=name, name_only=True)


def exe_remote_control():
    """
    Allows the user to control the machine from a terminal.
    """
    gantry.calibrate()
    while True:
        mode = input('Coordinate / Position (c/p/z): ')
        if mode == 'c':
            while True:
                input_str = input('x,y,z: ')
                if input_str == 'back':
                    break
                try:
                    x, y, z = map(float, input_str.split(','))
                    x, y = map(int, [x, y])
                except ValueError:
                    print('Input not valid.')
                    continue
                gantry.set_position(x, y)
                gantry.set_z_position(z)
        elif mode == 'p':
            while True:
                position = input('Position: ')
                if position == 'back':
                    break
                x, y = board.get_square_location(position)
                gantry.set_position(x, y)
        elif mode == 'z':
            while True:
                position = float(input('%: ')) / 100
                if position == 'back':
                    break
                gantry.set_z_position(position)
        else:
            print('Inout not valid.')


def exe_capture_key_position_images():
    """
    Captures the key position and returns positional data from the calibration grid.
    """
    _ = gantry.calibrate()
    for key_position in key_positions:
        x, y = key_position.gantry_position
        gantry.set_position(x, y)
        frame = camera.capture_frame()
        markers = Marker.extract_markers(frame, marker_family=Marker.FAMILY_tag36h11)
        sid_center_positions = {}
        for sid in key_position.sid_fid_mapping:
            fid = key_position.sid_fid_mapping[sid]
            found_markers = list(filter(lambda m: m.id == fid, markers))
            if len(found_markers) != 1:
                log.error(f"Found {len(found_markers)} markers with fid '{fid}'.")
                continue
            marker = found_markers[0]
            sid_center_positions[sid] = list([int(v) for v in marker.center])
            draw_markers(frame, [marker])
        save_frame_to_runtime_dir(frame, camera, calibration=True, name=f"key-position-{x}x{y}")
        log.info(f"Visible squares for key position at {key_position.gantry_position}:\n{json.dumps(sid_center_positions)}")
    gantry.set_position(0, 0)


def exe_determine_current_position():
    """
    Logs the current position of the gantry.
    """
    x, y = gantry.calibrate()
    log.info(f"Gantry was at position {x}, {y}")


def exe_main():
    gantry.set_position(100, 100, rel=True, slow=True)
    play_audio_ids(
        AUDIO_IDS.START_MESSAGE,
        AUDIO_IDS.PAUSE_HALF_SECOND,
        AUDIO_IDS.WAKEUP
    )
    # Perform mechanical calibration
    log.info('Performing gantry calibration.')
    _ = gantry.calibrate()
    play_audio_ids(
        AUDIO_IDS.CALIBRATION_COMPLETE,
        AUDIO_IDS.PAUSE_HALF_SECOND,
        AUDIO_IDS.SASS_0,
        AUDIO_IDS.PAUSE_HALF_SECOND,
        AUDIO_IDS.HAHA,
        AUDIO_IDS.PAUSE_HALF_SECOND
    )
    # Start playing sequence
    while True:
        gantry.set_position(200, 200)
        check_for_game_options()
        play_game()


"""
Execute main function.
"""


if __name__ == "__main__":
    log.enable_save_output(path=LOG_DIR)
    cleanup_runtime_dir()
    log.info(f"Program begin, argv: {argv}")
    try:
        if '--remote-control' in argv:
            exe_remote_control()
        elif '--capture-key-positions' in argv:
            exe_capture_key_position_images()
        elif '--capture-fcc-top' in argv:
            exe_capture_calibration_image('fcc-top')
        elif '--capture-fcc-base' in argv:
            exe_capture_calibration_image('fcc-base')
        elif '--calculate-fcc' in argv:
            calculate_fid_correction_coefficients(camera.frame_center)
        elif '--determine-current-position' in argv:
            exe_determine_current_position()
        elif '--make-move' in argv:
            gantry.calibrate()
            i = argv.index('--make-move') + 1
            move = argv[i]
            s, e = move[:2], move[2:]
            state_info = list(argv[i + 1])
            state = {
                s: state_info[0]
            }
            if len(state_info) == 2:
                state[e] = state_info[1]
            make_move(move, state)
        elif '--get-board-state' in argv:
            gantry.calibrate()
            state = get_board_state(save_images=True)
            s = generate_stockfish_instance()
            s.set_fen_position(Board.board_state_to_fen(state))
            log.info('Board state:\n' + s.get_board_visual())
        elif '--capture-frame' in argv:
            frame = camera.capture_frame(correct_distortion='--raw-image' not in argv)
            if '--show-markers' in argv:
                tag = Marker.FAMILY_tag36h11 if '--36h11' in argv else Marker.FAMILY_tag16h5
                markers = Marker.extract_markers(frame, marker_family=tag, scan_for_inverted_markers=True)
                draw_markers(frame, markers, board=board, primary_color=(244, 3, 252), secondary_color=(252, 98, 3))
                adjust_markers(markers)
                draw_markers(frame, markers, point_only=True, primary_color=(107, 252, 3), secondary_color=(107, 252, 3))
            save_frame_to_runtime_dir(frame, camera)
        elif '--capture-camera-distortion-images' in argv:
            for i in range(12):
                frame = camera.capture_frame(correct_distortion=False)
                save_frame_to_runtime_dir(frame, camera, calibration=True, name=f"cam-dis-{i}")
        elif '--play-self' in argv:
            _ = gantry.calibrate()
            moves = []
            stockfish = generate_stockfish_instance()
            while True:
                stockfish.set_position(moves)
                move = stockfish.get_best_move_time(1)
                if move is None:
                    break
                log.info(f"Making move: {move}")
                make_move(move, board_state=Board.fen_to_board_state(stockfish.get_fen_position()))
                moves.append(move)
        elif '--setup-board' in argv:
            gantry.calibrate()
            setup_board()
        else:
            exe_main()
    except KeyboardInterrupt:
        log.info('Program ended due to KeyboardInterrupt.')
    except Exception as e:
        log.error(f"Program execution failed. {e}")
    # Return gantry to origin and cleanup gpio
    gantry.set_z_position(min_extension)
    gantry.set_position(0, 0)
    gantry.release_grip()
    # Close the log file
    log.close_file()
