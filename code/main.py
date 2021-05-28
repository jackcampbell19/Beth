import json

from Board import Board
from Camera import Camera
from Gantry import Gantry
from Log import log


"""
Initialize global objects using the config file.
"""
log.info('Initializing components.')
# Read the config file
f = open("config.json")
config = json.load(f)
f.close()
# Init the camera
camera = Camera(
    input_index=0,
    frame_size=[config['camera']['width'], config['camera']['height']],
    k=config['camera']['calibration']['k'],
    d=config['camera']['calibration']['d'],
    fid_correction_coefficient_map=config['camera']['calibration']['fid-correction-coefficients']
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


"""
Execute main function.
"""


if __name__ == "__main__":
    # Perform mechanical calibration
    gantry.calibrate()

    gantry.set_position(1800, 0)
