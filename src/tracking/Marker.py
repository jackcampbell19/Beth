import numpy as np
import cv2.aruco as aruco
from src.misc.Log import log


class Marker:
    """
    Represents a fiducial marker.
    """

    def __init__(self, fid, corners):
        self.id = str(fid)
        self.corners = np.array(corners)
        p0 = (corners[0] + corners[1]) / 2
        p1 = (corners[2] + corners[3]) / 2
        self.center = (p0 + p1) / 2

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
    def extract_markers(frame, marker_type=aruco.DICT_4X4_1000):
        """
        Extracts all of the markers in given frame and returns a map of fid to marker.
        :param frame: The frame to search.
        :param marker_type: The marker type to search for.
        :return: {[Marker]} List of markers
        """
        log.info('Extracting aruco markers from camera frame.')
        aruco_dict = aruco.Dictionary_get(marker_type)
        parameters = aruco.DetectorParameters_create()
        corners, ids, rejected = aruco.detectMarkers(frame, aruco_dict, parameters=parameters)
        print('rejected:', rejected)
        markers = []
        for x in range(len(corners)):
            fid = str(ids[x][0])
            markers.append(
                Marker(
                    fid,
                    corners[x][0]
                )
            )
        log.info(f"Found {len(corners)} markers: {Marker.get_fids_from_list(markers)}")
        return markers
