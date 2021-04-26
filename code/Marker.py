from Log import Log
import numpy as np


class Marker:

    def __init__(self, fid, corners):
        self.id = str(fid)
        self.corners = corners
        p0 = (corners[0] + corners[1]) / 2
        p1 = (corners[2] + corners[3]) / 2
        self.center = (p0 + p1) / 2

    def scale(self, scalar):
        self.center *= scalar
        for x in range(len(self.corners)):
            self.corners[x] *= scalar

    def __repr__(self):
        return f"Marker(id: {self.id}, center: {self.center})"
