from kivy.uix.stencilview import StencilView
from kivy.properties import ListProperty
from utils import load_kv


class ResultSparseGraph(StencilView):
    successes = ListProperty()
    failures = ListProperty()
    errors = ListProperty()
    success_points = ListProperty()
    failure_points = ListProperty()
    error_points = ListProperty()
    scale_factors = ListProperty()

    graduation_vertices = ListProperty()
    graduation_indices = ListProperty()


load_kv()
