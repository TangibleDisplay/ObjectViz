# -*- coding: utf-8 -*-
'''
#exclude
'''
# fix qa errors for condiment
WITH_MOUSE = None               # noqa
WITH_SENTRY_URL = ''            # noqa
WITH_DEV = False                # noqa
                                # noqa
import condiment                # noqa
condiment.install()             # noqa
'''
#endexclude
'''

from sys import platform
from os import environ
from kivy.base import ExceptionManager, ExceptionHandler
from kivy.config import Config
from kivy.logger import Logger
from utils import get_screen_resolution


class LastStand(ExceptionHandler):
    def handle_exception(self, inst):
        from kivy.factory import Factory as F
        if 'space left on device' in str(inst):
            F.Logger.setLevel('critical')
            F.Message(
                text=(
                    'Your system seems to run low on disk space, please '
                    'clean up'
                ),
                display_time=10).show()

        if WITH_SENTRY_URL:
            from raven import Client
            c = Client('WITH_SENTRY_URL')
            c.captureException()
            return ExceptionManager.PASS
        pass


ExceptionManager.add_handler(LastStand())

screenx, screentop, screenwidth, screenheight = get_screen_resolution('primary')

environ.update({
    'KIVY_WINDOW': 'sdl2,pygame',
    'KIVY_TEXT': 'sdl2,pygame',
    'KIVY_IMAGE': 'sdl2,pygame',
    'SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS': '0',
})

Config.set('graphics', 'fullscreen', False)
Config.set('graphics', 'resizable', False)
Config.set('graphics', 'borderless', True)

Config.set('graphics', 'position', 'custom')
Config.set('graphics', 'left', screenx)
Config.set('graphics', 'top', screentop)
Config.set('graphics', 'width', screenwidth)
Config.set('graphics', 'height', screenheight)
Config.set('input', 'mouse', 'mouse, disable_multitouch')

if WITH_MOUSE:
    Config.set('input', 'mouse', 'mouse')

Config.set('input', 'tuio_', 'tuio,0.0.0.0:3333')

Config.set('input', 'wm_touch', 'wm_touch')
Config.set('kivy', 'keyboard_mode', 'systemandmulti')
