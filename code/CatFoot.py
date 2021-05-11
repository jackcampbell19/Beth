import RPi.GPIO as gpio
import time
from typing import Optional, Final


class Acceleration:

    @staticmethod
    def quadratic(x: float) -> float:
        return (x - 1) ** 2

    @staticmethod
    def linear(x: float) -> float:
        return 0.0

    @staticmethod
    def linear_decreasing(x: float) -> float:
        return -x + 1


def p_out(pin: Optional[int], val: bool):
    """
    Validates the pin is not None and then writes the value.
    :param pin: Pin to output to.
    :param val: Value to output.
    """
    if pin is not None:
        gpio.output(pin, val)


class Stepper:

    MODE_FULL: int = 0
    MODE_HALF: int = 1
    MODE_QUARTER: int = 2
    MODE_EIGHTH: int = 3
    MODE_SIXTEENTH: int = 4
    MODE_THIRTY_TWO: int = 5

    def __init__(self, step: int,
                 direction: Optional[int],
                 enable: Optional[int] = None,
                 reset: Optional[int] = None,
                 sleep: Optional[int] = None,
                 mode: Optional[(Optional[int], Optional[int], Optional[int])] = None):
        """
        Initializes the driver using the given pins.
        :param step: stp pin on board.
        :param direction: dir pin on board.
        :param enable: enable pin on board.
        :param reset: reset pin on board.
        :param sleep: sleep pin on board.
        :param mode: mode pins on board.
        """
        # Setup driver pins
        self.stp: Final[int] = step
        self.dir: Final[Optional[int]] = direction
        self.en: Final[Optional[int]] = enable
        self.rst: Final[Optional[int]] = reset
        self.slp: Final[Optional[int]] = sleep
        self.m0: Final[Optional[int]] = mode[0] if mode else None
        self.m1: Final[Optional[int]] = mode[1] if mode else None
        self.m2: Final[Optional[int]] = mode[2] if mode else None
        gpio.setmode(gpio.BCM)
        for pin in [self.stp, self.dir, self.en, self.rst, self.slp, self.m0, self.m1, self.m2]:
            if pin is not None:
                gpio.setup(pin, gpio.OUTPUT)
        # Initialize properties
        self._current_position: int = 0
        self.min_delay: float = 0.0005
        self.delay_range: float = self.min_delay * 2
        self.__sleep_while_idle: bool = False
        self.acceleration_curve = Acceleration.quadratic
        self.acceleration_step_range: float = 0.5
        self._target_position: Optional[int] = None
        self.__resolution_mode = Stepper.MODE_FULL
        # Set initial pin values
        p_out(self.dir, False)
        p_out(self.stp, False)
        p_out(self.en, False)
        p_out(self.rst, True)
        p_out(self.slp, True)
        p_out(self.m0, False)
        p_out(self.m1, False)
        p_out(self.m2, False)

    @property
    def sleep_while_idle(self):
        return self.__sleep_while_idle

    @sleep_while_idle.setter
    def sleep_while_idle(self, b: bool):
        p_out(self.stp, b)
        self.__sleep_while_idle = b

    @property
    def resolution_mode(self):
        return self.__resolution_mode

    @resolution_mode.setter
    def resolution_mode(self, mode: int):
        self.__resolution_mode = mode
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

    def get_current_position(self) -> int:
        """
        Returns the current position.
        :return: {int} current position
        """
        return self._current_position

    def get_target_position(self) -> Optional[int]:
        """
        Returns the current position.
        :return: {int} current position
        """
        return self._target_position

    def get_required_steps_for_target(self) -> int:
        """
        Returns the number of steps between the current and target positions
        :return:
        """
        return abs(self._target_position - self._current_position)

    def get_required_direction_for_target(self) -> bool:
        """
        Returns True if the stepper must rotate clockwise for the target
        :return:
        """
        return self._current_position < self._target_position

    def set_position_abs(self, position):
        """
        Sets the target position to the absolute position given.
        :param position: The position to target.
        """
        self._target_position = position

    def set_position_rel(self, position):
        """
        Sets the target position as if the current position is 0.
        :param position: The relative position.
        """
        self._target_position += position

    def update_position(self, current: int, target: Optional[int]):
        self._current_position = current
        self._target_position = target


class Controller:

    @staticmethod
    def move_async(*steppers: Stepper):
        pass

    @staticmethod
    def move_concurrently(*steppers: Stepper):
        """
        Moves all of the steppers at the same time at the same speed.
        :param steppers:
        :return:
        """
        step_max: int = 0
        for stepper in steppers:
            # If the 'sleep_while_idle' function is enabled, wake the steppers
            if stepper.sleep_while_idle:
                p_out(stepper.slp, True)
            # Determine the maximum step count and set the direction pins for each stepper
            step_max = max(step_max, stepper.get_required_steps_for_target())
            p_out(stepper.dir, stepper.get_required_direction_for_target())
        # Execute the steps for each stepper
        for i in range(step_max):
            for stepper in steppers:
                # Skip if the target position has already been reached
                if stepper.get_target_position() is None:
                    continue
                # Calculate the active delay for the given step
                active_delay: float = stepper.min_delay
                acceleration_steps: int = int(stepper.acceleration_step_range)
                if 0 < stepper.acceleration_step_range < 1:
                    acceleration_steps = int(stepper.get_required_steps_for_target() * stepper.acceleration_step_range)
                secondary_range_start: int = stepper.get_required_steps_for_target() - acceleration_steps
                distribution_selection: float = 0
                if i < acceleration_steps:
                    distribution_selection = float(i) / float(acceleration_steps)
                elif i > secondary_range_start:
                    distribution_selection = 1.0 - \
                                             ((float(i) - float(secondary_range_start)) / float(acceleration_steps))
                active_delay += stepper.acceleration_curve(distribution_selection) * stepper.delay_range
                # Pulse the gpio pins
                p_out(stepper.stp, True)
                time.sleep(active_delay)
                p_out(stepper.stp, False)
                time.sleep(active_delay)
                # Check to see if the stepper has reached its target position
                if stepper.get_current_position() + \
                        (i + 1) * (1 if stepper.get_required_direction_for_target() else -1) == \
                        stepper.get_target_position():
                    # If the 'sleep_while_idle' function is enabled, put the stepper to sleep
                    if stepper.sleep_while_idle:
                        p_out(stepper.slp, False)
                    # Update the position of the stepper
                    stepper.update_position(current=stepper.get_target_position(), target=None)


stepper_a = Stepper(15, 14, sleep=18)
stepper_a.min_delay = 0.0005
stepper_a.delay_range = 0.001

Controller.move_async(stepper_a)
