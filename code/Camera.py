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

    def __init__(self, index, size, k, d, distance_calibration):
        """
        Initializes the {Camera} object.
        :param index: The index of the camera to read from.
        :param size: [width, height]
        :param k: Distortion correction k variable
        :param d: Distortion correction d variable
        """
        width, height = size
        self.camera = cv2.VideoCapture(index)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.width = width
        self.height = height
        self.k = np.array(k)
        self.d = np.array(d)
        self.distance_calibration = distance_calibration
        self.mm_per_pixel = 1.0
        self.frame_queue = queue.Queue()
        t = threading.Thread(target=self.frame_reader)
        t.daemon = True
        t.start()

    def frame_reader(self):
        while True:
            ret, frame = self.camera.read()
            if not ret:
                log.error('Frame could not be read from camera.')
                raise CameraError()
            if not self.frame_queue.empty():
                try:
                    # Discard previous unprocessed frame
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
            self.frame_queue.put(frame)

    def correct_distortion(self, frame):
        """
        Corrects distortion due to curved lenses using the distortion variables.
        :param frame: The frame to correct.
        :return: The corrected frame.
        """
        log.info('Correcting camera distortion on frame.')
        m1, m2 = cv2.fisheye.initUndistortRectifyMap(self.k,
                                                     self.d,
                                                     np.eye(3),
                                                     self.k,
                                                     (self.width, self.height),
                                                     cv2.CV_16SC2)
        undistorted_img = cv2.remap(frame, m1, m2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        return undistorted_img

    def capture_frame(self, correct_distortion=True):
        """
        Captures a raw frame from the camera.
        :param correct_distortion: Tell the function if it should correct for distortion.
        :return: np array of pixel data
        """
        # self.camera.release()
        # self.camera = cv2.VideoCapture(0)
        log.info(f"Capturing frame from camera with"
                 f"{'' if correct_distortion else ' no'} distortion correction.")
        frame = self.frame_queue.get()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if correct_distortion:
            frame = self.correct_distortion(frame)
        return frame

    def take_snapshot(self):
        """
        Captures a frame and returns a map of all markers present in the frame
        as well as the coordinate in the center of the frame.
        :return:
        """
        log.info('Taking snapshot from camera.')
        frame = self.capture_frame()
        markers = Camera.extract_markers(frame)
        frame_center = np.array([self.width / 2, self.height / 2])
        return markers, frame_center

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
