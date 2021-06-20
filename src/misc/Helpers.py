from Log import log
from PIL import Image
import numpy as np
import cv2
import random
import os


RUNTIME_DIR_PATH = "./runtime"


def ensure_runtime_dir_exists(func):
    """
    Creates the runtime dir if it does not exist.
    """
    def wrapper(*args, **kwargs):
        if not os.path.exists(RUNTIME_DIR_PATH):
            os.mkdir(RUNTIME_DIR_PATH)
        func(*args, **kwargs)
    return wrapper


@ensure_runtime_dir_exists
def save_frame_to_runtime_dir(frame, name=None):
    """
    Saves a frame to the runtime dir.
    :param frame: THe frame to save.
    """
    data = Image.fromarray(frame)
    path = f"{RUNTIME_DIR_PATH}/{name if name is not None else log.elapsed_time_raw()}.jpg"
    log.info(f"Saving frame to {path}")
    data.save(path)


def stitch_frames_together(frames):
    """
    Stitches frames together and returns the new frame.
    :param frames: {2d np.array} Multidimensional array of frames.
    :return: {np.array} Stitched frame.
    """
    yn, xn, ys, xs, _ = frames.shape
    stitched_frame = np.array(
        [
            [[0, 0, 0] for _ in range(xn * xs)] for _ in range(yn * ys)
        ]
    )
    for x0 in range(xn):
        for y0 in range(yn):
            for x in range(xs):
                for y in range(ys):
                    for i in range(3):
                        stitched_frame[y0 * ys + y, x0 * xs + x][i] = frames[y0, x0][y, x][i]
    return stitched_frame


def draw_markers(frame, markers, point_only=False, primary_color=(100, 255, 0), secondary_color=(150, 150, 255)):
    for marker in markers:
        if not point_only:
            for i in range(4):
                cv2.line(frame, tuple(marker.corners[i]), tuple(marker.corners[(i + 1) % 4]), primary_color, 3)
            cv2.putText(frame, marker.id, tuple(marker.corners[0]), cv2.FONT_HERSHEY_SIMPLEX, 1, secondary_color, 3)
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
