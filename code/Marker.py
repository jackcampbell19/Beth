
class Marker:
    """
    Represents a fiducial marker.
    """

    def __init__(self, fid, corners):
        self.id = str(fid)
        self.corners = corners
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
