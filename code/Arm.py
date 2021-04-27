import random
import numpy as np
from RpiMotorLib import RpiMotorLib
import RPi.GPIO as GPIO


class Arm:

    def __init__(self, x_size, y_size, x_stp, y_stp, x_dir, y_dir):
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

    def cleanup(self):
        GPIO.cleanup()

    def calibrate(self):
        pass

    def position(self, v):
        x_steps = (self.current_position - v)[0]
        self.x_stepper.motor_go(clockwise=x_steps > 0, steps=abs(x_steps))
        y_steps = (self.current_position - v)[1]
        self.y_stepper.motor_go(clockwise=y_steps > 0, steps=abs(y_steps))

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

