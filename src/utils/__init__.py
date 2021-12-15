from screeninfo.screeninfo import get_monitors

from inspect import currentframe
from os.path import exists
from ast import literal_eval
from subprocess import Popen

from kivy.compat import string_types
from kivy.lang import Builder
from kivy.logger import Logger

DATEFORMAT = '%Y-%m-%d_%H-%M-%S'


def configbool(value):
    """Function used to decode ConfigParser boolean values
    """
    if isinstance(value, string_types):
        return value.lower() not in ('false', 'no', '')
    return bool(value)


def configlist(value):
    if isinstance(value, string_types):
        return literal_eval(value)


def load_kv():
    filename = currentframe().f_back.f_code.co_filename
    if '_ft_' in filename:
        filename = filename.replace('_ft_', '')

    f = filename[:-2] + 'kv'
    if exists(f):
        return Builder.load_file(f)


def get_screen_resolution(mode):
    if mode == 'primary':
        screens = [get_monitors()[0]]
    elif mode == 'all':
        screens = get_monitors()
    else:
        Logger.warn(
            'invalid screen mode selected: {}, defaulting to primary'
            .format(mode)
        )
        screens = [get_monitors()[0]]

    x = min(m.x for m in screens)
    y = min(m.y for m in screens)
    width = max(m.x + m.width for m in screens) - x
    height = max(m.y + m.height for m in screens) - y
    return x, y, width, height
