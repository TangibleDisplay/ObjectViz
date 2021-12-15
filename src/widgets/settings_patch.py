from kivy.properties import StringProperty, ListProperty, ObjectProperty
from kivy.factory import Factory as F
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.uix.recycleview import RecycleView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.resources import resource_find
import kivy.uix.settings  # noqa
kivy.uix.settings.Popup = F.OVPopup
kivy.uix.settings.TextInput = F.OVTextInput

from utils import load_kv

from glob import glob
from os.path import splitext, basename


class Tr(object):
    tr_title = StringProperty()
    tr_desc = StringProperty()


class TrSettingString(Tr, F.SettingString):
    pass


class TrSettingBoolean(Tr, F.SettingBoolean):
    pass


class TrSettingNumeric(Tr, F.SettingNumeric):
    pass


class TrSettingOptions(Tr, F.SettingOptions):
    def _create_popup(self, instance):
        # create th e popup
        popup = F.TrOptionsPopup(
            title=self.title,
            options=self.options,
            manager=self,
        )

        popup.height = len(self.options) * dp(55) + dp(150)

        # add all the options
        popup.open()


class TrLangs(TrSettingOptions):
    @property
    def options(self):
        dirname = resource_find('data/po')
        return [splitext(basename(x))[0] for x in glob('{}/*.mo'.format(dirname))]


class TrOptionsPopup(F.OVPopup):
    options = ListProperty()
    manager = ObjectProperty()


class TrOptionsChoice(ToggleButtonBehavior, Label):
    manager = ObjectProperty()
    popup = ObjectProperty()


class TrSettingTitle(Tr, F.SettingTitle):
    pass


class TrSettingPath(Tr, F.SettingPath):
    pass


load_kv()
