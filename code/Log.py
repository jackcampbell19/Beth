import time


class Log:
    """
    Logging class for debugging and monitoring.
    """

    LOG_INFO = True
    INIT_TIME = time.time()

    def elapsed_time(self):
        return f"\033[37m({self.elapsed_time_raw()}ms)\033[0m"

    def elapsed_time_raw(self):
        return int((time.time() - self.INIT_TIME) * 1000)

    def info(self, message):
        if not self.LOG_INFO:
            return
        print(f"\033[32m[INFO]\033[0m {self.elapsed_time()} {message}")

    def warn(self, message):
        print(f"\033[33m[WARN] {self.elapsed_time()} {message}\033[0m")

    def error(self, message):
        print(f"\033[31m[ERROR] {self.elapsed_time()} {message}\033[0m")

    def debug(self, message):
        print(f"\033[35m[DEBUG]\033[0m {self.elapsed_time()} {message}")


# Global log available for use
log = Log()
