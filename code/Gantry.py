import random
import numpy as np
from CatFoot import Stepper

from Log import log


class Gantry:
    """
    The gantry system used for physical movement.
    """

    def __init__(self, size, stp_pins, dir_pins):
        """
        Initializes the gantry with the given hardware specifications.
        :param size: {(int, int)} (x_size, y_size)
        :param stp_pins: {(int, int, int)} (x_stp, y0_stp, y1_stp)
        :param dir_pins: {(int, int, int)} (x_dir, y0_dir, y1_dir)
        """
        self.x_size, self.y_size = size
        x_stp, y0_stp, y1_stp = stp_pins
        x_dir, y0_dir, y1_dir = dir_pins
        self.x_stepper = Stepper(stp_pin=x_stp, dir_pin=x_dir)
        self.y0_stepper = Stepper(stp_pin=y0_stp, dir_pin=y0_dir)
        self.y1_stepper = Stepper(stp_pin=y1_stp, dir_pin=y1_dir)

    def calibrate(self):
        """
        Calibrates the gantry and sets the current position to [0, 0].
        """
        pass

    def set_position(self, x, y, rel=False):
        """
        Sets the absolute position of the gantry to the given position.
        :param rel: Set position relatively instead of absolutely.
        :param x: {int} The x coordinate.
        :param y: {int} The y coordinate.
        """
        log.info(f"Setting position to ({x}, {y})")
        if rel:
            self.x_stepper.set_position_rel(int(x))
            self.y0_stepper.set_position_rel(int(y))
            self.y1_stepper.set_position_rel(int(y))
        else:
            self.x_stepper.set_position_abs(int(x))
            self.y0_stepper.set_position_abs(int(y))
            self.y1_stepper.set_position_abs(int(y))
        Stepper.move_concurrently(self.x_stepper, self.y0_stepper, self.y1_stepper)

    def move_to_random_position(self):
        """
        Moves to a random position within the gantry's movement space.
        """
        self.set_position(random.randint(0, self.x_size), random.randint(0, self.y_size))

