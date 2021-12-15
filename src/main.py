# -*- coding: utf-8 -*-
'''
#exclude
'''
WITH_SENTRY_URL = None
WITH_DEBUG = False
WITH_NAME = ''

import condiment
condiment.install()
'''
#endexclude
'''

NAME = 'ObjectViz'


if WITH_NAME:
    NAME = 'WITH_NAME'

if __name__ in ('__main__', 'main', '<run_path>'):
    try:
        from application import app
        app.run()
    except Exception as e:
        if WITH_DEBUG:
            import pudb; pudb.post_mortem()
        if WITH_SENTRY_URL:
            from raven import Client
            c = Client('WITH_SENTRY_URL')
            c.captureException()
        raise

from kivy.utils import platform
from kivy.app import App
import psutil
import sys
if sys.platform == 'win':
    import winxpgui
