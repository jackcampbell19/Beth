import time

INIT_TIME = time.time()


class Log:

    LOG_INFO = True

    @staticmethod
    def elapsed_time():
        return f"\033[37m({int(time.time() - INIT_TIME)}s)\033[0m"

    @staticmethod
    def info(message):
        if not Log.LOG_INFO:
            return
        print(f"\033[32m[INFO]\033[0m {Log.elapsed_time()} {message}")

    @staticmethod
    def warn(message):
        print(f"\033[33m[WARN] {Log.elapsed_time()} {message}\033[0m")

    @staticmethod
    def error(message):
        print(f"\033[31m[ERROR] {Log.elapsed_time()} {message}\033[0m")

    @staticmethod
    def debug(message):
        print(f"\033[35m[DEBUG]\033[0m {Log.elapsed_time()} {message}")
