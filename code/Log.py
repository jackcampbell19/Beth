import time

INIT_TIME = time.time()


class Log:

    @staticmethod
    def elapsed_time():
        return f"{int(time.time() - INIT_TIME)}"

    @staticmethod
    def info(message):
        print(f"\033[32m[INFO]({Log.elapsed_time()})\033[0m {message}")

    @staticmethod
    def warn(message):
        print(f"\033[33m[WARN]({Log.elapsed_time()}) {message}\033[0m")

    @staticmethod
    def error(message):
        print(f"\033[31m[ERROR]({Log.elapsed_time()}) {message}\033[0m")
