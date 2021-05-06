import json
import numpy as np

from Gantry import Gantry
from Board import Board
from Camera import Camera
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
    index=0,
    size=[1920, 1080],
    k=config['camera']['calibration']['k'],
    d=config['camera']['calibration']['d'],
    distance_calibration=config['camera']['calibration']['distance']
)
# Init the board
board = Board(
    tl_fid=config['board-corner-fid-mapping']['top-left'],
    tr_fid=config['board-corner-fid-mapping']['top-right'],
    bl_fid=config['board-corner-fid-mapping']['bottom-left'],
    br_fid=config['board-corner-fid-mapping']['bottom-right'],
    fid_to_piece_map=config["fid-piece-mapping"]
)
# Init the gantry
gantry = Gantry(
    size=config['gantry']['size'],
    x_pins=config['gantry']['x-pins'],
    y_pins=config['gantry']['y-pins']
)


"""
Execute main function.
"""


def move_to_target_no_info(target_fid, proximity_threshold, units):
    # Take snapshot to get all of the markers present
    markers, center = camera.take_snapshot()
    # If marker is not present return
    if target_fid not in markers:
        log.error('Target marker not found.')
        return
    # Store initial positions
    target_start_position = markers[target_fid].center.copy()
    arm_start_position = gantry.current_position.copy()
    # Calculate the vector between the current position and the target markers position using arbitrary units
    direction_vector = markers[target_fid].center - center
    direction_vector *= -1
    # If the point is within the allowed distance from the center return
    if np.linalg.norm(direction_vector) < proximity_threshold:
        log.info(f"Target marker is within {proximity_threshold} units of the center of the frame.")
        return
    # Convert the direction vector from floats to ints
    direction_vector *= 1.0 / np.linalg.norm(direction_vector) * units
    direction_vector = direction_vector.astype(int)
    log.debug(direction_vector)
    # Move the arm along this vector
    gantry.move_along_vector(direction_vector)
    # Take snapshot to get all of the markers present
    markers, center = camera.take_snapshot()
    # If marker is not present, reset the position and call the function again to ensure the new position is in frame
    if target_fid not in markers:
        log.warn('Marker out of frame. Reverting position.')
        gantry.move_along_vector(-direction_vector)
        move_to_target_no_info(target_fid, proximity_threshold, units - 10)
        return
    # Store new position
    target_end_position = markers[target_fid].center.copy()
    arm_end_position = gantry.current_position.copy()
    # Calculate observed distances
    arm_actual_distance = np.linalg.norm(arm_end_position - arm_start_position)
    target_observed_distance = np.linalg.norm(target_end_position - target_start_position)
    log.debug(f"arm_actual_distance: {arm_actual_distance}, target_observed_distance: {target_observed_distance}")
    # Move back and move to scaled position
    scalar = arm_actual_distance / target_observed_distance
    gantry.move_along_vector(-direction_vector)
    adjusted_vector = direction_vector * scalar
    adjusted_vector = adjusted_vector.astype(int)
    gantry.move_along_vector(adjusted_vector)
    # Check how far it is from the target
    markers, center = camera.take_snapshot()
    target_final_position = markers[target_fid].center.copy()
    arm_final_position = gantry.current_position.copy()
    target_distance_from_center = np.linalg.norm(center - target_final_position)
    log.debug(f"Distance from center: {target_distance_from_center}")


if __name__ == "__main__":
    # Perform mechanical calibration
    gantry.calibrate()

    move_to_target_no_info("5", 5, 800)
