import random

from src.mechanical.CatFoot import Stepper, Servo, Electromagnet, Button
from src.misc.Log import log


class Gantry:
    """
    The gantry system used for physical movement.
    """

    def __init__(self, size, stp_pins, dir_pins, z_sig_pin, grip_sig_pin, x_stop_pin, y0_stop_pin, y1_stop_pin):
        """
        Initializes the gantry with the given hardware specifications.
        :param size: {(int, int)} (x_size, y_size)
        :param stp_pins: {(int, int, int)} (x_stp, y0_stp, y1_stp)
        :param dir_pins: {(int, int, int)} (x_dir, y0_dir, y1_dir)
        :param z_sig_pin: {int} Servo motor signal pin.
        """
        self.x_size, self.y_size = size
        x_stp, y0_stp, y1_stp = stp_pins
        x_dir, y0_dir, y1_dir = dir_pins
        self.x_stepper = Stepper(stp_pin=x_stp, dir_pin=x_dir)
        self.y0_stepper = Stepper(stp_pin=y0_stp, dir_pin=y0_dir)
        self.y1_stepper = Stepper(stp_pin=y1_stp, dir_pin=y1_dir)
        self.z_delay = 1.3
        self.z_servo = Servo(sig_pin=z_sig_pin, default_delay=self.z_delay)
        self.gripper = Electromagnet(sig_pin=grip_sig_pin)
        self.x_stop = Button(pin=x_stop_pin)
        self.y0_stop = Button(pin=y0_stop_pin)
        self.y1_stop = Button(pin=y1_stop_pin)
        self.z_position = 0

    def calibrate(self, test_size=False):
        """
        Calibrates the gantry and sets the current position to [0, 0]. Returns
        """
        base_distance = 150
        log.info('Starting calibration sequence.')
        self.x_stepper.set_position_rel(base_distance)
        Stepper.move(self.x_stepper, acceleration_function=Stepper.ACCELERATION_SIN)
        while not self.x_stop.is_pressed():
            self.x_stepper.set_position_rel(-3)
            Stepper.move(self.x_stepper, acceleration_function=Stepper.ACCELERATION_CONST,
                         min_delay=0.004, max_delay=0.004)
        log.info('X stop found.')
        x_pos = -self.x_stepper.get_current_position()
        self.x_stepper.reset()
        self.y0_stepper.set_position_rel(base_distance)
        self.y1_stepper.set_position_rel(base_distance)
        Stepper.move(self.y0_stepper, self.y1_stepper, acceleration_function=Stepper.ACCELERATION_SIN)
        while True:
            if self.y0_stop.is_pressed() and self.y1_stop.is_pressed():
                break
            if not self.y0_stop.is_pressed():
                self.y0_stepper.set_position_rel(-3)
            if not self.y1_stop.is_pressed():
                self.y1_stepper.set_position_rel(-3)
            Stepper.move(self.y0_stepper, self.y1_stepper, acceleration_function=Stepper.ACCELERATION_CONST,
                         min_delay=0.004, max_delay=0.004)
        log.info('Y stops found.')
        y0_pos = -self.y0_stepper.get_current_position()
        y1_pos = -self.y1_stepper.get_current_position()
        y_pos = int(round((y0_pos + y1_pos) / 2))
        self.y0_stepper.reset()
        self.y1_stepper.reset()
        if test_size:
            self.y0_stepper.set_position_abs(self.y_size)
            self.y1_stepper.set_position_abs(self.y_size)
            self.x_stepper.set_position_abs(self.x_size)
            Stepper.move(self.y0_stepper, self.y1_stepper, self.x_stepper)
            self.y0_stepper.set_position_abs(0)
            self.y1_stepper.set_position_abs(0)
            self.x_stepper.set_position_abs(0)
            Stepper.move(self.y0_stepper, self.y1_stepper, self.x_stepper)
        return x_pos, y_pos

    def set_position(self, x, y, rel=False, slow=False):
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
        if slow:
            Stepper.move(self.x_stepper, self.y0_stepper, self.y1_stepper, max_delay=0.0012, min_delay=0.0008)
        else:
            Stepper.move(self.x_stepper, self.y0_stepper, self.y1_stepper)

    def set_z_position(self, p):
        """
        Sets the Z position based on the input {p}. If p == 1 the z servo will
        be fully extended, if p == 0 the z servo will be fully retracted.
        """
        p = max(0, min(p, 1))
        log.info(f"Setting z to {int(p * 100)}% extension.")
        self.z_servo.set_angle(
            180 * (1 - p),
            delay=max(
                    self.z_delay,
                    self.z_delay * abs(self.z_position - p)
                 )
        )
        self.z_position = p

    def engage_grip(self):
        log.info('Engaging grip.')
        self.gripper.magnetize()

    def release_grip(self):
        log.info('Releasing grip.')
        self.gripper.demagnetize()

    def move_to_random_position(self):
        """
        Moves to a random position within the gantry's movement space.
        """
        self.set_position(random.randint(0, self.x_size), random.randint(0, self.y_size))

