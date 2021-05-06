from Log import log
from PIL import Image


def save_frame_to_runtime_dir(frame):
    """
    Saves a frame to the runtime dir.
    :param frame: THe frame to save.
    """
    data = Image.fromarray(frame)
    data.save(f"runtime/frame-{log.elapsed_time_raw()}.jpg")