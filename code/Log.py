
class Log:

    @staticmethod
    def info(message):
        print(f"\032[31m[INFO]\033[0m {message}")

    @staticmethod
    def warn(message):
        print(f"\033[33m[WARN] {message}\033[0m")

    @staticmethod
    def error(message):
        print(f"\031[32m[ERROR] {message}\033[0m")
