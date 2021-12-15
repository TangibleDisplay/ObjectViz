'''
Retain Touch
============

Reuse touch to counter lost finger behavior
'''

__all__ = ('InputPostprocRetainTouch', )

from kivy.vector import Vector
from kivy.core.window import Window
import time


class InputPostprocRetainTouch(object):
    '''
    InputPostprocRetainTouch is a post-processor to delay the 'up' event of a
    touch, to reuse it under certains conditions. This module is designed to
    prevent lost finger touches on some hardware/setups.

    Retain touch can be configured in the Kivy config file::

        [postproc]
            retain_time = 100
            retain_distance = 50

    The distance parameter is in the range 0-1000 and time is in milliseconds.
    '''

    def __init__(self, app):
        self._app = app
        self._available = []
        self._links = {}

    def process(self, events):
        # check if module is disabled
        c = self._app.config
        timeout = float(c.get('retain touch', 'retain_time')) / 1000.
        distance = float(c.get('retain touch', 'retain_distance'))

        if timeout == 0:
            return events

        d = time.time()
        for etype, touch in events[:]:
            if not touch.is_touch:
                continue
            # custom
            if etype == 'end':
                if hasattr(touch, 'ud'):
                    if 'retain_touch' not in touch.ud:
                        continue
                events.remove((etype, touch))
                if touch.uid in self._links:
                    selection = self._links[touch.uid]
                    selection.ud.__pp_retain_time__ = d
                    self._available.append(selection)
                    del self._links[touch.uid]
                else:
                    touch.ud.__pp_retain_time__ = d
                    self._available.append(touch)
            elif etype == 'update':
                if touch.uid in self._links:
                    selection = self._links[touch.uid]
                    selection.x = touch.x
                    selection.y = touch.y
                    selection.sx = touch.sx
                    selection.sy = touch.sy
                    events.remove((etype, touch))
                    events.append((etype, selection))
                else:
                    pass
            elif etype == 'begin':
                # new touch, found the nearest one
                selection = None
                selection_distance = float('inf')
                for touch2 in self._available:
                    touch.scale_for_screen(*Window.size)
                    touch_distance = Vector(touch2.pos).distance(touch.pos)
                    if touch_distance > distance:
                        continue
                    if touch_distance < selection_distance:
                        # eligible for continuation
                        selection_distance = touch_distance
                        selection = touch2
                if selection is None:
                    continue

                self._links[touch.uid] = selection
                touch.ud = selection.ud
                self._available.remove(selection)
                events.remove((etype, touch))

        for touch in self._available[:]:
            t = touch.ud.__pp_retain_time__
            if d - t > timeout:
                self._available.remove(touch)
                events.append(('end', touch))

        return events
