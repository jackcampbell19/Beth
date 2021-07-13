import sys
from src.misc.Log import log

if "--mock-gpio" in sys.argv:
    log.info("--mock-gpio enabled. All GPIO setup and output will be mocked.")
    from src.misc.MockGPIO import MockGPIO as gpio
else:
    import RPi.GPIO as gpio

import time
import math


gpio.setmode(gpio.BCM)


def p_out(pin, val):
    """
    Validates the pin is not None and then writes the value.
    :param pin: Pin to output to.
    :param val: Value to output.
    """
    if pin is not None:
        gpio.output(pin, val)


class Electromagnet:

    def __init__(self, sig_pin):
        self.sig_pin = sig_pin
        gpio.setup(sig_pin, gpio.OUT)
        self.demagnetize()

    def magnetize(self):
        gpio.output(self.sig_pin, True)

    def demagnetize(self):
        gpio.output(self.sig_pin, False)


class Servo:

    def __init__(self, sig_pin):
        gpio.setup(sig_pin, gpio.OUT)
        self.pin = sig_pin
        self.pwm = gpio.PWM(sig_pin, 50)
        self.pwm.start(0)

    def set_angle(self, deg):
        duty = deg / 18 + 2
        p_out(self.pin, True)
        self.pwm.ChangeDutyCycle(duty)
        time.sleep(1)

    def cleanup(self):
        self.pwm.stop()


class Stepper:
    # Resolution modes
    MODE_FULL = 0
    MODE_HALF = 1
    MODE_QUARTER = 2
    MODE_EIGHTH = 3
    MODE_SIXTEENTH = 4
    MODE_THIRTY_TWO = 5

    # Acceleration functions
    ACCELERATION_SIN = lambda x: -math.sin(x * math.pi) + 1
    ACCELERATION_QUAD = lambda x: (2 * x - 1) ** 4

    def __init__(self, stp_pin, dir_pin=None, en_pin=None, rst_pin=None,
                 slp_pin=None, m0_pin=None, m1_pin=None, m2_pin=None):
        """
        Initializes the driver using the given pins.
        :param stp_pin: {int} stp pin on board.
        :param dir_pin: {int} dir pin on board.
        :param en_pin: {int} enable pin on board.
        :param rst_pin: {int} reset pin on board.
        :param slp_pin: {int} sleep pin on board.
        :param m0_pin: {int} m0 pi on board.
        :param m1_pin: {int} m1 pi on board.
        :param m2_pin: {int} m2 pi on board.
        """
        # Setup driver pins
        self.stp = stp_pin
        self.dir = dir_pin
        self.en = en_pin
        self.rst = rst_pin
        self.slp = slp_pin
        self.m0 = m0_pin
        self.m1 = m1_pin
        self.m2 = m2_pin
        for pin in [self.stp, self.dir, self.en, self.rst, self.slp, self.m0, self.m1, self.m2]:
            if pin is not None:
                gpio.setup(pin, gpio.OUT)
        # Initialize properties
        self._current_position = 0
        self._target_position = None
        self._resolution_mode = Stepper.MODE_FULL
        # Set initial pin values
        p_out(self.dir, False)
        p_out(self.stp, False)
        p_out(self.en, False)
        p_out(self.rst, True)
        p_out(self.slp, True)
        p_out(self.m0, False)
        p_out(self.m1, False)
        p_out(self.m2, False)

    def set_resolution_mode(self, mode):
        """
        Sets the resolution mode of the stepper.
        :param mode: {int} Mode number
        """
        self._resolution_mode = mode
        mode_settings = [
            (False, False, False),
            (True, False, False),
            (False, True, False),
            (True, True, False),
            (False, False, True),
            (True, False, True),
            (False, True, True),
            (True, True, True)
        ]
        p_out(self.m0, mode_settings[mode][0])
        p_out(self.m1, mode_settings[mode][1])
        p_out(self.m2, mode_settings[mode][2])

    def get_current_position(self):
        """
        :return: {int} The current position.
        """
        return self._current_position

    def get_target_position(self):
        """
        :return: {int} The target position.
        """
        return self._target_position

    def get_required_steps_for_target(self):
        """
        :return: {int} Number of steps between the current and target positions
        """
        if self._target_position is None:
            return 0
        return abs(self._target_position - self._current_position)

    def get_required_direction_for_target(self):
        """
        :return: {bool} True if the stepper must rotate clockwise for the target
        """
        if self._target_position is None:
            return True
        return self._current_position < self._target_position

    def set_position_abs(self, position):
        """
        Sets the target position to the absolute position given.
        :param position: {int} The position to target.
        """
        self._target_position = position

    def set_position_rel(self, position):
        """
        Sets the target position as if the current position is 0.
        :param position: {int} The relative position.
        """
        if self._target_position is None:
            self._target_position = 0
        self._target_position += position

    def update_current_position_with_target(self):
        self._current_position = self._target_position
        self._target_position = None

    @staticmethod
    def move_concurrently(*steppers, rising_delay=0.00055, falling_delay=0.00055):
        """
        Move all steppers together one step at a time until each stepper reaches its target position.
        :param rising_delay: Delay after the rising edge of the step pin.
        :param falling_delay: Delay after the falling edge of the step pins.
        :param steppers: {list} Steppers to move.
        """
        targets = []
        total_step_count = 0
        for stepper in steppers:
            p_out(stepper.dir, stepper.get_required_direction_for_target())
            targets.append([stepper.stp, stepper.get_required_steps_for_target()])
            total_step_count += stepper.get_required_steps_for_target()
        n_targets = len(targets)
        while total_step_count > 0:
            for i in range(n_targets):
                if targets[i][1] > 0:
                    targets[i][1] -= 1
                    total_step_count -= 1
                    p_out(targets[i][0], True)
            time.sleep(rising_delay)
            for i in range(n_targets):
                p_out(targets[i][0], False)
            time.sleep(falling_delay)
        for stepper in steppers:
            stepper.update_current_position_with_target()

    @staticmethod
    def move(*steppers, min_delay=0.0004, max_delay=0.0015, acceleration_function=ACCELERATION_QUAD):
        """
        Move all steppers together one step at a time until each stepper reaches its target position.
        :param acceleration_function:
        :param max_delay:
        :param min_delay:
        :param steppers: {list(Stepper)} Steppers to move.
        """
        required_steps = [s.get_required_steps_for_target() for s in steppers]
        completed = [False if required_steps[i] > 0 else True for i in range(len(steppers))]
        max_steps = max(required_steps)
        stepper_step_frequency = list(map(lambda x: int(math.floor(max_steps / x)) if x > 0 else 0, required_steps))
        step_counts = [0 for _ in range(len(steppers))]
        for stepper in steppers:
            p_out(stepper.dir, stepper.get_required_direction_for_target())
        for c_step in range(max_steps):
            delay = min_delay + acceleration_function(c_step / max_steps) * (max_delay - min_delay)
            for i in range(len(steppers)):
                if completed[i] or c_step % stepper_step_frequency[i] != 0:
                    continue
                p_out(steppers[i].stp, True)
                step_counts[i] += 1
            time.sleep(delay)
            for i in range(len(steppers)):
                if completed[i] or c_step % stepper_step_frequency[i] != 0:
                    continue
                p_out(steppers[i].stp, False)
                if step_counts[i] == required_steps[i]:
                    completed[i] = True
                    steppers[i].update_current_position_with_target()
            time.sleep(delay)
