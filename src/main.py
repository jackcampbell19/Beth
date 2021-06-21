import pathlib
import json
import time
from sys import argv, path

src = pathlib.Path(__file__).parent.absolute()
path.append(str(src.parent.absolute()))

from src.tracking.Board import Board, KeyPosition, Square
from src.tracking.Marker import Marker
from src.mechanical.Camera import Camera
from src.mechanical.Gantry import Gantry
from src.misc.Exceptions import BoardPieceViolation
from src.misc.Helpers import *
from src.misc.Log import log

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
        visible_squares=[
            Square(identifier=vs['id'], corners=vs['corners'])
            for vs in kp['visible-squares']
        ]
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
    fid_to_piece_map=config["fid-piece-mapping"]
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
    grip_sig_pin=config['gantry']['pins']['grip']['sig']
)

"""
Define main functions.
"""


def adjust_markers(markers):
    """
    Adjusts the markers based on the fid correction coefficient matrix.
    :param markers: {list(markers)} List of markers
    :return: Adjusted markers
    """
    frame_center = [x / 2 for x in camera.frame_size]
    for marker in markers:
        x_dis, y_dis = marker.center - frame_center
        x_coefficient, y_coefficient = fcc_map[marker.id] if marker.id in fcc_map else (1, 1)
        x_correction_amount = -(x_coefficient * (x_dis / frame_center[0]))
        y_correction_amount = -(y_coefficient * (y_dis / frame_center[1]))
        marker.adjust(x_correction_amount, y_correction_amount)


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
            for square in key_position.visible_squares:
                if point_lies_in_square(marker.center, square.corners):
                    if square.id in square_contents and square_contents[square.id] != piece_id:
                        raise BoardPieceViolation(f"Two pieces found in the same square: {square.id}")
                    square_contents[square.id] = piece_id
        log.info(f"Found pieces: {square_contents}")
    return square_contents


"""
Execute main function.
"""


def exe_remote_control():
    """
    Allows the user to control the machine from a terminal.
    """
    while True:
        input_str = input('x,y,z: ')
        try:
            x, y, z = map(float, input_str.split(','))
            x, y = map(int, [x, y])
        except ValueError:
            print('Input not valid.')
            continue
        gantry.set_position(x, y)
        gantry.set_z_position(z)


def exe_capture_key_position_images():
    gantry.calibrate()
    for key_position in key_positions:
        x, y = key_position.gantry_position
        gantry.set_position(x, y)
        frame = camera.capture_frame()
        save_frame_to_runtime_dir(frame, calibration=True, name=f"key-position-{x}x{y}.jpg")


def exe_main():
    # Perform mechanical calibration
    log.info('Performing gantry calibration.')
    gantry.calibrate()


if __name__ == "__main__":
    SAVE_OUTPUT = '--save-output' in argv
    if SAVE_OUTPUT:
        log.SAVE_OUTPUT = True
        log.info('Save output enabled.')
    try:
        if '--remote-control' in argv:
            exe_remote_control()
        elif '--capture-key-position-images' in argv:
            exe_capture_key_position_images()
        else:
            exe_main()
    except KeyboardInterrupt:
        log.info('Program ended due to KeyboardInterrupt.')
        exit(0)
