from kivy.uix.relativelayout import FloatLayout
from utils import load_kv


class LetterboxView(FloatLayout):
    def add_widget(self, widget, index=0):
        if 'container' in self.ids:
            self.ids.container.add_widget(widget, index)
        else:
            super(LetterboxView, self).add_widget(widget, index)

load_kv()
