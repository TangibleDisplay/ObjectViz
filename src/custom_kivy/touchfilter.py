
'''
Filter Touches
==============

Don't even consider some touches
'''

__all__ = ('InputPostprocFilterTouches', )

from kivy.vector import Vector
from collections import deque
import time


class InputPostprocFilterTouches(object):
    '''
    '''

    def __init__(self, app):
        self.min_duration = app.config.getint('filter', 'min_duration') / 1000.
        self.max_speed = app.config.getint('filter', 'max_speed') / 100.
        self.queue = deque()
        self.timeouts = dict()
        self.blacklist = deque()

    def process(self, events):
        d = time.time()
        timeouts = self.timeouts
        q = self.queue
        bl = self.blacklist

        # release previously held events
        while q:
            event = q.pop()
            timeout = timeouts[event].pop()
            if timeout > d:
                q.append(event)
                timeouts[event].append(timeout)
                break
            events.append(event)
            timeouts.pop(event)

        for etype, touch in events[:]:
            if not touch.is_touch:
                continue
            # custom
            if etype == 'end':
                while (etype, touch) in self.queue:
                    q.remove((etype, touch))
                    timeouts[(etype, touch)].pop()
                events.remove((etype, touch))

            elif etype == 'update':
                if (etype, touch) in q:
                    if (
                        Vector(
                            touch.x - touch.ox,
                            touch.y - touch.oy
                        ).length() / (d - touch.time_start) > self.max_speed
                    ):
                        bl.append(touch)
                    events.remove((etype, touch))
                    q.appendleft((etype, touch))
                    _timeouts = timeouts.setdefaults((etype, touch), deque())
                    _timeouts.appendleft(d + self.min_duration)

            elif etype == 'begin':
                # new touch, put it in queue
                q.appendleft((etype, touch))
                _timeouts = timeouts.setdefault((etype, touch), deque())
                _timeouts.appendleft(d + self.min_duration)

                events.remove((etype, touch))

        return events
