# -*- coding: utf-8 -*-

from os import getenv
import config_patch  # noqa

from utils import DATEFORMAT, load_kv, get_screen_resolution
from os import makedirs

from lang import tr

import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.properties import (
    AliasProperty,
    BooleanProperty,
    BoundedNumericProperty,
    ConfigParserProperty,
    DictProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    OptionProperty,
    StringProperty,
)
from kivy.logger import Logger, FileHandler
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.bubble import Bubble
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.factory import Factory
from kivy.vector import Vector
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.utils import platform
from kivy.compat import string_types
from kivy.uix.vkeyboard import VKeyboard
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout

from kivy.base import stopTouchApp
from kivy.resources import resource_find, resource_add_path

from shutil import copy
from psutil import disk_usage
from math import pi, radians, sin, cos, log10
import json
import socket
import random
from time import time, strftime
from os.path import dirname, join, exists
from collections import deque
from subprocess import Popen

from kivy.input.postproc import kivy_postproc_modules
from custom_kivy.retaintouch import InputPostprocRetainTouch
from custom_kivy.touchfilter import InputPostprocFilterTouches

from layouts import LetterboxView

from utils.math import angle_diff, get_angle, standard_deviation as std_dev
from functools import partial

from oscpy.parser import format_bundle
from oscpy.client import SOCK


if platform == 'win':
    import win32gui
    import win32con
    import winxpgui
    import win32api
    # solves a weird import bug on windows
    from kivy.input.providers import wm_touch  # noqa
    from custom_kivy.clipboard_winctypes import ClipboardWindows
    from kivy.core import clipboard
    clipboard.Clipboard = ClipboardWindows()

NAME = getenv('WITH_NAME', 'ObjectViz')

kivy.require('2.0.0')
INF = float('inf')
NAN = float('nan')

HWND = None

resource_add_path('src')

with open('version.txt') as f:
    __version__ = f.readline().strip()


def dist(p1, p2):
    """Classical Pythagora for distance
    """
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** .5


def nice_num(n):
    return round(n, - (int(log10(n)) - 1))


def configbool(value):
    """Function used to decode ConfigParser boolean values
    """
    if isinstance(value, string_types):
        return value.lower() not in ('false', 'no', '')
    return bool(value)


def get_tid(touch):
    """Utility function to fix mouse event casting as ints
    """
    if (
            isinstance(touch.uid, string_types) and
            touch.id.startswith('mouse')
    ):
        return touch.uid[5:]
    else:
        return touch.uid


def xuniqueCombinations(keys, items, maxd, n):
    """Get all combinations of n items within a list of items, but filtering
       on a max distance between two items in a combination
    """
    if n == 0:
        yield tuple()
    else:
        for i, k in enumerate(keys):
            for cc in xuniqueCombinations(
                [
                    x for x in keys[i + 1:]
                    if dist(items[x].pos, items[k].pos) < maxd
                ], items, maxd, n - 1
            ):
                yield (k, ) + cc


class TouchFilter(object):
    """Mixin to use on any Widget that wants to filter input events
       based on provider
    """
    accepted_touches = []

    @classmethod
    def remove_touch(cls, touch):
        try:
            cls.accepted_touches.remove(touch)
        except ValueError:
            pass

    def touch_types_filter(decorated):
        """Function decorator, meant to be used with on_touch_* operations,
           when you want to filter on certain providers
        """
        def func(*args):
            touches = TouchFilter.accepted_touches
            touch = args[1]

            Logger.trace("{}: Testing touch {} for duplicate".format(
                         time(), touch))

            md = app.touch_filter_min_distance
            mt = app.touch_filter_min_time
            if touch not in touches:
                for t in touches:
                    # another touch at the exact same pos, stop dispatching
                    if 'smart_ignore' in t.ud:
                        continue

                    if 'smart_ignore' in touch.ud or (
                        t is not touch and ((
                            abs(t.x - touch.x) < md and
                            abs(t.y - touch.y) < md
                        ) or (
                            abs(t.ox - touch.ox) < md and
                            abs(t.oy - touch.oy) < md and
                            abs(t.time_start - touch.time_start) < mt
                        ))
                    ):
                        Logger.trace("Found dupplicate {} ignoring".format(t))
                        touch.ud['smart_ignore'] = True
                        return True
                else:
                    touches.append(touch)

            return decorated(*args)
        return func

    @touch_types_filter
    def on_touch_down(self, touch):
        return super(TouchFilter, self).on_touch_down(touch)

    @touch_types_filter
    def on_touch_move(self, touch):
        return super(TouchFilter, self).on_touch_move(touch)

    @touch_types_filter
    def on_touch_up(self, touch):
        Clock.schedule_once(
            lambda x: TouchFilter.remove_touch(touch),
            app.double_touch_delay)
        return super(TouchFilter, self).on_touch_up(touch)


Factory.register('TouchFilter', cls=TouchFilter)


class OVPopup(TouchFilter, Popup):
    def on_border(self, *args):
        self.ids.container.padding = [
            self.border[2], self.border[1], self.border[0], self.border[3]
        ]


class ExitDialog(OVPopup):
    pass


class OVKeyboard(TouchFilter, VKeyboard):
    pass


class RootWidget(TouchFilter, LetterboxView):
    pass


class OVTextInput(TextInput):
    def _bind_keyboard(self):
        super(OVTextInput, self)._bind_keyboard()
        if self._keyboard:
            widget = self.keyboard.widget
            widget.do_scale = False
            widget.do_rotation = False
            Animation(top=Window.height / 3, d=0.8, t='out_elastic',
                      scale=1.5).start(widget)


class AppLabel(Label):
    index = NumericProperty(0)
    vwidth = NumericProperty(100)

    def collide_point(self, x, y):
        return (
            self.right - self.vwidth < x < self.right and
            self.y < y < self.top
        )


class CalibButton(ToggleButtonBehavior, Label):
    ballpos = ListProperty([0, 0])
    num = NumericProperty(0)
    bubble = ObjectProperty(None, allownone=True)
    zone = ObjectProperty(None)

    def toggle_menu(self, *args):
        if self.bubble:
            self.remove_widget(self.bubble)
            self.bubble = None
            Clock.unschedule(self.toggle_menu)
        else:
            self.bubble = bubble = CalibButtonBubble(button=self)
            self.add_widget(bubble)
            Clock.schedule_once(self.toggle_menu, 3)

    def _do_press(self):
        if self.state == 'down':
            self.toggle_menu()
        else:
            if self.zone.calib(str(self.num)):
                self.state = 'down'


class CalibLayout(FloatLayout):
    nb = NumericProperty(0)

    def on_nb(self, *args):
        Clock.schedule_once(self._populate, 0)

    def _populate(self, *args):
        self.ids.container.clear_widgets()
        for i in range(1, self.nb + 1):
            self.ids.container.add_widget(
                CalibButton(num=i, zone=app.root.ids.zone))


class TimeoutAction(Widget):
    """Simple way to trigger an action on a long touch
    """
    timeout = NumericProperty(1)
    progress = NumericProperty(0)
    action = ObjectProperty(None)

    def start(self, touch):
        touch.grab(self)
        self.touch = touch
        self.center = touch.pos
        self.anim = Animation(progress=1, d=self.timeout)
        self.anim.start(self)

    def on_progress(self, *args):
        self.center = self.touch.pos
        if self.progress == 1:
            self.parent.remove_widget(self)
            self.action(self.touch)

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super(TimeoutAction, self).on_touch_up(touch)

        self.anim.cancel(self)
        if self.parent:
            self.parent.remove_widget(self)


class TangibleObject(Widget):
    """A detected object, manages its own state, position, rotation, etc
    """
    oid = StringProperty('')
    tid = StringProperty('')
    angle = NumericProperty(0)
    angle_offset = NumericProperty(0)
    da = NumericProperty(0)
    dr = NumericProperty(0)
    m = ListProperty([0, 0])
    touches_ids = ListProperty([])
    ud = DictProperty({})
    age = NumericProperty(0)
    colors = ListProperty([])
    circles = ListProperty([])
    dx = NumericProperty(0)
    dy = NumericProperty(0)
    surface = NumericProperty(0)
    display_angle = ListProperty([])
    data_surface = ListProperty([])
    data_display_angle = ListProperty([])
    partially_calibrated = ObjectProperty(True)
    angle_ref_touch = ObjectProperty(None)
    missing_map = ListProperty([])
    birthdate = NumericProperty(0)

    def on_surface(self, *args):
        """When surface is updated, keep track of the value in recent data"""
        self.data_surface.append(self.surface)
        nb = app.config.getint('detection', 'nb_value_average')
        while len(self.data_surface) > nb:
            self.data_surface.pop(0)
        if self.partially_calibrated:
            self.complete_calibration()

    def on_display_angle(self, *args):
        nb = app.config.getint('detection', 'nb_value_average')
        self.data_display_angle.append(self.display_angle)
        while len(self.data_display_angle) > nb:
            self.data_display_angle.pop(0)
        if self.partially_calibrated:
            self.complete_calibration()

    def on_center(self, *args):
        zone = app.root.ids.zone
        if app.undetect_outside_zones and not zone.in_zones(self.center):
            zone.undetect(self)

    def complete_calibration(self):
        nb = app.config.getint('detection', 'nb_value_average')
        if (
            len(self.data_display_angle) >= nb and
            len(self.data_surface) >= nb
        ):
            l = len(self.data_display_angle)
            surface_mean = sum(self.data_surface) / nb
            angle1_mean = sum(x[0] for x in self.data_display_angle) / l
            angle2_mean = sum(x[1] for x in self.data_display_angle) / l
            app.root.ids.zone.set_coordinates(
                self.oid,
                len(self.touches_ids),
                surface_mean,
                1,  # aspect ratio, we don't care yet
                {
                    0: angle1_mean,
                    1: angle2_mean,
                })

            standard_deviation_surface = std_dev(self.data_surface)
            standard_deviation_angles = (
                std_dev(list(x[0] for x in self.data_display_angle)),
                std_dev(list(x[1] for x in self.data_display_angle)))

            sigma = app.tolerance_sigma_warning
            for k, d, maxval in (
                ('surface_tolerance', standard_deviation_surface, 750),
                ('angle_tolerance', max(standard_deviation_angles), 5),
            ):
                if getattr(app, k) < sigma * d:
                    v = nice_num(sigma * d)
                    # _k = k.replace('_', ' ')
                    _k = {
                        'surface_tolerance': tr._('surface'),
                        'angle_tolerance': tr._('angle'),
                    }[k]

                    def confirm(k, _k, v, *args):
                        Message(text=tr._('{} updated to {}').format(_k, v)).show()
                        app.setter(k)(app, v),  # 'or' for chaining

                    def retry(data_name, *args):
                        self.data_surface = []
                        self.data_display_angle = []
                        self.partially_calibrated = True

                    choices = {
                        '1:{}'.format(tr._('retry')): retry,
                        '2:{}'.format(tr._('do nothing')): None
                    }

                    if v < maxval:
                        choices[('2:{}'.format(tr._('increase')))] = partial(confirm, k, _k, v)

                    text = (
                        tr._("""Mesures were often over current {} limit, you can retry
                             calibration more slowly{} or do nothing.""")
                    ).format(
                        tr._(_k),
                        tr._(', increase {} to {} (but risk more misdetections)')
                        .format(tr._(_k), v) if v < maxval else ''
                    )

                    Question(
                        text=text,
                        choices=choices,
                    ).show()

            self.partially_calibrated = False

            oid = self.oid
            coordinates = app.root.ids.zone.coordinates[oid]


class TangibleObjectDataGraph(BoxLayout):
    """Widget to represent statistics about a detected object, surface
       and angle evolution and current values, mainly
    """
    target = ObjectProperty(None)


class CalibButtonBubble(Bubble):
    button = ObjectProperty(None)


class ScoreDisplay(GridLayout):
    """Widget displaying the relationship between a set of points, and
       the associated matching scores against models
    """
    touches = ListProperty()
    zone = ObjectProperty()
    scores = DictProperty()
    texture_size = ListProperty([0, 0])
    _top = NumericProperty()
    _x = NumericProperty()
    points = ListProperty([])
    surface = NumericProperty()
    angle_min = NumericProperty()
    angle_max = NumericProperty()
    visible = BooleanProperty()

    def update_label(self, index, text):
        if len(self.children) > index:
            self.children[-index - 1].text = text
        else:
            self.add_widget(Factory.GridLabel(text=text))

    def on_visible(self, *args):
        Animation.stop_all(self, 'opacity')
        Animation(opacity=1 if self.visible else 0, d=.3).start(self)

    def update(self, *args):
        try:
            touches = [self.zone.touches[t] for t in self.touches]
            self.visible = True
        except KeyError:
            self.visible = False
            return

        scores = self.scores
        i = 0
        for l in ('Id', 'Score', 'Surface', 'Angle min', 'Angle max'):
            self.update_label(i, l)
            i += 1

        for text in (
            '', '',
            int(self.surface),
            round(self.angle_min, 1),
            round(self.angle_max, 1),
        ):
            self.update_label(i, str(text))
            i += 1

        for s in sorted(scores, key=lambda x: scores[x])[:5]:
            self.update_label(i, s)
            i += 1
            for x in scores[s]:
                self.update_label(i, text=str(round(x, 1)))
                i += 1

        for w in self.children[i + 1:]:
            self.remove_widget(w)

        self._top = top = min(x.y for x in touches) - 50
        mi = min(x.x for x in touches)
        ma = max(x.x for x in touches)
        w = ma - mi
        self._x = x = mi + w / 2
        dists = sorted(touches, key=lambda t: dist(t.pos, (x, top)))
        a, b = dists[:2]
        # XXX if we want more than 3 points in objects, a shortest path
        # finder will be needed from a to be through all the other
        # points
        c = dists[-1]
        self.points = [x, top, a.x, a.y, c.x, c.y, b.x, b.y]


class DetectionZone(FloatLayout):
    """Most of the software's logic is here, (FIXME), keeping track of
       existing touches, objects, etc
    """
    scale = NumericProperty(0)
    touches = DictProperty({})
    coordinates = DictProperty({})
    min_object_slots_nb = NumericProperty(3)
    max_object_slots_nb = NumericProperty(3)  # max
    objects = DictProperty({})  # current objects on table
    zones = ListProperty([])
    graphs = DictProperty({})
    graphzone = ObjectProperty(None)
    pointer_angle = NumericProperty(0)
    pointer_anim = ObjectProperty(None)
    touches_points = DictProperty()
    candidates_widgets = DictProperty()
    lost_objects = ListProperty()
    __uniq_id = 0

    @classmethod
    def get_free_tid(cls):
        cls.__uniq_id += 1
        return str(cls.__uniq_id)

    def _get_state(self):
        if (
            self.min_object_slots_nb <=
            len(self.free_touches) <=
            self.max_object_slots_nb
        ):
            return 'set'

        elif len(self.free_touches) > self.max_object_slots_nb:
            return 'error'

        elif self.objects:
            return 'done'

        return 'ready'

    state = AliasProperty(_get_state, None, bind=('free_touches',))

    def _get_free_touches(self, *args):
        self.update_objects_touches()  # XXX shouldn't be needed!
        return [t for t in self.touches if t not in self.objects_touches]

    free_touches = AliasProperty(_get_free_touches, None,
                                 bind=('touches', 'objects'))

    def __init__(self, **kwargs):
        super(DetectionZone, self).__init__(**kwargs)
        self.messages_touches = deque()
        self.messages_objects = deque()

        Clock.schedule_once(self.find_object, app.object_detection_interval)
        Clock.schedule_interval(self.collect_objects, .1)

        self.objects_touches = set()

        # TUIO send 'alive' on a regular basis
        self.tuio_counter = 0
        self.activate_alive()
        app.bind(send_tuio_obj=self.activate_alive,
                 send_tuio_touch=self.activate_alive)

    def activate_alive(self, *args):
        Clock.unschedule(self.flush_tuio)
        if app.send_tuio_obj or app.send_tuio_touch:
            Clock.schedule_interval(self.flush_tuio, app.tuio_flush_interval)

    def on_state(self, *args):
        if self.pointer_anim:
            self.pointer_anim.stop(self)

        if self.state == 'set':
            self.pointer_anim = Animation(pointer_angle=160, t='out_bounce')

        elif self.state == 'done':
            self.pointer_anim = Animation(pointer_angle=0, t='out_bounce')

        elif self.state == 'error':
            self.pointer_anim = Animation(pointer_angle=220, t='out_bounce')

        else:
            return

        self.pointer_anim.start(self)

    def undetect(self, *args):
        for c, i in list(self.objects.items()):
            if not args or i in args:
                self.remove_widget(i)
                del(self.objects[c])

    def compare_with_coords(
        self, item, c_nb, c_surface, angles, c_angle_min, c_angle_max
    ):
        # nb = item['nb']
        surface = item['surface']
        angle_min = item['angle_min']
        angle_max = item['angle_max']
        #  nb
        # if nb != c_nb:
        #     return INF, NAN, NAN, NAN
        # surface
        d = abs(surface - c_surface)
        # angles
        dmin = abs(angle_min - angles[c_angle_min])
        dmax = abs(angle_max - angles[c_angle_max])
        if app.show_visual_log:
            app.visual_log('surface: %s: %s = %s' % (surface, c_surface, d))
            app.visual_log(
                'dmin: %s - %s = %s' % (angle_min, angles[c_angle_min], dmin))
            app.visual_log(
                'dmax: %s - %s = %s' % (angle_max, angles[c_angle_max], dmax))

        if d > app.surface_tolerance or max(dmin, dmax) > app.angle_tolerance:
            score = INF
        else:
            score = ((d + 1) * (dmin + 1) * (dmax + 1))
        return score, d, dmin, dmax

    def compare_with_calib(self, coordinates, current, candidate):
        best = None
        if app.training_current:
            target_score = (INF, app.training_current, INF, INF, INF)
        else:
            target_score = ()
        if not current:
            return
        c_nb, c_surface, c_ratio, angles = current
        c_angle_min = min(angles, key=lambda x: angles[x])
        c_angle_max = max(angles, key=lambda x: angles[x])

        # compare current values with calibration coordinates
        if app.display_scores:
            c = self.candidates_widgets.get(candidate)
            if not c:
                c = ScoreDisplay(
                    touches=candidate,
                    zone=self,
                    surface=c_surface,
                    angle_min=c_angle_min,
                    angle_max=c_angle_max)
                self.candidates_widgets[candidate] = c
                self.add_widget(c)
                Clock.schedule_once(c.update)
        else:
            c = None

        compare_with_coords = self.compare_with_coords
        for i, item in coordinates.items():
            if not item:
                if c:
                    c.scores[i] = INF, NAN, NAN, NAN
                continue

            s, d, dmin, dmax = compare_with_coords(
                item, c_nb, c_surface, angles, c_angle_min, c_angle_max)

            if s is None:
                if c:
                    c.scores[i] = INF, d, dmin, dmax
                continue

            if app.show_visual_log:
                app.visual_log('%s' % i)
                app.visual_log('%s: %s' % (i, s))

            if s != INF and (best is None or s < best[0]):
                best = (s, i, d, dmin, dmax)
            if i == app.training_current:
                target_score = (s, i, d, dmin, dmax)

            if c:
                c.scores[i] = (s, d, dmin, dmax)
        if c:
            c.surface = c_surface
            c.angle_min = angles[c_angle_min]
            c.angle_max = angles[c_angle_max]

        if best is not None:
            return best[1], best

        return None, target_score

    @classmethod
    def get_angles(cls, op):
        """for a list of touches, returns the list of angles between
           each ordered tripplet of points
        """
        angles = {}
        k = list(op.keys())
        l = len(k)
        C = cls.convert_touch_coords
        A = get_angle
        p = {x: C(op[x].pos) for x in op}

        for i, c in enumerate(k):
            a = A((
                p[k[(i - 1) % l]],
                p[k[i]],
                p[k[(i + 1) % l]]))
            angles[c] = abs(a)
        return angles

    @classmethod
    def convert_touch_coords(cls, pos):
        """Convert units from the window's relative size, to the
           configured detection frame size's, most of the time they are the
           same, but they may not, and nothing would work anymore in this
           case
        """
        x, y = pos
        w, h = Window.size
        X = x * app.screen_ratio_width / w
        Y = y * app.screen_ratio_height / h
        return X, Y

    def get_surface(self, op):
        """Return the surface between a set of points, currently only
           work for 3 points
        """
        # try to stop a crash because of touches deduplication
        if len(op) == 3:
            a, b, c = (
                self.convert_touch_coords(x.pos)
                for x in op.values()
            )
            return 0.5 * abs(
                (b[0] - a[0]) * (c[1] - a[1]) -
                (c[0] - a[0]) * (b[1] - a[1])  # noqa
            )
        elif len(op) < 2:
            return 0

    def collide_point(self, x, y):
        dx = (self.center_x - x) / (self.width / 2.)
        dy = (self.center_y - y) / (self.height / 2.)
        h = (dx ** 2 + dy ** 2) ** .5
        return h <= 1

    def adapt(self, oid):
        """Update an object's calibration to also match the current set
           of points
        """
        if not self.state == 'set':
            return

        self.calibrate(oid, update=True)

    def calib(self, oid, pos=None):
        """Starts an object's calibration routine
        """
        if self.state == 'set':
            self.calibrate(oid)
            return True
        else:
            return False

    def start_training(self, oid):
        app.mode = 'use'
        if self.objects_touches:
            message = 'remove all objects from the screen'
            Message(text=message,
                    callback=lambda *args: self.start_training(oid)).show()
            return
        Message(text='Put the object on the table').show()
        app.training[oid] = {}
        app.training_current = oid
        app.touch_buffer[oid] = {}

    def in_zones(self, pos):
        """Check if a touch if is in any of the declared detection zones
        """
        return not self.zones or any(
            z.collide_point(*pos) for z in self.zones)

    def get_combinations(self):
        """Get the set of currently available combinations of free
           touches, depending on app's state
        """
        nb = self.min_object_slots_nb
        if app.mode == 'use':
            touches = {
                t: self.touches[t] for t
                in self.free_touches
                if self.in_zones(self.touches[t].pos)}
        else:
            touches = {t: self.touches[t] for t in self.free_touches}

        l = len(touches)
        if l == nb:
            yield tuple(touches.keys())
        elif l > nb:
            touches_keys = list(touches.keys())
            maxd = app.max_distance_between_points

            for combination in xuniqueCombinations(
                touches_keys, touches, maxd, nb
            ):
                yield combination

    def add_missing_touch(self, obj, touch):
        obj.missing_map.append(touch)

    def fix_incomplete_objects(self):
        for _, o in self.objects.items():
            if not o.missing_map:
                continue
            # print "trying to fix %s" % o.missing_map
            best = None
            mintime = min(x.time_end for x in o.missing_map)
            for c in xuniqueCombinations(
                [
                    t for t in self.free_touches
                    if self.touches[t].time_start >= mintime
                ],
                self.touches,
                app.max_distance_between_points,
                len(o.missing_map)
            ):
                c_nb, c_surface, c_ratio, angles = self.touches2coordinates(
                    {k: self.touches[k] for k in tuple(o.touches_ids) + c})
                c_angle_min = min(angles, key=lambda x: angles[x])
                c_angle_max = max(angles, key=lambda x: angles[x])

                s, d, dmin, dmax = self.compare_with_coords(
                    self.coordinates[o.oid],
                    c_nb, c_surface, angles, c_angle_min, c_angle_max)

                if s != INF and (best is None or s < best[0]):
                    best = (s, c, c_angle_min)

            if best:
                for k, c in self.candidates_widgets.items():
                    if any(get_tid(t) in k for t in o.missing_map):
                        for t in o.missing_map:
                            try:
                                c.touches.remove(get_tid(t))
                            except ValueError:
                                pass
                        c.touches.extend(best[1])
                        del(self.candidates_widgets[k])
                        self.candidates_widgets[tuple(c.touches)] = c

                if o.angle_ref_touch in [get_tid(x) for x in o.missing_map]:
                    if len(o.missing_map) == 1:
                        # if there is only one missing touch, we can
                        # guess the missing angle_ref_touch is this one
                        t = [t for t in best[1] if t not in o.touches_ids][0]
                        o.angle_ref_touch = get_tid(self.touches[t])
                    else:
                        # else we have to hope the angle mesure is
                        # consistent with the first detection.
                        o.angle_ref_touch = get_tid(self.touches[best[2]])
                    Logger.debug("new angle_ref_touch is touch {}".format(
                        o.angle_ref_touch))
                o.missing_map = []
                # print "before fixing", o.touches_ids
                o.touches_ids.extend(best[1])
                # print "after fixing", o.touches_ids
                # self.update_objects_touches()
                self.update_objects(o.tid)
                self.lost_objects = [
                    o_ for o_ in self.lost_objects if o_[0] != o.tid]

            if app.cleanup_matched_objects:
                self.cleanup_candidates()

    def show_training_stats(self, oid, training_set):
        """Process the results of a training set, into
           human-understandable results
        """

        samples = []
        errors = 0
        failures = 0
        successes = 0
        directs = 0
        success_surface_diff = 0
        success_angle_diff = 0
        miss_surface_diff = 0
        miss_angle_diff = 0

        success_points = []
        error_points = []
        failure_points = []

        for k, v in training_set.items():
            success = False
            samples += [len(v)]
            error = False
            direct = True
            for r in v:
                if r[1] == oid and r[0] < INF:
                    success = True
                    success_surface_diff += r[2]
                    success_angle_diff += r[3] + r[4]
                    success_points.append((r[2], max(r[3:4])))

                elif r[1] != oid:
                    error = True
                    error_points.append((r[2], max(r[3:4])))

                else:
                    miss_surface_diff += r[2] / len(v)
                    miss_angle_diff += (r[3] + r[4]) / len(v)
                    direct = False
                    failure_points.append((r[2], max(r[3:4])))

            if success:
                successes += 1
                if direct:
                    directs += 1
            elif error:
                errors += 1
            else:
                failures += 1

        miss_surface_diff = (miss_surface_diff / failures) if failures else 0

        miss_angle_diff = (miss_angle_diff / (failures * 2)) if failures else 0

        average_surface_diff = (
            (miss_surface_diff + success_surface_diff) /
            (successes + failures))

        average_angle_diff = (
            (miss_angle_diff + success_angle_diff) /
            ((successes + failures) * 2))

        ResultsPopup(
            successes=successes,
            errors=errors,
            failures=failures,
            directs=directs,
            average_surface_diff=average_surface_diff,
            average_angle_diff=average_angle_diff,
            miss_angle_diff=miss_angle_diff,
            miss_surface_diff=miss_surface_diff,
            samples=sum(samples),
            average_samples_per_candidate=sum(samples) / len(samples),
            normalized_samples=app.touch_buffer[oid].values(),
            error_points=error_points,
            failure_points=failure_points,
            success_points=success_points,
        ).open()

    def update_training(self, result, combination):
        training = app.training[app.training_current]
        training.setdefault(combination, set())
        training[combination].add(result[1])
        f = lambda x: x[1] == app.training_current and x[0] < INF

        if result[0]:
            Message(
                text='{success}({direct})/{combinations}'.format(
                    success=len(filter(lambda x: any(map(f, x)),
                                       training.values())),
                    direct=len(filter(lambda x: all(map(f, x)),
                                      training.values())),
                    combinations=len(training.keys()),
                )
            ).show()
        if len(training) >= app.training_length:
            self.show_training_stats(app.training_current, training)
            app.mode = 'main'
        else:
            return True

    def collect_objects(self, dt):
        t = time()
        to_delete = []
        for tid, timeout in self.lost_objects[:]:
            if timeout < t:
                self.remove_widget(self.objects[tid])
                oid = self.objects[tid].oid

                del(self.objects[tid])
                to_delete.append(tid)

        self.lost_objects = [
            o for o in self.lost_objects if o[0] not in to_delete]

    def find_object(self, dt):
        t = time()
        if not self.free_touches:
            Clock.schedule_once(
                self.find_object, app.object_detection_interval)
            return

        coordinates = self.coordinates

        self.fix_incomplete_objects()

        # make groups of slots(touches) that are potential objects
        for c in self.get_combinations():
            touches = {k: self.touches[k] for k in c}

            current = self.touches2coordinates(touches)
            if current:
                angle_ref = min(current[-1], key=lambda x: current[-1][x])
            else:
                continue

            result = self.compare_with_calib(coordinates, current, tuple(c))

            if app.training_current and (result[0] or INF not in result[1][1:]):
                if self.update_training(result, c):
                    oid = app.training_current
                    touch_buffer = app.touch_buffer[oid]
                    buffering = touch_buffer.setdefault(tuple(c), [])
                    angles = self.get_angles(touches)

                    obj = TangibleObject(
                        size=(130, 130),
                        oid=oid,
                        tid=self.get_free_tid(),
                        touches_ids=c,
                        angle_ref_touch=min(angles, key=lambda x: angles[x]),
                        angle_offset=coordinates[oid]['angle_offset'],
                        partially_calibrated=coordinates[oid]['new'],
                        birthdate=0
                    )

                    center, angle = self.get_center_angle(obj, touches)
                    target_angle = random.gauss(1, .055) * angle % 360
                    if target_angle > 180:
                        target_angle -= 360

                    normalized_coords = []
                    for touch in touches.values():
                        vector = Vector(
                            touch.x - center[0],
                            touch.y - center[1]
                        )
                        vector = vector.rotate(target_angle)
                        normalized_coords.append((vector.x, vector.y))

                    buffering += normalized_coords

            if not result[0]:
                continue

            oid = result[0]
            score, _, d_surface, d_min, dmax = result[1]

            # update self.objects with new objects
            tid = self.get_free_tid()
            self.objects[tid] = to = TangibleObject(
                size=(130, 130),
                oid=oid,
                tid=tid,
                touches_ids=c,
                angle_ref_touch=angle_ref,
                angle_offset=self.coordinates[oid]['angle_offset'],
                partially_calibrated=self.coordinates[oid]['new'],
                birthdate=app.time)

            Logger.debug('object detected: {}'.format(oid))

            self.add_widget(to)
            self.update_objects_touches()
            self.update_objects(tid)
            break

        if app.cleanup_matched_objects:
            self.cleanup_candidates()

        dt = time() - t
        # automatically adapt to current load
        Clock.schedule_once(self.find_object, 25 * dt)

    def cleanup_candidates(self):
        for k, c in list(self.candidates_widgets.items()):
            if (
                any(t in self.objects_touches for t in c.touches) or
                not all(t in self.touches for t in c.touches)
            ):
                self.remove_candidate(k)

    def get_center_angle(self, obj, touches):
        # print touches
        points = []
        for i, item in touches.items():
            points.append(item.pos)
        if app.keep_missing_touches:
            for i in obj.missing_map:
                points.append(i.pos)
        # center
        try:
            x, y = zip(*points)
            center = (sum(x) / len(x), sum(y) / len(y))
            # self.current_object_center = center
        except:
            return (None, None)
        # angle
        # get first pos
        reftouch = touches.get(obj.angle_ref_touch)
        if not reftouch:
            # first look into missing touches ids for the reftouch
            for t in obj.missing_map:
                tid = get_tid(t)
                if tid == obj.angle_ref_touch:
                    reftouch = t
                    break

        if (
            (obj.missing_map and app.keep_angle_on_incomplete_object) or
            not reftouch
        ):
            angle = None
            Logger.trace("keeping object angle, {}".format(angle))
        else:
            pos = reftouch.pos
            # get vect formed with center pos
            first_vect = Vector(pos)
            center_vect = Vector(center)
            vect = first_vect - center_vect
            # get angle value from orthogonal vector
            angle = -vect.angle(Vector(0, 1)) % 360.

        # self.current_object_angle = angle
        return (center, angle)

    def update_objects_touches(self):
        objects = self.objects
        objects_touches = set()
        for obj in objects.values():
            objects_touches.update(obj.touches_ids)

        self.objects_touches = objects_touches

    def update_objects(self, tid):
        if tid in ('None', None):
            return

        objects = self.objects
        # Update center and angle for new object
        touches = {
            t: self.touches[t]
            for t in self.objects[tid].touches_ids
        }
        o = objects[tid]
        center, angle = self.get_center_angle(o, touches)

        if (
            not o.missing_map and
            not list(xuniqueCombinations(
                o.touches_ids, self.touches,
                app.max_distance_between_points,
                self.min_object_slots_nb))
        ):
            self.remove_widget(o)
            del(objects[tid])
            return

        if o.partially_calibrated or app.mode == 'main':
            if (
                app.config.getboolean('apparence', 'display_surface') and
                not o.missing_map
            ):
                o.surface = self.get_surface(touches)

            if (
                app.config.getboolean('apparence', 'display_angle') and
                not o.missing_map
            ):
                angles = self.get_angles(touches).values()
                o.display_angle = max(angles), min(angles)

        dt = Clock.frametime
        if center is not None:
            dx = (center[0] - o.center[0]) / dt
            dy = (center[1] - o.center[1]) / dt
            # o.m = (o.m[0] + o.dx) / 2., (o.m[1] + o.dy) / 2.
            o.m = dx - o.dx, dy - o.dy
            o.dx = dx
            o.dy = o.dy
            o.center = center
        if angle is not None:
            angle -= o.angle_offset
            da = (angle - o.angle) / dt
            o.dr = o.da - da
            o.da = da
            d = angle_diff(o.angle, angle % 360)
            if not app.do_angle_filtering or abs(d) < app.angle_threshold:
                o.angle = angle % 360.

        # TUIO Send
        if tid in self.objects:
            self.send_tuio_object(tid)

    def touches2coordinates(self, touches):
        nb = len(touches)
        if nb < self.min_object_slots_nb:
            return

        angles = self.get_angles(touches)
        surface = self.get_surface(touches)

        ar = 1

        return nb, surface, ar, angles

    def forget(self, oid):
        Logger.debug('forget object {}'.format(oid))
        for k, v in list(self.objects.items()):
            if v.oid == oid:
                try:
                    self.remove_widget(self.objects[k])
                    self.objects.pop(k)
                except:
                    pass

        if oid in self.coordinates:
            self.coordinates.pop(oid)

        self.update_max_distance()

    def update_max_distance(self):
        if self.coordinates:
            m = max(o.get('maxdist', 0) for o in self.coordinates.values())
        else:
            m = 0

        app.max_distance_between_points = m

    def set_coordinates(
        self, oid, nb, surface, ar, angles, set_offset=None, new=False,
        update=False, maxdist=0
    ):
        # print "set coordinate called"
        angle_min = min(angles, key=lambda x: angles[x])
        angle_max = max(angles, key=lambda x: angles[x])
        o = self.coordinates[oid]
        if update:
            loc = locals()
            for x in ('surface', 'angle_min', 'angle_max'):
                if 'angle' in x:
                    diff = angles[loc[x]] - o[x]
                    tolerance = app.angle_tolerance
                else:
                    diff = loc[x] - o[x]
                    tolerance = app.surface_tolerance
                if abs(diff) > tolerance:
                    loc[x] = o[x] + diff / abs(diff) * tolerance

        o['nb'] = nb
        o['surface'] = surface
        o['aspect_ratio'] = ar
        o['angle_min'] = angles[angle_min]
        o['angle_max'] = angles[angle_max]
        o['new'] = new and not update
        o['maxdist'] = maxdist or app.max_distance_between_points

        if set_offset:
            x, y = zip(*(x.pos for x in set_offset.values()))
            center = (sum(x) / len(x), sum(y) / len(y))
            # needs a list of 3 points
            pos = set_offset[angle_min].pos
            # get vect formed with center pos
            first_vect = Vector(pos)
            center_vect = Vector(center)
            vect = first_vect - center_vect
            # get angle value from orthogonal vector
            offset = - vect.angle(Vector(0, 1)) % 360.
            # print "offset = %s" % offset
            self.coordinates[oid]['angle_offset'] = offset

    def calibrate(self, oid, update=False):
        Logger.debug('calibrating oid: "{}" (update={})'.format(oid, update))
        if not update:
            self.coordinates[oid] = {}

        touches = {k: self.touches[k] for k in self.free_touches}
        coords, touches = self.touches2coordinates(touches), touches

        real_touches = touches.values()
        m = 0

        for t in real_touches:
            for t2 in real_touches:
                m = max(m, dist(t.pos, t2.pos) * app.point_box_size_multiplier)

        self.set_coordinates(
            oid, *coords, set_offset=touches, update=update, new=True,
            maxdist=m)

        self.update_max_distance()

    def touch2objects(self, touch_id):
        objs = []
        for id2, item in self.objects.items():
            if touch_id in item.touches_ids:
                objs.append(id2)
        return objs

    def update_objects_pos(self, touchid):
        for tid in self.touch2objects(touchid):
            self.update_objects(tid)

    def flush_tuio(self, dt):
        self.tuio_counter += 1
        messages = []
        alive = tuple(int(x) for x in self.objects.keys())
        messages.append((b'/tuio/2Dobj', (b'alive',) + alive))

        while self.messages_objects:
            data = self.messages_objects.popleft()
            messages.append((b'/tuio/2Dobj', (b'set', ) + data))

        messages.append((b'/tuio/2Dobj', (b'fseq', self.tuio_counter)))
        bundle = format_bundle(messages)[0]
        for ip in app.send_tuio_ip.split(','):
            try:
                for p in app._send_tuio_port:
                    SOCK.sendto(bundle, (ip, p))
            except socket.error:
                Message(
                    text="invalid tuio ip ('{}'), disabling for {} seconds.".
                    format(ip, 5)
                ).show()
                app.send_tuio_touch = False
                app.send_tuio_obj = False
                Clock.schedule_once(app.activate_tuio, 5)
                continue

        # touches
        self.tuio_counter += 1
        messages = []
        tt = self.touches.keys()
        ot = self.objects_touches
        alive = tuple(int(x) for x in tt if x not in ot)
        messages.append((b'/tuio/2Dcur', (b'alive', ) + alive))

        while self.messages_touches:
            data = self.messages_touches.popleft()
            if data[0] in alive:
                messages.append((b'/tuio/2Dcur', (b'set', ) + data))

        messages.append((b'/tuio/2Dcur', (b'fseq', self.tuio_counter)))
        bundle = format_bundle(messages)[0]
        for ip in app.send_tuio_ip.split(','):
            try:
                for p in app._send_tuio_port:
                    SOCK.sendto(bundle, (ip, p))
            except socket.error:
                Message(
                    text="invalid tuio ip ('{}'), disabling for {} seconds.".
                    format(ip, 5)
                ).show()
                app.send_tuio_touch = False
                app.send_tuio_obj = False
                Clock.schedule_once(app.activate_tuio, 5)
                continue

    def send_tuio_object(self, tid):
        if not app.send_tuio_obj:
            return
        W = Window.width
        H = Window.height
        # objects
        # retrieve coordinates
        obj = self.objects[tid]
        oid = obj.oid
        oid = obj.oid
        x, y = obj.center
        x = float(x / W)
        y = float(1 - y / H)
        a = float(radians(obj.angle))
        # dt = Clock.frametime
        # X = float(obj.dx / W)
        # Y = float(- obj.dy / H)
        # A = float(radians(obj.da))
        # r = float(obj.dr)
        # m = float((obj.m[0] ** 2 + obj.m[1] ** 2) ** .5)
        # message.append(mode)
        # data
        # for i in [int(oid), int(oid), x, y, a, X, Y, A, m, r]:
        self.messages_objects.append(
            (int(tid), int(oid), x, y, a, 0.1, 0.1, 0.1, 0.1, 0.1))

    def send_tuio_touch(self, tid):
        if not app.send_tuio_touch:
            return
        W = Window.width
        H = Window.height
        dt = Clock.frametime
        # retrieve coordinates
        touches = self.touches
        if tid not in touches.keys():
            return
        if tid in self.objects_touches:
            return  # omit touches that are affected to objects
        touch = touches[tid]
        x, y = touch.pos
        x = x / W
        y = 1 - y / H
        X = touch.dsx / dt
        Y = touch.dsy / dt
        # data
        try:
            self.messages_touches.append((
                int(tid), x, y, X, Y, .0
                # .0, .0, .0, .0, .0, .0, .0, .0, .0, .0, .0, .0
            ))

        except ValueError:
            Logger.info('TUIO: %s is not an integer, cancel' % tid)
            return

    def add_point(self, tid, touch):
        self.touches_points[tid] = tp = Factory.TouchPoint()
        tp.touch = touch,
        tp.tid = str(tid)
        self.add_widget(tp)

    def on_touch_down(self, touch):
        if super(DetectionZone, self).on_touch_down(touch):
            return True

        elif app.mode == 'zones':
            if any(map(lambda x: isinstance(x, TimeoutAction), self.children)):
                return
            ta = TimeoutAction(size_hint=(None, None),
                               action=self.create_zone,
                               timeout=1)
            self.add_widget(ta)
            ta.start(touch)
            return True

        elif self.collide_point(*touch.pos):
            tid = get_tid(touch)
            if app.display_touches:
                self.add_point(tid, touch)

            self.touches[tid] = touch
            touch.grab(self)
            # send tuio
            self.send_tuio_touch(tid)
            if (
                self.in_zones(touch.pos) or not
                app.config.getboolean(
                    'retain touch', 'use_retain_touch_inside_zone')
            ):
                touch.ud['retain_touch'] = True
            return True

    def on_touch_move(self, touch):
        tid = get_tid(touch)
        if app.display_touches and tid in self.touches_points:
            self.touches_points[tid].pos = touch.pos

        if app.display_scores and tid in self.touches:
            for k, c in list(self.candidates_widgets.items()):
                if tid in c.touches:
                    maxd = app.max_distance_between_points
                    if any(
                        dist(self.touches[tid].pos,
                             self.touches[t].pos) > maxd
                        for t in c.touches
                        if t != tid and t in self.touches
                    ):
                        self.remove_candidate(k)
                        break
                    else:
                        c.update()

        if not self.collide_point(*touch.pos):
            if 'retain_touch' in touch.ud:
                touch.ud.pop('retain_touch')
            if tid in self.touches:
                del(self.touches[tid])

                # delete relative objects
                to_delete = self.touch2objects(tid)

                for id2 in to_delete:
                    self.remove_widget(self.objects[id2])
                    del(self.objects[id2])

                self.update_objects_touches()

            return super(DetectionZone, self).on_touch_move(touch)

        if tid not in self.touches:
            self.touches[tid] = touch
            # schedule objects list update in 1 second
            if (
                self.in_zones(touch.pos) or not
                app.config.getboolean(
                    'retain touch', 'use_retain_touch_inside_zone')
            ):
                touch.ud['retain_touch'] = True
            elif 'retain_touch' in touch.ud:
                touch.ud.pop('retain_touch')

        self.update_objects_pos(tid)

        if app.config.getboolean('tuio', 'send_tuio_touch_send_touch_move'):
            self.send_tuio_touch(tid)

        return super(DetectionZone, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        tid = get_tid(touch)
        if app.display_touches and tid in self.touches_points:
            self.remove_widget(self.touches_points.pop(tid))

        for c in list(self.candidates_widgets.keys()):
            if tid in c and not any(t in self.objects_touches for t in c):
                self.remove_widget(self.candidates_widgets.pop(c))

        if tid in list(self.touches.keys()):
            objs = self.touch2objects(tid)

            # XXX why would a touch be part of multiple objects?
            for tid_obj in objs:
                o = self.objects[tid_obj]
                o.touches_ids.remove(tid)
                self.add_missing_touch(o, touch)

                if not o.touches_ids:
                    self.lost_objects.append((
                        tid_obj, time() + app.lost_object_timeout / 1000.))

            del(self.touches[tid])

            self.update_objects_touches()

        if touch.grab_current is self:
            touch.ungrab(self)
        return super(DetectionZone, self).on_touch_up(touch)

    def remove_candidate(self, candidate):
        try:
            self.remove_widget(self.candidates_widgets.pop(candidate))
        except KeyError:
            pass

    def create_zone(self, touch):
        z = ZoneDefinition(sx=touch.sx, sy=touch.sy, sh=.1, sw=.1)
        self.zones.append(z)
        self.add_widget(z)

    def on_objects(self, *args):
        for o in list(self.graphs.keys()):
            if o not in self.objects:
                self.graphzone.remove_widget(self.graphs.pop(o))

        if not app.display_stats:
            return

        for o in self.objects:
            if o not in self.graphs:
                graph = TangibleObjectDataGraph(target=self.objects[o])
                self.graphs[o] = graph
                self.graphzone.add_widget(graph)
                sv = self.graphzone.parent.parent
                if not sv.scroll_y:
                    sv.scroll_y = 1
                Animation(scroll_y=0, d=.5, t='out_quad').start(sv)
                # print "added widget"

    def recenter_anim(self):
        a = Animation(
            center=App.get_running_app().root.center, d=.5, t='out_elastic')
        a.bind(on_complete=lambda *x:
               self.setter('pos_hint')(self, {'center': (.5, .5)}))
        return a


class ResultsPopup(Popup):
    successes = NumericProperty()
    directs = NumericProperty()
    failures = NumericProperty()
    errors = NumericProperty()
    samples = NumericProperty()
    average_samples_per_candidate = NumericProperty()
    average_surface_diff = NumericProperty()
    average_angle_diff = NumericProperty()
    miss_surface_diff = NumericProperty()
    miss_angle_diff = NumericProperty()
    normalized_samples = ListProperty()
    success_points = ListProperty()
    failure_points = ListProperty()
    error_points = ListProperty()


class ZoneDefinition(Widget):
    sx = NumericProperty(0)
    sy = NumericProperty(0)
    sw = NumericProperty(0)
    sh = NumericProperty(0)
    corner_size = NumericProperty(50)

    def on_touch_down(self, touch):
        if app.mode == 'zones':
            if super(ZoneDefinition, self).on_touch_down(touch):
                return True
            if self.ids.lock.state == 'down':
                return False

            vt = Vector(*touch.pos)
            # if vt.distance(self.center) < 10:
            #     self.destroy()
            #     return True
            if vt.distance(self.pos) < self.corner_size:
                touch.ud['corner'] = 0
                touch.grab(self)
                return True
            elif vt.distance((self.right, self.y)) < self.corner_size:
                touch.ud['corner'] = 1
                touch.grab(self)
                return True
            elif vt.distance((self.right, self.top)) < self.corner_size:
                touch.ud['corner'] = 2
                touch.grab(self)
                return True
            elif vt.distance((self.x, self.top)) < self.corner_size:
                touch.ud['corner'] = 3
                touch.grab(self)
                return True
            elif self.collide_point(*touch.pos):
                touch.ud['corner'] = (touch.sx - self.sx, touch.sy - self.sy)
                touch.grab(self)
                return True

        return super(ZoneDefinition, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return super(ZoneDefinition, self).on_touch_move(touch)

        corner = touch.ud['corner']

        if corner == 0:
            self.sw -= touch.sx - self.sx
            self.sh -= touch.sy - self.sy
            self.sx = touch.sx
            self.sy = touch.sy

        elif corner == 1:
            self.sw = touch.sx - self.sx
            self.sh -= touch.sy - self.sy
            self.sy = touch.sy

        elif corner == 2:
            self.sw = touch.sx - self.sx
            self.sh = touch.sy - self.sy

        elif corner == 3:
            self.sh = touch.sy - self.sy
            self.sw -= touch.sx - self.sx
            self.sx = touch.sx

        else:
            self.sx = touch.sx - corner[0]
            self.sy = touch.sy - corner[1]

        if self.sw < 0:
            self.sw *= -1
            self.sx -= self.sw
            touch.ud['corner'] = (corner + (-1 if corner % 2 else 1)) % 4

        if self.sh < 0:
            self.sh *= -1
            self.sy -= self.sh
            touch.ud['corner'] = (corner + (1 if corner % 2 else -1)) % 4

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super(ZoneDefinition, self).on_touch_up(touch)
        touch.ungrab(self)

    def destroy(self):
        self.parent.zones.remove(self)
        self.parent.remove_widget(self)

    def to_list(self):
        return [self.sx, self.sy, self.sw, self.sh]

    @staticmethod
    def from_list(data):
        return ZoneDefinition(sx=data[0], sy=data[1], sw=data[2], sh=data[3])


class LoadSaveButton(Button):
    target = StringProperty('')
    dialog = ObjectProperty(None)


class SaveDialog(OVPopup):
    target = StringProperty(u'')

    def __init__(self, **kwargs):
        super(SaveDialog, self).__init__(**kwargs)
        self.populate()

    def populate(self):
        self.ids.box.clear_widgets()
        for p in app.config.sections():
            if not p.startswith(u'profile-'):
                continue
            b = LoadSaveButton(target=p[len(u'profile-'):], dialog=self)
            self.ids.box.add_widget(b)

    def action(self):
        Logger.debug('saving to profile "{}"'.format(self.target))
        target = self.target
        app.save_objects(profile=target)
        app.save_zones(profile=target)
        app.profile = self.target
        app.config.write()

    def delete_profile(self):
        target = self.target
        app.config.remove_section(u'profile-' + target)
        self.populate()


class LoadDialog(SaveDialog):
    def action(self):
        Logger.debug('switching to profile "{}"'.format(self.target))
        app.profile = self.target


class ProgressiveLabel(Label):
    target_text = StringProperty('')
    interval = NumericProperty(0.07)

    def on_target_text(self, *args):
        Clock.unschedule(self.update_text)
        self.text = ''
        Clock.schedule_interval(self.update_text, self.interval)

    def update_text(self, *args):
        self.text += self.target_text[len(self.text)]
        if self.text == self.target_text:
            return False


class CloseButton(Image):
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            ta = TimeoutAction(timeout=2, action=lambda *x: self.callback())
            self.add_widget(ta)
            ta.start(touch)
            if app.mode == 'zones':
                return True
        return super(CloseButton, self).on_touch_down(touch)

    def callback(self, button=None, *args):
        Clock.unschedule(self.close)
        a = Animation(center=self.center, d=.5, t='out_quad')
        a.bind(on_complete=lambda *x: x[1].parent and self.remove_widget(x[1]))
        if button:
            a.start(button)
            n = int(button.text) + 1
        else:
            n = 1

        if n == 4:
            if app.mode == 'main':
                app.stop()
            else:
                app.mode = 'main'
            return

        b = Button(
            size=(50, 50),
            text='%s' % n,
            background_normal='atlas://data/theme/bg_piece',
            background_down='atlas://data/theme/bg_piece',
            border=(8, 8, 21, 25),
            pos=self.pos,
            size_hint=(None, None))

        b.bind(on_press=self.callback)

        self.add_widget(b)

        Animation(
            center=(
                self.center_x + cos(-n * pi / 8) * 100,
                self.center_y + sin(-n * pi / 8) * 100),
            t='out_elastic', d=.5).start(b)
        Clock.schedule_interval(lambda *x: self.close(b), 3)

    def close(self, button):
        a = Animation(center=self.center, d=.5, t='out_quad')
        a.bind(on_complete=lambda *x: x[1].parent and self.remove_widget(x[1]))
        a.start(button)


class Application(App):
    mode = OptionProperty('main', options=['main', 'use', 'zones'])
    profile = StringProperty(u'')
    log = ListProperty([])
    time = NumericProperty(0)
    icon = StringProperty('data/icons/icon.ico')
    training = DictProperty()
    training_current = StringProperty()
    touch_buffer = DictProperty()
    demo = BooleanProperty(False)
    expired = BooleanProperty(False)
    demo_timeout = NumericProperty()
    countdown_message = ObjectProperty(allownone=True)
    license_popup = ObjectProperty(allownone=True)
    use_kivy_settings = False
    name = StringProperty(NAME)
    title = StringProperty(NAME)
    lang = ConfigParserProperty('en', 'general', 'lang', 'app', val_type=str)
    settings_vars = DictProperty(
        {
            u'NAME': NAME,
        }
    )

    def get_software(self):
        return NAME

    def set_software(self, value):
        pass

    software = AliasProperty(get_software, set_software)

    def get_software_dir(self):
        return dirname(self.get_application_config())

    def set_software_dir(self, value):
        pass

    software_dir = AliasProperty(get_software_dir, set_software_dir)

    send_tuio_touch = BooleanProperty(True)
    send_tuio_obj = BooleanProperty(True)

    auto_use = ConfigParserProperty(
        False, 'general', 'auto_use', 'app', val_type=configbool)
    auto_save = ConfigParserProperty(
        False, 'general', 'auto_save', 'app', val_type=configbool)
    minimized_start = ConfigParserProperty(
        False, 'general', 'minimized_start', 'app', val_type=configbool)

    dev_mode = ConfigParserProperty(
        False, 'general', 'dev_mode', 'app', val_type=configbool)

    confirm_exit = ConfigParserProperty(
        False, 'general', 'confirm_exit', 'app', val_type=configbool)

    screen_mode = ConfigParserProperty('', 'general', 'screen_mode', 'app')

    screen_ratio_width = ConfigParserProperty(
        0, 'tuio', 'screen_ratio_width', 'app', val_type=float)
    screen_ratio_height = ConfigParserProperty(
        0, 'tuio', 'screen_ratio_height', 'app', val_type=float)

    max_distance_between_points = ConfigParserProperty(
        0, 'detection', 'max_distance_between_points', 'app', val_type=float)

    point_box_size_multiplier = ConfigParserProperty(
        0, 'detection', 'point_box_size_multiplier', 'app', val_type=float)

    surface_tolerance = ConfigParserProperty(
        300, 'detection', 'surface_tolerance', 'app', val_type=float)

    angle_tolerance = ConfigParserProperty(
        0, 'detection', 'angle_tolerance', 'app', val_type=float)

    send_tuio_port = ConfigParserProperty(
        '', 'tuio', 'send_tuio_port', 'app')
    send_tuio_ip = ConfigParserProperty(
        '127.0.0.1', 'tuio', 'send_tuio_ip', 'app', val_type=str)

    tuio_flush_interval = ConfigParserProperty(
        0, 'tuio', 'tuio_flush_interval', 'app', val_type=float)

    display_stats = ConfigParserProperty(
        True, 'apparence', 'display_stats', 'app', val_type=configbool)

    display_touches = ConfigParserProperty(
        False, 'detection', 'display_touches', 'app', val_type=configbool)

    show_visual_log = ConfigParserProperty(
        False, 'detection', 'show_visual_log', 'app', val_type=configbool)

    display_scores = ConfigParserProperty(
        False, 'detection', 'display_scores', 'app', val_type=configbool)

    cleanup_matched_objects = ConfigParserProperty(
        False, 'detection', 'cleanup_matched_objects', 'app',
        val_type=configbool)

    object_detection_interval = ConfigParserProperty(
        0, 'detection', 'object_detection_interval', 'app', val_type=float)

    keep_missing_touches = ConfigParserProperty(
        True, 'detection', 'keep_missing_touches', 'app', val_type=configbool)

    training_length = ConfigParserProperty(
        10, 'detection', 'training_length', 'app', val_type=int)

    do_angle_filtering = ConfigParserProperty(
        False, 'behavior', 'do_angle_filtering', 'app', val_type=configbool)

    angle_threshold = ConfigParserProperty(
        180, 'behavior', 'angle_threshold', 'app', val_type=float)

    touch_filter_min_distance = ConfigParserProperty(
        0, 'behavior', 'touch_filter_min_distance', 'app', val_type=int)

    touch_filter_min_time = ConfigParserProperty(
        0, 'behavior', 'touch_filter_min_time', 'app', val_type=float)

    hidden_use_mode = ConfigParserProperty(
        False, 'general', 'hidden_use_mode', 'app', val_type=configbool)

    keep_angle_on_incomplete_object = ConfigParserProperty(
        True, 'detection', 'keep_angle_on_incomplete_object', 'app',
        val_type=configbool)

    tolerance_sigma_warning = ConfigParserProperty(
        0, 'detection', 'tolerance_sigma_warning', 'app', val_type=float)

    lost_object_timeout = ConfigParserProperty(
        250, 'detection', 'lost_object_timeout', 'app', val_type=float)

    retain_distance = ConfigParserProperty(
        0, 'retain touch', 'retain_distance', 'app', val_type=int)

    retain_time = ConfigParserProperty(
        0, 'retain touch', 'retain_time', 'app', val_type=int)

    double_touch_delay = ConfigParserProperty(
        0, 'behavior', 'double_touch_delay', 'app', val_type=float)

    undetect_outside_zones = ConfigParserProperty(
        False, 'detection', 'undetect_outside_zones', 'app',
        val_type=configbool)

    def _get_opacity(self):
        if platform == 'win':
            try:
                return winxpgui.GetLayeredWindowAttributes(HWND)[1] / 255.
            except Exception as e:
                Logger.error(
                    'failed to get opacity: {}'.format(e))

        else:
            Logger.warning(
                'window get opacity not implemented on {}'.format(platform))
        return 1

    def _set_opacity(self, value):
        if platform == 'win':
            win32gui.SetWindowLong(
                HWND, win32con.GWL_EXSTYLE,
                win32gui.GetWindowLong(
                    HWND, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
            winxpgui.SetLayeredWindowAttributes(
                HWND, win32api.RGB(0, 0, 0), max(1, int(value * 255)),
                win32con.LWA_ALPHA)

            return True
        else:
            Logger.error(
                'window set opacity not implemented on {}'.format(platform)
            )

    opacity = AliasProperty(_get_opacity, _set_opacity)

    def get_application_config(self):
        if exists('{}.ini'.format(self.name)):
            path = '{}.ini'.format(self.name)
        else:
            path = '~/%(appname)s/%(appname)s.ini'

        cfg = super(Application, self).get_application_config(path)
        d = dirname(cfg)
        if d and not exists(d):
            makedirs(d)
        return cfg

    def build_config(self, config):
        config.setdefaults('general', {
            'auto_use': False,
            'minimized_start': False,
            'auto_save': False,
            'profile': u'default',
            'confirm_exit': True,
            'hidden_use_mode': False,
            'dev_mode': False,
            'lang': 'en',
            'screen_mode': 'primary',
        })
        config.setdefaults('detection', {
            'max_distance_between_points': 0,
            'point_box_size_multiplier': 3,
            'min_object_slots_nb': 3,
            'max_object_slots_nb': 3,
            'surface_tolerance': 150,
            'angle_tolerance': 3,
            'nb_value_average': 300,
            'show_visual_log': False,
            'keep_missing_touches': False,
            'tolerance_sigma_warning': 2,
            'undetect_outside_zones': False,
            'object_detection_interval': .1,
            'display_scores': False,
            'cleanup_matched_objects': False,
            'keep_angle_on_incomplete_object': True,
            'lost_object_timeout': 250,
        })
        config.setdefaults('tuio', {
            'send_tuio_touch_send_touch_move': True,
            'send_tuio_port': '3337-3340',
            'send_tuio_ip': '127.0.0.1',
            'screen_ratio_width': 1920.,
            'screen_ratio_height': 1080.,
            'tuio_flush_interval': .05,
        })
        config.setdefaults('profile-default', {
            'zones': '[]',
            'objects': '{}'
        })
        config.setdefaults('apparence', {
            'display_surface': True,
            'display_angle': True,
            'display_stats': True,
        })
        config.setdefaults('retain touch', {
            'use_custom_retaintouch': True,
            'use_retain_touch_inside_zone': True,
            'retain_distance': 50,
            'retain_time': 0
        })
        config.setdefaults('behavior', {
            'do_angle_filtering': False,
            'angle_threshold': 90,
            'double_touch_delay': 0.05,
            'touch_filter_min_distance': 20,
            'touch_filter_min_time': .1,
        })
        config.setdefaults('filter', {
            'do_filter_touches': False,
            'min_duration': 0,
            'max_speed': 0
        })

    def _filter_config(self, values):
        for value in values:
            if 'platform' in value and platform != value['platform']:
                continue
            elif 'dev_only' in value and not self.dev_mode:
                continue
            yield {
                k: v
                for k, v in value.items()
                if k not in ('platform', 'dev_only')
            }

    def load_config(self):
        config = super(Application, self).load_config()
        if not config.filename:
            config.filename = self.get_application_config()

    def build_settings(self, settings):
        Logger.info('build settings')
        settings.register_type('tr_string', Factory.TrSettingString)
        settings.register_type('tr_bool', Factory.TrSettingBoolean)
        settings.register_type('tr_numeric', Factory.TrSettingNumeric)
        settings.register_type('tr_options', Factory.TrSettingOptions)
        settings.register_type('tr_langs', Factory.TrLangs)
        settings.register_type('tr_title', Factory.TrSettingTitle)
        settings.register_type('tr_path', Factory.TrSettingPath)
        with open(resource_find('settings.json'), encoding='utf8') as f:
            j = json.load(f)
        Logger.info('json loaded')
        j2 = [r for r in self._filter_config(j)]

        settings.add_json_panel(
            NAME,
            self.config,
            data=json.dumps(j2)
        )

    def display_settings(self, settings):
        try:
            p = self.settings
        except:
            self.settings = p = OVPopup(content=settings, size_hint=(.5, .5))
            settings.bind(on_close=p.dismiss)
        p.open()

    def run(self):
        self.load_config()
        self.root = ROOT

        self.built = True

        return super(Application, self).run()

    def _win_find_hwnd(self, *args):
        global HWND
        HWND = win32gui.FindWindow(None, NAME)
        Logger.debug('FindWindow returned {}'.format(HWND))
        if not HWND:
            Clock.schedule_once(self._win_find_hwnd, .01)

    def on_start(self):
        Logger.debug('app starting')
        self.borderless_toggled = False
        if platform == 'win':
            self._win_find_hwnd()

        self.parse_ports()

        if self.config.getboolean('general', 'auto_use') and not (
                app.expired or app.demo):
            Clock.schedule_once(lambda *x: self.setter('mode')(self, 'use'), 0)
        if self.config.getboolean('general', 'minimized_start'):
            Window.minimize()

        self.profile = self.config.get('general', 'profile')

        if self.config.getboolean('retain touch', 'use_custom_retaintouch'):
            kivy_postproc_modules['retaintouch'] = \
                InputPostprocRetainTouch(self)

        if self.config.getboolean('filter', 'do_filter_touches'):
            kivy_postproc_modules['filter'] = \
                InputPostprocFilterTouches(self)

        self.bind(send_tuio_port=self.parse_ports)
        Clock.schedule_interval(self.update_time, 0)

        Window.bind(on_key_down=self.manage_keyboard)
        self.check_disk_space()
        if self.config.getboolean('general', 'hidden_use_mode'):
            self.borderless_toggled = True
            self.toggle_borders(5)

        self.position_screen(*get_screen_resolution(self.screen_mode))

    def on_screen_mode(self, *args):
        self.position_screen(*get_screen_resolution(self.screen_mode))

    def position_screen(self, screenx, screentop, screenwidth, screenheight):
        Window.size = (screenwidth, screenheight)
        Window.top = screentop
        Window.left = screenx

    def check_disk_space(self, *args):
        if FileHandler.filename:
            d = dirname(FileHandler.filename)
        else:
            d = dirname(self.get_application_config())
        free = disk_usage(d).free

        if free < 32 * 10 ** 6:
            Factory.ExitPopup(
                title='Not enough disk space to run properly, '
                'please free at least 200 MB').open()

        elif free < 2 * 10 ** 8:
            Message(
                text='Your system has less then 200M of available space, you '
                'may run into issues'
            ).show()
        Logger.debug('free disk space: {}'.format(free))

    def activate_tuio(self, *args):
        self.send_tuio_touch = self.send_tuio_obj = True

    def manage_keyboard(self, window, keycode, scancode, text, modifiers):
        if keycode == 27:
            if self.mode == 'main':
                self.exit()
            else:
                self.mode = 'main'
            return True

    def parse_ports(self, *args):
        Logger.debug('parsing ports')
        try:
            self._send_tuio_port = list(
                self.parse_port(self.send_tuio_port))
        except ValueError as e:
            Logger.debug(str(e))
            self.send_tuio_port = '3337-3340'
            self.parse_ports()

    @staticmethod
    def parse_port(port):
        for p in port.split(','):
            if '-' in p:
                b, e = [int(x) for x in p.split('-')]
                for i in range(b, e + 1):
                    yield i
            else:
                yield int(p)

    def update_time(self, dt):
        try:
            self.time += dt
        except ReferenceError:
            # a weakref error can happen when a TangibleObject Disapear,
            # no easy solution…
            pass

    def on_profile(self, *args):
        if self.profile:
            self.load_zones()
            self.load_objects()

    def save_zones(self, profile=None):
        if not profile:
            profile = self.profile

        profile = u'profile-%s' % profile

        if not self.config.has_section(profile):
            self.config.add_section(profile)
        zones = self.root.ids.zone.zones
        self.config.set(profile, 'zones',
                        json.dumps([z.to_list() for z in zones]))

    def load_zones(self):
        zone = self.root.ids.zone
        for z in zone.zones[:]:
            zone.remove_widget(z)
            zone.zones.remove(z)

        profile = u'profile-%s' % self.profile

        if not self.config.has_section(profile):
            return

        zc = self.config.get(profile, 'zones')
        zones = json.loads(zc)
        for z in zones:
            nz = ZoneDefinition.from_list(z)
            zone.add_widget(nz)
            zone.zones.append(nz)

    def save_objects(self, profile=None):
        if not profile:
            profile = self.profile

        profile = u'profile-%s' % profile

        if not self.config.has_section(profile):
            self.config.add_section(profile)

        self.config.set(profile, 'objects',
                        json.dumps(self.root.ids.zone.coordinates))

    def load_objects(self):
        profile = u'profile-%s' % self.profile
        if not self.config.has_section(profile):
            objects = []
        else:
            objects = json.loads(self.config.get(profile, 'objects')) or []
        try:
            self.root.ids.zone.coordinates = objects
        except ReferenceError:
            pass
        self.root.ids.zone.undetect()

    def save_dialog(self):
        SaveDialog(target=self.profile).open()

    def load_dialog(self):
        LoadDialog(target=self.profile).open()

    def exit(self):
        if self.confirm_exit:
            if not any(isinstance(x, ExitDialog) for x in Window.children):
                ExitDialog().open()
        else:
            stopTouchApp()

    def on_stop(self):
        if self.expired:
            return
        self.root.ids.zone.undetect()
        self.root.ids.zone.flush_tuio(0)
        self.root.ids.zone.flush_tuio(0)
        self.config.set('general', 'profile', self.profile)
        if self.auto_save:
            self.save_objects()
            self.save_zones()
        self.config.write()

    def resize_window(self, value):
        if value == 'fullscreen':
            Window.size = Window.system_size
        else:
            Window.size = [int(x) for x in value.split(',')]
            Window.pos = (0, 0)

    def toggle_fullscreen(self, value):
        if value:
            Window.fullscreen = 'fake'
        else:
            Window.fullscreen = False

    def select_port(self, *args):
        Factory.PortSelection().open()

    def visual_log(self, message):
        if self.show_visual_log:
            self.log.append(message)
            self.log = self.log[-40:]

    def on_mode(self, *args):
        Clock.unschedule(self.update_time)
        # breadcrumbs.record(data={'mode': self.mode}, category='workflow')
        if self.mode == 'main':
            Clock.schedule_interval(self.update_time, 0)
            if self.training_current:
                self.warn('training cancelled')
                self.training_current = ''

        zone = self.root.ids.zone
        # zone.pos_hint = {'center_x': .5, 'center_y': .5}
        if self.mode in ('use', 'zones'):
            anim = Animation(scale=1, t='in_quad')
            if zone.center != zone.parent.center:
                a = zone.recenter_anim()
                anim = a & anim
            if self.hidden_use_mode:
                anim.bind(on_complete=self.hide_window)
        else:
            anim = Animation(scale=0, t='out_elastic')
            if self.hidden_use_mode:
                self.show_window()
        anim.start(zone)

    def toggle_borders(self, n):
        Window.borderless = n % 2
        Logger.debug('toggle borders')
        if n:
            Clock.schedule_once(lambda *x: self.toggle_borders(n - 1), .01)

    def hide_window(self, *args):
        Logger.debug('hide window')
        if self.mode != 'use':
            return

        if not self.borderless_toggled:
            self.borderless_toggled = True
            self.toggle_borders(5)

        Animation.stop_all(self, 'opacity')
        Animation(opacity=0).start(self)

    def show_window(self, *args):
        Logger.debug('show window')
        Animation.stop_all(self, 'opacity')
        a = Animation(opacity=1)
        a.bind(on_complete=lambda *x:
               Window.setter('borderless')(Window, True))
        a.start(self)

    def on_display_touches(self, *args):
        Logger.debug('display touches: {}'.format(self.display_touches))
        zone = self.root.ids.zone
        if not self.display_touches:
            for tid, p in list(zone.touches_points.items()):
                zone.touches_points.pop(tid)
                zone.remove_widget(p)
        else:
            for tid in zone.touches:
                if tid not in zone.touches_points:
                    zone.add_point(tid, zone.touches[tid])

    def get_credits(self):
        with open(resource_find('data/credits.txt')) as f:
            return f.read().format(
                version=__version__,
                year=strftime('%Y')
            )

    def on_pause(self, *args):
        return True

    def on_lang(self, instance, lang):
            tr.switch_lang(lang)


class Message(Label):
    display_time = NumericProperty(3)
    callback = ObjectProperty()

    def on_show_complete(self, *args):
        self.hide()

    def show(self):
        self.opacity = 0
        app.root.ids.messages.add_widget(self)
        a = (
            Animation(opacity=1, t='in_quad', d=.3) +
            Animation(d=self.display_time)
        )
        a.bind(on_complete=self.on_show_complete)
        a.start(self)
        if self.callback:
            self.callback()

    def hide(self, *args):
        a = Animation(opacity=0, scale=0, t='out_quad', d=1)
        a.bind(on_complete=lambda *x:
               app.root.ids.messages.remove_widget(self))
        a.start(self)


class Question(Message):
    '''
    usage:
        {
        '1:title': 'value',
        '2:title': 'value',
        }
        '''
    choices = DictProperty([])

    def on_show_complete(self, *args):
        pass

    def show(self):
        for item, callback in sorted(self.choices.items()):
            txt = item.split(':', 1)[1]
            q = Factory.QuestionButton(text=txt, on_release=self.hide)
            if callback:
                q.bind(on_release=callback)
            self.ids.choices.add_widget(q)

        super(Question, self).show()


Window.set_vkeyboard_class(OVKeyboard)

# XXX simplest, dirtiest solution, for kivy settings to ignore mouse too
# a better solution could be to contribute to kivy a way to cleanly set
# the popup class for settings, and make all settingitems use it

import widgets.settings_patch  # noqa

app = Application()
ROOT = load_kv()
