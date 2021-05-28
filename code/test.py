import Helpers as helpers
import cv2
import numpy as np
from Camera import Camera

frame = cv2.imread('test/frame-14618.jpg')
markers = Camera.extract_markers(frame)

helpers.draw_markers(frame, list(markers.values()))
Camera.adjust_markers(markers, (1920, 1080), {
    '9': [100, 100],
    '7': [125, 80],
    '6': [125, 70],
    '8': [100, 100],
    '5': [150, 70]
})
helpers.draw_markers(frame, list(markers.values()), point_only=True, primary_color=(0, 0, 255))

cv2.drawMarker(frame, (960, 540), (255, 0, 255), cv2.MARKER_CROSS, 30, 5)

cv2.imwrite('x.png', frame)

###
#
import random

gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
# edges = cv2.Canny(gray, 140, 250, apertureSize=3)
# cv2.imwrite('runtime/edges.jpg', edges)
# minLineLength = 100
# lines = cv2.HoughLinesP(image=edges, rho=1, theta=np.pi/180, threshold=100, lines=np.array([]),
#                         minLineLength=minLineLength, maxLineGap=80)
# a, b, c = lines.shape
# for i in range(a):
#     p0, p1 = (lines[i][0][0], lines[i][0][1]), (lines[i][0][2], lines[i][0][3])
#     # cv2.line(frame,
#     #          p0,
#     #          p1,
#     #          (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
#     #          3,
#     #          cv2.LINE_AA)
#     c = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
#     cv2.drawMarker(frame, p0, c,
#                    cv2.MARKER_TILTED_CROSS, 10, 3)
#     cv2.drawMarker(frame, p1, c,
#                    cv2.MARKER_TILTED_CROSS, 10, 3)
#     cv2.imwrite('runtime/hough-lines.jpg', frame)

###
import time

# Extract features
features = cv2.goodFeaturesToTrack(gray, 300, 0.01, 50)
# Translate features to list of points
points = [[int(f[0][0]), int(f[0][1])] for f in features]
# Draw points to image
for point in points:
    c = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    cv2.drawMarker(frame, tuple(point), c, markerSize=25, thickness=3)
cv2.imwrite('features.png', frame)
# Cluster points based on x coordinates such that each cluster fits within x threshold space
x_threshold = 40
point_clusters = [
    [points[0]]
]


def cluster_x_condition(cluster, p, threshold):
    cluster_xs = [x for (x, y) in cluster]
    cluster_xs.append(p[0])
    return max(cluster_xs) - min(cluster_xs) < threshold


for i in range(1, len(points)):
    found_cluster = False
    for j in range(len(point_clusters)):
        if cluster_x_condition(point_clusters[j], points[i], x_threshold):
            found_cluster = True
            point_clusters[j].append(points[i])
    if not found_cluster:
        point_clusters.append([points[i]])

for i in range(len(point_clusters)):
    x_vals = [x[0] for x in point_clusters[i]]
    x_avg = int(sum(x_vals) / len(x_vals))
    if len(x_vals) > 7:
        cv2.line(frame, (x_avg, 0), (x_avg, 1080), (0, 0, 255), 3)

cv2.imwrite('lines.png', frame)
