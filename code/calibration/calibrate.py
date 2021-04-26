import cv2
import numpy as np
import glob


def calibrate(checkerboard_dimensions=(6, 9)):
    sub_pix_criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.1)
    calibration_flags = \
        cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC + cv2.fisheye.CALIB_CHECK_COND + cv2.fisheye.CALIB_FIX_SKEW
    obj_p = np.zeros((1, checkerboard_dimensions[0] * checkerboard_dimensions[1], 3), np.float32)
    obj_p[0, :, :2] = np.mgrid[0:checkerboard_dimensions[0], 0:checkerboard_dimensions[1]].T.reshape(-1, 2)
    img_shape = None
    obj_points = []  # 3d point in real world space
    img_points = []  # 2d points in image plane.
    images = glob.glob('images/*.png')
    for f_name in images:
        img = cv2.imread(f_name)
        if img_shape is None:
            img_shape = img.shape[:2]
        else:
            assert img_shape == img.shape[:2], "All images must share the same size."
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, checkerboard_dimensions,
                                                 cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK + cv2.CALIB_CB_NORMALIZE_IMAGE)
        # If found, add object points, image points (after refining them)
        if ret:
            obj_points.append(obj_p)
            cv2.cornerSubPix(gray, corners, (3, 3), (-1, -1), sub_pix_criteria)
            img_points.append(corners)
    n_ok = len(obj_points)
    k = np.zeros((3, 3))
    d = np.zeros((4, 1))
    r_vecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(n_ok)]
    t_vecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(n_ok)]
    rms, _, _, _, _ = \
        cv2.fisheye.calibrate(
            obj_points,
            img_points,
            gray.shape[::-1],
            k,
            d,
            r_vecs,
            t_vecs,
            calibration_flags,
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6)
        )
    print("Found " + str(n_ok) + " valid images for calibration")
    print("k=" + str(k.tolist()))
    print("d=" + str(d.tolist()))


if __name__ == '__main__':
    assert int(cv2.__version__[0]) >= 3, 'The fisheye module requires opencv version >= 3.0.0'
    calibrate()
