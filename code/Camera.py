import cv2
import numpy as np
from PIL import Image
from Exceptions import *
import cv2.aruco as aruco
import time

from Log import Log
from Marker import Marker


class Camera:
    """
    The {Camera} class is a wrapper for the {VideoCapture} camera from cv2. This
    class does additional computation when reading frames and initializing.
    """

    def __init__(self, index, width, height, k, d, distance_calibration):
        """
        Initializes the {Camera} object.
        :param index: The index of the camera to read from.
        :param width: The resolution width.
        :param height: The resolution height.
        :param k: Distortion correction k variable
        :param d: Distortion correction d variable
        """
        self.camera = cv2.VideoCapture(index)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.width = width
        self.height = height
        self.k = np.array(k)
        self.d = np.array(d)
        self.distance_calibration = distance_calibration
        self.mm_per_pixel = 1.0

    def correct_distortion(self, frame):
        """
        Corrects the frame using the distortion variables.
        :param frame: The frame to correct.
        :return: The corrected frame.
        """
        Log.info('Correcting camera distortion on frame.')
        m1, m2 = cv2.fisheye.initUndistortRectifyMap(self.k,
                                                     self.d,
                                                     np.eye(3),
                                                     self.k,
                                                     (self.width, self.height),
                                                     cv2.CV_16SC2)
        undistorted_img = cv2.remap(frame, m1, m2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        return undistorted_img

    def capture_frame(self, r=5, correct_distortion=True):
        """
        Captures a frame from the camera.
        :param correct_distortion: Tell the function if it should correct for distortion.
        :param r: Number of initial frames to read to allow for calibration.
        :return: np array of pixel data
        """
        Log.info(f"Capturing frame from camera with {r} initial "
                 f"frames and{'' if correct_distortion else ' no'} distortion correction.")
        for _ in range(r):
            self.camera.read()
        success, frame = self.camera.read()
        if not success:
            Log.error('Frame could not be read from camera.')
            raise CameraError()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if correct_distortion:
            frame = self.correct_distortion(frame)

        data = Image.fromarray(frame)
        data.save(f"frame-{Log.elapsed_time()}.jpg")

        return frame

    def take_snapshot(self):
        """
        Returns a map of all markers present in the current frame adjusted with the distance calibration.
        :return: [Marker...]
        """
        Log.info('Taking snapshot from camera.')
        frame = self.capture_frame(r=0)
        markers = Camera.extract_markers(frame)
        Log.info(f"Scaling snapshot markers for real world distances using scalar {self.mm_per_pixel}.")
        for key in markers:
            markers[key].scale(self.mm_per_pixel)
        frame_center = np.array([self.width / 2, self.height / 2])
        frame_center *= self.mm_per_pixel
        return markers, frame_center

    def calibrate_observed_distances(self):
        """
        Uses markers with know distance to calculate the real world distances being captured by the camera.
        """
        # Get all the markers
        start_fid, end_fid, fid_distance = self.distance_calibration
        Log.info(f"Calibrating camera using reference markers {start_fid} and {end_fid} at "
                 f"distance of {fid_distance} millimeters.")
        frame = self.capture_frame()
        markers = Camera.extract_markers(frame)
        if start_fid not in markers or end_fid not in markers:
            Log.warn('Calibration marker is not visible. Ensure it is in the frame of the camera.')
            raise CalibrationMarkerNotVisible()
        # Calculate the pixel distance between the two markers in the raw image
        observed_distance = np.linalg.norm(markers[end_fid].center - markers[start_fid].center)
        # Calculate the physical distance of a pixel
        self.mm_per_pixel = fid_distance / observed_distance

    @staticmethod
    def extract_markers(frame, marker_type=aruco.DICT_4X4_1000, save_img=False):
        """
        Extracts all of the markers in given frame and returns a map of fid to marker.
        :param save_img:
        :param frame:
        :param marker_type:
        :return:
        """
        Log.info('Extracting aruco markers from camera frame.')
        aruco_dict = aruco.Dictionary_get(marker_type)
        parameters = aruco.DetectorParameters_create()
        corners, ids, _ = aruco.detectMarkers(frame, aruco_dict, parameters=parameters)
        if save_img:
            marked_frame = aruco.drawDetectedMarkers(frame, corners, ids)
            output_frame = f"runtime/marked-frame-{int(time.time())}.png"
            Log.info(f"Saving marked frame to {output_frame}")
            data = Image.fromarray(marked_frame)
            data.save(output_frame)
        markers = {}
        for x in range(len(corners)):
            fid = str(ids[x][0])
            markers[fid] = Marker(
                    fid,
                    corners[x][0]
                )
        Log.info(f"Found {len(corners)} markers: {list(markers.keys())}")
        return markers
