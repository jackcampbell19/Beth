
class MockGPIO:
    """
    Mock GPIO class for testing on devices that do not support GPIO.
    """
    BCM = ""
    OUT = ""
    IN = ""
    PUD_UP = ""

    @staticmethod
    def output(x, y):
        pass

    @staticmethod
    def setmode(x):
        pass

    @staticmethod
    def setup(x, y, **kwargs):
        pass

    @staticmethod
    def input(x):
        pass

    @staticmethod
    def PWM(x, y):
        return MockPWM()


class MockPWM:

    def start(self, x):
        pass

    def ChangeDutyCycle(self, x):
        pass

    def stop(self):
        pass





