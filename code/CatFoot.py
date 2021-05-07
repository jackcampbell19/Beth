from RPi.GPIO import gpio
import time

class Stepper:

    QUADRATIC = lambda x: -(2 * x - 1) ** 2 + 1
    LINEAR_DECREASING = lambda x: -x + 1
    LINEAR_INCREASING = lambda x: x
    LINEAR = lambda x: 0

    def __init__(self, step, direction, enable=None, reset=None, sleep=None, mode=None):
        """
        Initializes the driver using the given pins.
        :param step: stp pin on board.
        :param direction: direction pin on board.
        :param enable: enable pin on board.
        :param reset: reset pin on board.
        :param sleep: sleep pin on board.
        :param mode: mode pin on board.
        """
        self.stp = step
        self.dir = direction
        self.en = enable
        self.rst = reset
        self.slp = sleep
        self.mode = mode
        gpio.setmode(gpio.BCM)
        for pin in [self.stp, self.dir, self.en, self.rst, self.slp, self.mode]:
            gpio.setup(pin, gpio.OUTPUT)
        self.current_position = 0
        self.default_delay = 0.0005
        self.sleep_when_not_moving = True
        self.target_position = None

    def set_default_delay(self, delay):
        self.default_delay = delay

    def set_sleep_when_not_moving(self, val):
        self.default_delay = val

    def set_position_abs(self, position):
        self.target_position = position

    def set_position_rel(self, position):
        self.target_position += position



class Controller:

    def move_async(self, *steppers):
        pass

    def move_concurrently(self, *steppers, delay=0.0005):
        step_max = 0
        for stepper in steppers:
            if stepper.sleep_when_not_moving and stepper.slp is not None:
                gpio.output(stepper.slp, True)
            step_max = max(step_max, abs(stepper.current_position - stepper.target_position))
            gpio.output(stepper.dir, stepper.current_position < stepper.target_position)
        for i in range(step_max):
            for stepper in steppers:
                if stepper.target_position is None:
                    continue
                active_delay = delay
                gpio.output(stepper.stp, True)
                time.sleep(active_delay)
                gpio.output(stepper.stp, False)
                time.sleep(active_delay)
                stepper.current_position += 1 if stepper.current_position < stepper.target_position else -1
                if stepper.current_position == stepper.target_position:
                    if stepper.sleep_when_not_moving and stepper.slp is not None:
                        gpio.output(stepper.slp, False)
                    stepper.target_position = None


stepper_a = Stepper(15, 14, sleep=18)

controller = Controller()

controller.move_async(stepper_a)