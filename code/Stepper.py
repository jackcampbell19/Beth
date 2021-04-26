# Motor driver code. Allows the CNC driver to control the motors.

import RPi.GPIO as GPIO
from time import sleep

# Set board mode.
GPIO.setmode(GPIO.BOARD)


# Stepper class.
class Stepper:

    SHORTEST_DELAY = 0.002

    def __init__(self, stp, dir):
        self.stp = stp
        self.dir = dir
        for pin in [self.stp, self.dir]:
            GPIO.setup(pin, GPIO.OUT)

    # Rotates the motor one step forward or backwards.
    def step(self, forward):
        if forward:
            GPIO.output(self.dir, 0)
            GPIO.output(self.stp, 0)
            GPIO.output(self.stp, 1)
        else:
            GPIO.output(self.dir, 1)
            GPIO.output(self.stp, 0)
            GPIO.output(self.stp, 1)
        sleep(self.SHORTEST_DELAY)
