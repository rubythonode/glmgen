
__version__ = '3.0.0'

import os

def schedule_dir():
    return os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/schedules')