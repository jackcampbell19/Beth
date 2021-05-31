import json

from Board import Board, KeyPosition, Square
from Camera import Camera
from Gantry import Gantry
from Log import log
from Helpers import *
from Marker import Marker
from sys import argv


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
    corner_fids=(
        config['board-corner-fid-mapping']['top-left'],
        config['board-corner-fid-mapping']['top-right'],
        config['board-corner-fid-mapping']['bottom-left'],
        config['board-corner-fid-mapping']['bottom-right']
    ),
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
    )
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
        x_correction_amount = -(x_coefficient * (x_dis / (camera.frame_size[0] / 2)))
        y_correction_amount = -(y_coefficient * (y_dis / (camera.frame_size[1] / 2)))
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
    return markers


"""
Execute main function.
"""


def exe_main():
    if SAVE_OUTPUT:
        log.SAVE_OUTPUT = True
        log.info('Save output enabled. All output will be saved.')
    # Perform mechanical calibration
    log.info('Performing gantry calibration.')
    gantry.calibrate()

    # TODO: Temporary test code
    for key_position in key_positions:
        x, y = key_position.gantry_position
        gantry.set_position(x, y)
        frame = camera.capture_frame()
        save_frame_to_runtime_dir(frame)



if __name__ == "__main__":
    SAVE_OUTPUT = '--save-output' in argv
    exe_main()
