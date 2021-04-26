import random

class Arm:

    def __init__(self, x_size, y_size):
        self.x_size = x_size
        self.y_size = y_size
        self.current_position = (0, 0, 0)

    def calibrate(self):
        pass

    def move(self, x, y):
        pass

    def move_to_random_position(self):
        """
        Moves to a random position within the arms movement space.
        """
        self.move(random.randint(0, self.x_size), random.randint(0, self.y_size))

