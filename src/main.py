import json

from Board import Board, KeyPosition, Square
from Camera import Camera
from Gantry import Gantry
from Helpers import *
from Marker import Marker
from sys import argv
from Exceptions import BoardPieceViolation
import time


"""
Initialize global objects/variables using the config file.
"""
log.info('Initializing components.')
SAVE_OUTPUT = False
# Read the config file
f = open("config.json")
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


def exe_main():
    if SAVE_OUTPUT:
        log.SAVE_OUTPUT = True
        log.info('Save output enabled.')
    # Perform mechanical calibration
    log.info('Performing gantry calibration.')
    gantry.calibrate()

    # TODO: Temporary test code

    def z_down():
        gantry.set_z_position(1)

    def z_up():
        gantry.set_z_position(0)

    def move_origin():
        gantry.set_position(0, 0)

    def move_pos1():
        gantry.set_position(1200, 0)

    def move_pos2():
        gantry.set_position(1000, 1600)

    z_down()
    gantry.engage_grip()
    z_up()
    move_pos1()
    z_down()
    gantry.release_grip()
    z_up()
    move_origin()
    move_pos1()
    z_down()
    gantry.engage_grip()
    z_up()
    move_origin()
    z_down()
    gantry.release_grip()
    z_up()
    z_down()
    gantry.engage_grip()
    z_up()
    move_pos2()
    z_down()
    gantry.release_grip()
    z_up()
    z_down()
    gantry.engage_grip()
    z_up()
    move_origin()
    z_down()
    gantry.release_grip()
    z_up()



if __name__ == "__main__":
    SAVE_OUTPUT = '--save-output' in argv
    exe_main()
