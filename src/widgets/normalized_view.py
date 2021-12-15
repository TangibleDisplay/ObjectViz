from kivy.uix.widget import Widget
from kivy.properties import ListProperty
from utils import load_kv


class NormalizedView(Widget):
    samples = ListProperty()
    r = ListProperty()
    g = ListProperty()
    b = ListProperty()

    def on_samples(self, instance, value):
        if not value:
            return

        r, g, b = [[] for i in range(3)]
        for points in value:
            for point in points:
                if point[0] > 25:
                    b += point
                elif point[0] < -25:
                    g += point
                else:
                    r += point

        self.r, self.g, self.b = r, g, b

load_kv()
