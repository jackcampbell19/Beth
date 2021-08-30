from src.misc.Exceptions import BoardPieceViolation
from src.misc.Log import log, Log
from PIL import Image
import numpy as np
import cv2
import os

import pathlib

CURRENT_DIR = pathlib.Path(__file__).parent.absolute()
RUNTIME_DIR_PATH = CURRENT_DIR.parent.parent.joinpath('runtime').absolute()
CALIBRATION_DIR = RUNTIME_DIR_PATH.joinpath('calibration').absolute()
IMAGES_DIR = RUNTIME_DIR_PATH.joinpath('images').absolute()
LOG_DIR = RUNTIME_DIR_PATH.joinpath('logs').absolute()


def ensure_runtime_dir_exists(func):
    """
    Creates the runtime dir if it does not exist. Erases old images and logs.
    """
    def wrapper(*args, **kwargs):
        for path in [RUNTIME_DIR_PATH, CALIBRATION_DIR, IMAGES_DIR, LOG_DIR]:
            if not os.path.exists(path):
                os.mkdir(path)
        func(*args, **kwargs)
    return wrapper


@ensure_runtime_dir_exists
def cleanup_runtime_dir():
    log.info('Cleaning up runtime directory')
    image_retain_milliseconds = 1000 * 30
    for filename in os.listdir(IMAGES_DIR):
        timestamp = filename.split('.')[0].split('-')[0]
        if timestamp.isnumeric():
            timestamp = int(timestamp)
            if Log.current_time_in_milliseconds() - timestamp < image_retain_milliseconds:
                continue
        image_path = str(IMAGES_DIR.joinpath(filename).absolute())
        os.remove(image_path)
        log.info(f"Removed image {filename} from runtime/images")
    log_retain_milliseconds = 60 * 60 * 12 * 1000
    for filename in os.listdir(LOG_DIR):
        timestamp = filename.split('.')[0]
        if timestamp.isnumeric():
            timestamp = int(timestamp)
            if Log.current_time_in_milliseconds() - timestamp < log_retain_milliseconds:
                continue
        log_path = str(LOG_DIR.joinpath(filename).absolute())
        os.remove(log_path)
        log.info(f"Removed image {filename} from runtime/logs")


@ensure_runtime_dir_exists
def save_frame_to_runtime_dir(frame, camera=None, calibration=False, name=None):
    """
    Saves a frame to the runtime dir.
    :param calibration: If true the file will be saved to the calibration dir
    :param name: Name of the file
    :param frame: The frame to save
    :param camera: The camera object used to capture the frame.
    """
    data = Image.fromarray(frame)
    image_name = f"{Log.current_time_in_milliseconds()}"
    if camera is not None:
        image_name += f"-e{str(camera.exposure)[:6]}"
    if name is not None:
        image_name += f"-{name}"
    path = f"{CALIBRATION_DIR if calibration else IMAGES_DIR}/{image_name}.jpg"
    log.info(f"Saving frame to {path}")
    data.save(path)


def draw_markers(frame, markers, board=None, point_only=False, primary_color=(100, 255, 0), secondary_color=(150, 150, 255)):
    for marker in markers:
        if not point_only:
            for i in range(4):
                cv2.line(frame, tuple(marker.corners[i]), tuple(marker.corners[(i + 1) % 4]), primary_color, 3)
            text = marker.id
            if board is not None:
                try:
                    text = board.translate_fid_to_piece(marker.id)
                except BoardPieceViolation:
                    pass
            cv2.putText(frame, text, tuple(marker.corners[0]), cv2.FONT_HERSHEY_SIMPLEX, 1, secondary_color, 3)
        cv2.drawMarker(frame, tuple(marker.center), primary_color, cv2.MARKER_CROSS, 20, 3)


def draw_visible_square(frame, square_data):
    corners = np.array([
        [int(x), int(y)]
        for x, y in square_data.corners
    ])
    p0 = (corners[0] + corners[1]) / 2
    p1 = (corners[2] + corners[3]) / 2
    center = (p0 + p1) / 2
    cv2.polylines(
        frame,
        [corners.reshape((-1, 1, 2))],
        True,
        (240, 120, 40),
        3
    )
    cv2.putText(frame, square_data.id, tuple([int(center[0]), int(center[1])]),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (240, 120, 40), 3)


def point_lies_in_square(point, square_corners):
    x, y = point
    p0, p1, p2, p3 = square_corners
    square_lines = [p0 + p1, p1 + p2, p2 + p3, p3 + p0]
    return all([
        ((y - y0) * (x1 - x0) - (x - x0) * (y1 - y0) > 0)
        for x0, y0, x1, y1 in square_lines
    ])
