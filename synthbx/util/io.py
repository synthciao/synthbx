import os


def load_data(path, delimiter='\t'):
    with open(path, 'r') as fr:
        rows = [line.replace('\n', '').split(delimiter) for line in fr]
        return rows


def store_data(path, data, delimiter='\t'):
    with open(path, 'w') as fw:
        for row in data:
            fw.write(delimiter.join([str(i) for i in row]))
            fw.write('\n')
    return


def get_ext_files(path, ext):
    return [n for n in os.listdir(path)
            if n.endswith(ext)
            ]


RESET = '\033[0m'
YELLOW = '\033[1;33m'
RED = '\033[1;31m'
BLUE = '\033[1;34m'
CYAN = '\033[1;36m'


def yprint(msg):
    print(f'{YELLOW}{msg}{RESET}')


def cprint(msg):
    print(f'{CYAN}{msg}{RESET}')


def rprint(msg):
    print(f'{RED}{msg}{RESET}')


def bprint(msg):
    print(f'{BLUE}{msg}{RESET}')
