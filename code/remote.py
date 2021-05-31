import os

if __name__ == '__main__':

    dir_path = os.path.dirname(os.path.realpath(__file__))
    remote_path = '/projects/chess-bot/code'

    print(dir_path)

    remote_commands = [
        f"cd {remote_path}",
        'rm -rf runtime',
        'mkdir runtime',
        'python3 main.py'
    ]

    commands = [
        f"scp -r {dir_path} pi@192.168.1.75:{remote_path}",
        f"ssh pi@192.168.1.75 '{' && '.join(remote_commands)}'",
        'rm -rf runtime',
        'mkdir runtime',
        f"scp -r pi@192.168.1.75:{remote_path}/runtime {dir_path}/runtime",
    ]

    print(' && '.join(commands))
