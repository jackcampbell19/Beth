import cv2
import numpy as np
from src.misc.Exceptions import *

from src.misc.Log import log


class Camera:
    """
    The {Camera} class is a wrapper for the {VideoCapture} camera from cv2. This
    class does additional computation when reading frames and initializing.
    """

    def __init__(self, camera_index, frame_size, k, d):
        """
        Initializes the {Camera} object.
        :param camera_index: The index of the camera to read from.
        :param frame_size: [width, height]
        :param k: Distortion correction k variable.
        :param d: Distortion correction d variable.
        """
        self.frame_size = tuple(frame_size)
        self.index = camera_index
        self.k = np.array(k)
        self.d = np.array(d)
        self.mock_frame_path = None
        self.latest_frame = None
        self.frame_center = np.array([self.frame_size[0] / 2, self.frame_size[1] / 2])

    def generate_camera(self):
        """
        Generates and returns a new camera instance.
        :return:
        """
        camera = cv2.VideoCapture(self.index)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_size[0])
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_size[1])
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 3)
        camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
        for _ in range(10):
            _, _ = camera.read()
        exposure = camera.get(cv2.CAP_PROP_EXPOSURE)
        print(exposure)
        camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        camera.set(cv2.CAP_PROP_EXPOSURE, exposure * 0.2)
        return camera

    def correct_distortion(self, frame):
        """
        Corrects distortion due to curved lenses using the distortion variables 'k' and 'd'.
        :param frame: The frame to correct.
        :return: The corrected frame.
        """
        log.info('Correcting camera distortion on frame.')
        new_k = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(self.k,
                                                                       self.d,
                                                                       self.
                                                                       frame_size,
                                                                       np.eye(3),
                                                                       balance=1)
        m1, m2 = cv2.fisheye.initUndistortRectifyMap(self.k,
                                                     self.d,
                                                     np.eye(3),
                                                     new_k,
                                                     self.frame_size,
                                                     cv2.CV_32FC1)
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
        log.info('Warming camera up.')
        camera = self.generate_camera()
        log.info(f"Capturing frame from camera with"
                 f"{'' if correct_distortion else ' no'} distortion correction.")
        print('a', camera.get(cv2.CAP_PROP_EXPOSURE))
        ret, frame = camera.read()
        if not ret:
            raise CameraError('Failed to read from from camera.')
        camera.release()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if correct_distortion:
            frame = self.correct_distortion(frame)
        self.latest_frame = frame
        return frame
