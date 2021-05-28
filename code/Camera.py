import cv2
import numpy as np
from PIL import Image
from Exceptions import *
import cv2.aruco as aruco
import time
import queue
import threading

from Log import log
from Marker import Marker


class Camera:
    """
    The {Camera} class is a wrapper for the {VideoCapture} camera from cv2. This
    class does additional computation when reading frames and initializing.
    """

    def __init__(self, input_index, frame_size, k, d, fid_correction_coefficient_map):
        """
        Initializes the {Camera} object.
        :param input_index: The index of the camera to read from.
        :param frame_size: [width, height]
        :param k: Distortion correction k variable
        :param d: Distortion correction d variable
        :param fid_correction_coefficient_map: fid correction coefficient map
        """
        self.frame_size = frame_size
        self.index = input_index
        self.k = np.array(k)
        self.d = np.array(d)
        self.fcc_map = fid_correction_coefficient_map
        self.mock_frame_path = None
        self.latest_frame = None
        self.frame_center = np.array([self.frame_size[0] / 2, self.frame_size[1] / 2])

    def generate_camera(self, init_frames=10):
        """
        Generates and returns a new camera instance.
        :param init_frames:
        :return:
        """
        camera = cv2.VideoCapture(self.index)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_size[0])
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_size[1])
        camera.set(cv2.CAP_PROP_FOCUS, 50)
        for _ in range(init_frames):
            camera.read()
        return camera

    def correct_distortion(self, frame):
        """
        Corrects distortion due to curved lenses using the distortion variables 'k' and 'd'.
        :param frame: The frame to correct.
        :return: The corrected frame.
        """
        log.info('Correcting camera distortion on frame.')
        m1, m2 = cv2.fisheye.initUndistortRectifyMap(self.k,
                                                     self.d,
                                                     np.eye(3),
                                                     self.k,
                                                     self.frame_size,
                                                     cv2.CV_16SC2)
        undistorted_img = cv2.remap(frame, m1, m2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        return undistorted_img

    def capture_frame(self, correct_distortion=True):
        """
        Captures a raw frame from the camera.
        :param correct_distortion: Tell the function if it should correct for distortion.
        :return: np array of pixel data
        """
        if self.mock_frame_path is not None:
            log.debug('Camera returning a mock frame in place of the captured image.')
            frame = cv2.imread(self.mock_frame_path)
            self.latest_frame = frame
            return frame
        log.info(f"Capturing frame from camera with"
                 f"{'' if correct_distortion else ' no'} distortion correction.")
        camera = self.generate_camera()
        ret, frame = camera.read()
        for _ in range(100):
            if ret:
                break
            ret, frame = camera.read()
        if not ret:
            raise CameraError('Failed to read from from camera.')
        camera.release()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if correct_distortion:
            frame = self.correct_distortion(frame)
        self.latest_frame = frame
        return frame

    @staticmethod
    def adjust_markers(markers, frame_size, fid_correction_coefficient_map):
        """
        Adjusts the markers based on the fid correction coefficient matrix.
        :param markers: List of markers
        :param frame_size: Size of the frame
        :param fid_correction_coefficient_map: fid correction coefficient map
        :return: Adjusted markers
        """
        frame_center = [x / 2 for x in frame_size]
        for marker in markers.values():
            x_dis, y_dis = marker.center - frame_center
            x_coefficient, y_coefficient = fid_correction_coefficient_map[marker.id] \
                if marker.id in fid_correction_coefficient_map \
                else (1, 1)
            x_correction_amount = -(x_coefficient * (x_dis / (frame_size[0] / 2)))
            y_correction_amount = -(y_coefficient * (y_dis / (frame_size[1] / 2)))
            marker.adjust(x_correction_amount, y_correction_amount)

    def take_snapshot(self):
        """
        Captures a frame and returns a map of all markers present in the frame
        as well as the coordinate in the center of the frame.
        :return:
        """
        log.info('Taking snapshot from camera.')
        frame = self.capture_frame()
        markers = Camera.extract_markers(frame)
        Camera.adjust_markers(markers, self.frame_size, self.fcc_map)
        return markers

    @staticmethod
    def extract_markers(frame, marker_type=aruco.DICT_4X4_1000):
        """
        Extracts all of the markers in given frame and returns a map of fid to marker.
        :param frame: The frame to search.
        :param marker_type: The marker type to search for.
        :return: { "fid": Marker }
        """
        log.info('Extracting aruco markers from camera frame.')
        aruco_dict = aruco.Dictionary_get(marker_type)
        parameters = aruco.DetectorParameters_create()
        corners, ids, _ = aruco.detectMarkers(frame, aruco_dict, parameters=parameters)
        markers = {}
        for x in range(len(corners)):
            fid = str(ids[x][0])
            markers[fid] = Marker(
                    fid,
                    corners[x][0]
                )
        log.info(f"Found {len(corners)} markers: {list(markers.keys())}")
        return markers
