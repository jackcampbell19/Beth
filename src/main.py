import pathlib
import json
from sys import argv, path

src = pathlib.Path(__file__).parent.absolute()
path.append(str(src.parent.absolute()))

from src.tracking.Board import Board, KeyPosition, Square
from src.tracking.Marker import Marker
from src.mechanical.Camera import Camera
from src.mechanical.Gantry import Gantry
from src.mechanical.CatFoot import cleanup
from src.misc.Exceptions import BoardPieceViolation, InvalidMove
from src.misc.Helpers import *
from src.calibration.Calibration import calculate_fid_correction_coefficients
from src.misc.Log import log
from random import randint


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


def make_move(move):
    if len(move) != 4:
        raise InvalidMove(f"{move}")
    s, e = move[:2], move[2:]
    sx, sy = board.get_square_location(s)
    ex, ey = board.get_square_location(e)
    gantry.set_position(sx, sy)


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


def analyze_board():
    """
    Analyzes the board to find where all the pieces are.
    For each key position, move the gantry to that position, take a
    snapshot and locate the position of each of the visible pieces.
    :return: [square_id: fid] A map of square ids to piece ids.
    """
    log.info('Analyzing board.')
    square_contents = {}
    for key_position in key_positions:
        x, y = key_position.gantry_position
        gantry.set_position(x, y)
        markers, frame = take_snapshot()
        for marker in markers:
            piece_id = board.translate_fid_to_piece(marker.id)
            sid = key_position.get_closest_sid(marker.center)
            if sid in square_contents and square_contents[sid] != piece_id:
                raise BoardPieceViolation(f"Two pieces found in the same square: {sid}")
            square_contents[sid] = piece_id
        log.info(f"Found pieces: {square_contents}")
    return square_contents


"""
Execute main function.
"""


def exe_capture_calibration_image(name):
    save_frame_to_runtime_dir(camera.capture_frame(), name=name, calibration=True)


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
        save_frame_to_runtime_dir(frame, calibration=True, name=f"key-position-{x}x{y}")
        log.info(f"Visible squares for key position at {key_position.gantry_position}:\n{json.dumps(sid_center_positions)}")
    gantry.set_position(0, 0)


def exe_determine_current_position():
    x, y = gantry.calibrate()
    log.info(f"Gantry was at position {x}, {y}")


def exe_main():
    # Perform mechanical calibration
    log.info('Performing gantry calibration.')
    _ = gantry.calibrate()


if __name__ == "__main__":
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
        elif '--capture-frame' in argv:
            camera.mock_frame_path = str(CALIBRATION_DIR.joinpath('all.jpg').absolute())
            frame = camera.capture_frame(correct_distortion='--raw-image' not in argv)
            if '--show-markers' in argv:
                markers = Marker.extract_markers(frame)
                draw_markers(frame, markers, point_only=True, primary_color=(255, 0, 0), secondary_color=(255, 0, 0))
                adjust_markers(markers)
                draw_markers(frame, markers, point_only=True, primary_color=(0, 255, 0), secondary_color=(0, 255, 0))
            save_frame_to_runtime_dir(
                frame, name=f"cf-{randint(0, 1000)}-{log.elapsed_time_raw()}"
            )
        else:
            exe_main()
    except KeyboardInterrupt:
        log.info('Program ended due to KeyboardInterrupt.')
        exit(0)
    # Return gantry to origin and cleanup gpio
    gantry.set_position(0, 0)
    gantry.set_z_position(0)
    gantry.release_grip()
