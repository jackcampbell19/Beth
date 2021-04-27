import random
import numpy as np
from RpiMotorLib import RpiMotorLib


class Arm:

    def __init__(self, stepr_per_mm, x_size, y_size, x_stp, y_stp, x_dir, y_dir):
        self.steps_per_mm = stepr_per_mm
        self.x_size = x_size
        self.y_size = y_size
        self.current_position = np.array([0, 0])
        self.x_stepper = RpiMotorLib.A4988Nema(
            direction_pin=x_dir,
            step_pin=x_stp,
            mode_pins=(21, 21, 21),
            motor_type="DRV8825"
        )
        self.y_stepper = RpiMotorLib.A4988Nema(
            direction_pin=y_dir,
            step_pin=y_stp,
            mode_pins=(21, 21, 21),
            motor_type="DRV8825"
        )

    def calibrate(self):
        pass

    def position(self, v):
        steps = v - self.current_position
        steps *= self.steps_per_mm
        self.x_stepper.motor_go(clockwise=True if steps[0] > 0 else False, steps=abs(steps[0]))
        self.y_stepper.motor_go(clockwise=True if steps[1] > 0 else False, steps=abs(steps[1]))
        self.current_position = v

    def move_along_vector(self, v):
        self.position(self.current_position + v)

    def move_to_random_position(self):
        """
        Moves to a random position within the arms movement space.
        """
        self.position(np.array(
            [
                random.randint(0, self.x_size),
                random.randint(0, self.y_size)
            ]
        ))

