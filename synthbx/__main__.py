from synthbx.core.synthesize import synthesize
from synthbx.env.const import EFolder
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--specification', required=True,
                    help='path to the folder containing schema folder and example folder'
                    )
parser.add_argument('-m', '--mode', choices=['synth', 'clean', 'verify'],
                    default='synth', )

args = parser.parse_args()

benchmark = args.specification
mode = args.mode

path = benchmark

if mode == 'synth':
    synthesize(path)
elif mode == 'clean':
    os.system(
        f'rm -rf {path}/{EFolder.SYNTH} {path}/{EFolder.RESULT} 2> /dev/null'
    )
else:
    raise NotImplementedError
    pass
