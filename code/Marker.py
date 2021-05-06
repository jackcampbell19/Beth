
class Marker:
    """
    Represents a marker.
    """

    def __init__(self, fid, corners):
        self.id = str(fid)
        self.corners = corners
        p0 = (corners[0] + corners[1]) / 2
        p1 = (corners[2] + corners[3]) / 2
        self.center = (p0 + p1) / 2

    def __repr__(self):
        return f"Marker(id: {self.id}, center: {self.center})"
