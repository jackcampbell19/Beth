import numpy as np
import apriltag
import cv2
from src.misc.Log import log


class Marker:
    """
    Represents a fiducial marker.
    """

    FAMILY_tag16h5 = 'tag16h5'
    FAMILY_tag36h11 = 'tag36h11'

    def __init__(self, fid, corners):
        self.id = str(fid)
        self.corners = np.array(corners)
        p0 = (corners[0] + corners[1]) / 2
        p1 = (corners[2] + corners[3]) / 2
        self.center = (p0 + p1) / 2
        self.center = (int(self.center[0]), int(self.center[1]))

    def __repr__(self):
        return f"Marker(id: {self.id}, center: {self.center})"

    def adjust(self, x, y):
        self.center[0] += x
        self.center[1] += y
        for i in range(len(self.corners)):
            self.corners[i][0] += x
            self.corners[i][1] += y

    @staticmethod
    def get_fids_from_list(markers):
        return [marker.id for marker in markers]

    @staticmethod
    def extract_markers(frame, marker_family):
        """
        Takes in a RGB color frame and extracts all of the apriltag markers present. Returns a list of markers.
        :param frame: The frame to search.
        :param marker_family: The marker family to search for.
        :return: {[Marker]} List of markers
        """
        log.info('Extracting apriltag markers from camera frame.')
        markers = []
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        options = apriltag.DetectorOptions(families=marker_family)
        detector = apriltag.Detector(options)
        results = detector.detect(gray)
        for r in results:
            c0, c1, c2, c3 = r.corners
            c0 = np.array([
                int(c0[0]),
                int(c0[1])
            ])
            c1 = np.array([
                int(c1[0]),
                int(c1[1])
            ])
            c2 = np.array([
                int(c2[0]),
                int(c2[1])
            ])
            c3 = np.array([
                int(c3[0]),
                int(c3[1])
            ])
            fid = str(r.tag_id)
            markers.append(
                Marker(
                    fid,
                    [c0, c1, c2, c3]
                )
            )
        log.info(f"Found {len(markers)} markers: {Marker.get_fids_from_list(markers)}")
        return markers
