import pathlib
import json
from sys import argv, path

src = pathlib.Path(__file__).parent.absolute()
path.append(str(src.parent.absolute()))

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
SAVE_OUTPUT = False
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
        sid_fid_mapping=kp['square-calibration-fid-mapping']
    )
    for kp in config['key-positions']
]
z_axis_extension = config['z-axis-piece-extension']
# Init the camera
camera = Camera(
    camera_index=0,
    frame_size=[config['camera']['width'], config['camera']['height']],
    k=config['camera']['calibration']['k'],
    d=config['camera']['calibration']['d']
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
        gantry.set_z_position(0)
        gantry.set_position(100, 100)
        gantry.set_z_position(1)
        gantry.release_grip()
        gantry.set_z_position(0)
    gantry.set_position(sx, sy)
    extension_amount = get_extension_amount(board_state[s])
    gantry.set_z_position(extension_amount)
    gantry.engage_grip()
    gantry.set_z_position(0)
    gantry.set_position(ex, ey)
    gantry.set_z_position(extension_amount)
    gantry.release_grip()
    gantry.set_z_position(0)


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


def take_snapshot():
    """
    Captures a frame and returns a map of all markers present in the frame
    as well as the coordinate in the center of the frame.
    :return: [Marker] A list of markers
    """
    log.info('Taking snapshot from camera.')
    frame = camera.capture_frame()
    markers = Marker.extract_markers(frame)
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
        if save_images:
            save_frame_to_runtime_dir(frame, camera)
        for marker in markers:
            piece_id = board.translate_fid_to_piece(marker.id)
            sid = key_position.get_closest_sid(marker.center)
            if sid in board_state and board_state[sid] != piece_id:
                raise BoardPieceViolation(f"Two pieces found in the same square: {sid}")
            board_state[sid] = piece_id
    log.info(f"Board state: {board_state}")
    return board_state


def verify_initial_state():
    pass


def wait_for_player_turn():
    # TODO: replace with proper button
    gantry.x_stop.wait_until_pressed()


def play_game():
    state_history = [Board.fen_to_board_state('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')]
    moves = []
    stockfish = generate_stockfish_instance()
    verify_initial_state()
    while True:
        wait_for_player_turn()
        board_state = get_board_state()
        previous_state = state_history[-1]
        try:
            detected_move = Board.get_move_from_board_states(previous_state, board_state)
        except InvalidMove:
            log.error('Invalid move detected.')
            continue
        state_history.append(board_state)
        moves.append(detected_move)
        stockfish.set_position(moves)
        generated_move = stockfish.get_best_move_time(2)
        if generated_move is None:
            break
        make_move(generated_move, board_state)


"""
Define exe function.
"""


def exe_capture_calibration_image(name):
    save_frame_to_runtime_dir(camera.capture_frame(), camera, calibration=True, name=name)


def exe_remote_control():
    """
    Allows the user to control the machine from a terminal.
    """
    gantry.calibrate()
    while True:
        mode = input('Coordinate / Position (c/p): ')
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
        markers = Marker.extract_markers(frame)
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
        exe_capture_calibration_image(f"key-position-{x}x{y}")
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
        AUDIO_IDS.WAKEUP,
        AUDIO_IDS.CALIBRATION_0
    )
    # Wait for stops to be pressed
    gantry.x_stop.wait_until_pressed()
    play_audio_ids(AUDIO_IDS.CALIBRATION_1)
    gantry.y0_stop.wait_until_pressed()
    play_audio_ids(AUDIO_IDS.CALIBRATION_2)
    gantry.y1_stop.wait_until_pressed()
    play_audio_ids(AUDIO_IDS.CALIBRATION_3)
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
        play_game()


"""
Execute main function.
"""


if __name__ == "__main__":
    cleanup_runtime_dir()
    log.info(f"Program begin, argv: {argv}")
    SAVE_OUTPUT = '--save-output' in argv
    if SAVE_OUTPUT:
        log.SAVE_OUTPUT = True
        log.info('Save output enabled.')
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
        elif '--play-audio' in argv:
            i = argv.index('--play-audio') + 1
            play_audio_ids(*argv[i].split(' '))
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
            print(s.get_board_visual())
        elif '--capture-frame' in argv:
            frame = camera.capture_frame(correct_distortion='--raw-image' not in argv)
            if '--show-markers' in argv:
                markers = Marker.extract_markers(frame)
                draw_markers(frame, markers, point_only=True, primary_color=(255, 0, 0), secondary_color=(255, 0, 0))
                adjust_markers(markers)
                draw_markers(frame, markers, point_only=True, primary_color=(0, 255, 0), secondary_color=(0, 255, 0))
            save_frame_to_runtime_dir(frame, camera)
        elif '--capture-camera-distortion-images' in argv:
            for i in range(12):
                gantry.set_z_position(30)
                gantry.set_z_position(0)
                frame = camera.capture_frame(correct_distortion=False)
                save_frame_to_runtime_dir(frame, camera, calibration=True, name=f"cam-dis-{i}")
        elif '--test-exposure' in argv:
            #for x in [0.0005, 0.001, 0.002, 0.003, 0.004, 0.005, 0.006]:
            for x in [0.002, 0.004, 0.01]:
                f = camera.capture_frame(exposure=x, correct_distortion=False)
                norm_image = cv2.normalize(f, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)
                print(f)
                print('\n\n\n')
                print(norm_image)
                save_frame_to_runtime_dir(f, camera, name=x)
                m = Marker.extract_markers(f)
                draw_markers(f, m)
                save_frame_to_runtime_dir(f, camera, name=f"{x}-markers")
                save_frame_to_runtime_dir(norm_image, camera, name=f"{x}-norm")
        else:
            exe_main()
    except KeyboardInterrupt:
        log.info('Program ended due to KeyboardInterrupt.')
        exit(0)
    # Return gantry to origin and cleanup gpio
    gantry.set_position(0, 0)
    gantry.set_z_position(0)
    gantry.release_grip()
