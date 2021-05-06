import random
import numpy as np
from RpiMotorLib import RpiMotorLib

from Log import log


class Gantry:
    """
    The gantry system used for physical movement.
    """

    def __init__(self, size, x_pins, y_pins):
        """
        Initializes the gantry with the given hardware specifications.
        :param size: [width, height]
        :param x_pins: [[step, direction]...]
        :param y_pins: [[step, direction]...]
        """
        self.x_size = size[0]
        self.y_size = size[1]
        self.current_position = np.array([0, 0])
        self.x_stepper = RpiMotorLib.A4988Nema(
            step_pin=x_pins[0],
            direction_pin=x_pins[1],
            mode_pins=(21, 21, 21),
            motor_type="DRV8825"
        )
        self.y_stepper = RpiMotorLib.A4988Nema(
            step_pin=y_pins[0],
            direction_pin=y_pins[1],
            mode_pins=(21, 21, 21),
            motor_type="DRV8825"
        )
        self.step_delay = 0.001

    def calibrate(self):
        """
        Calibrates the gantry and sets the current position to [0, 0].
        """
        pass

    def set_position(self, v):
        """
        Sets the absolute position of the gantry to the given position.
        :param v: np.array([x, y])
        """
        log.info(f"Setting position to {v}")
        x_steps, y_steps = v - self.current_position
        self.x_stepper.motor_go(clockwise=True if x_steps > 0 else False, steps=abs(x_steps), stepdelay=self.step_delay)
        self.y_stepper.motor_go(clockwise=True if y_steps > 0 else False, steps=abs(y_steps), stepdelay=self.step_delay)
        self.current_position = v

    def move_along_vector(self, v):
        """
        Moves the gantry relatively along a vector from the current position.
        :param v: np.array([x, y])
        """
        self.set_position(self.current_position + v)

    def move_to_random_position(self):
        """
        Moves to a random position within the gantry's movement space.
        """
        self.set_position(np.array(
            [
                random.randint(0, self.x_size),
                random.randint(0, self.y_size)
            ]
        ))

