import time


class Log:
    """
    Logging class for debugging and monitoring.
    """

    LOG_INFO = True
    INIT_TIME = time.time()
    SAVE_OUTPUT = False

    def elapsed_time(self):
        return f"\033[37m({self.elapsed_time_raw()}ms)\033[0m"

    def elapsed_time_raw(self):
        return int((time.time() - self.INIT_TIME) * 1000)

    def info(self, message):
        if not self.LOG_INFO:
            return
        self.write_line(f"\033[32m[INFO]\033[0m {self.elapsed_time()} {message}")

    def warn(self, message):
        self.write_line(f"\033[33m[WARN] {self.elapsed_time()} {message}\033[0m")

    def error(self, message):
        self.write_line(f"\033[31m[ERROR] {self.elapsed_time()} {message}\033[0m")

    def debug(self, message):
        self.write_line(f"\033[35m[DEBUG]\033[0m {self.elapsed_time()} {message}")

    def write_line(self, line):
        if self.SAVE_OUTPUT:
            pass
        print(line)


# Global log available for use
log = Log()
