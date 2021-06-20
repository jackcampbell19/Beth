
class MockGPIO:
    """
    Mock GPIO class for testing on devices that do not support GPIO.
    """
    BCM = ""
    OUT = ""

    @staticmethod
    def output(x, y):
        pass

    @staticmethod
    def setmode(x):
        pass

    @staticmethod
    def setup(x, y):
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





