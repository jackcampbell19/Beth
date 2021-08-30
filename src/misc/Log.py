import time


class Log:
    """
    Logging class for debugging and monitoring.
    """

    log_info = True
    init_time = time.time()
    save_output = False
    file = None

    def elapsed_time(self):
        return f"\033[37m({self.elapsed_time_raw()}ms)\033[0m"

    def elapsed_time_raw(self):
        """
        Elapsed time in milliseconds.
        """
        return int((time.time() - self.init_time) * 1000)

    def enable_save_output(self, path):
        self.save_output = True
        self.file = open(f"{path}/{Log.current_time_in_milliseconds()}.log", 'a+')

    def close_file(self):
        self.file.close()

    @staticmethod
    def current_time_in_milliseconds():
        return int(time.time() * 1000)

    def info(self, message):
        if not self.log_info:
            return
        self.write_line(f"\033[32m[INFO]\033[0m {self.elapsed_time()} {message}")

    def warn(self, message):
        self.write_line(f"\033[33m[WARN] {self.elapsed_time()} {message}\033[0m")

    def error(self, message):
        self.write_line(f"\033[31m[ERROR] {self.elapsed_time()} {message}\033[0m")

    def debug(self, message):
        self.write_line(f"\033[35m[DEBUG]\033[0m {self.elapsed_time()} {message}")

    def write_line(self, line):
        if self.save_output:
            stripped_line = line
            for x in [0, 31, 33, 32, 35, 37]:
                stripped_line = stripped_line.replace(f"\033[{x}m", '')
            self.file.write(stripped_line + '\n')
        print(line)


# Global log available for use
log = Log()
