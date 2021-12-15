from operator import mul
from libc.math cimport atan2
from libc.math cimport M_PI as pi

INF = float('inf')
NAN = float('nan')


def angle_diff(a1, a2):
    """Reports the angular difference between two angles"""

    d = abs(a1 - a2 % 360)
    if d > 180:
        # this happens when the angle goes from 360 to 0
        d = - (min(a1, a2) + 360 - max(a1, a2))
    return d if a1 < a2 else -d


def get_scale_factor(points):
    if not points:
        return 1, 1

    mw = max(p[0] for p in points)
    mh = max(p[1] for p in points)

    return mw, mh


def autoscale_points(points, scale, size, pos):
    mw, mh = scale
    width, height = size
    x, y = pos
    for p in points:
        yield x + p[0] * width / mw
        yield y + p[1] * height / mh


def standard_deviation(l):
    mean = sum(l) / len(l)
    mean_sq = sum(x ** 2 for x in l) / len(l)
    return (mean_sq - mean ** 2) ** .5


cpdef get_angle(points):
    """for a list of points [A, B, C], returns the angle in A.
    """
    cdef float A, B, C, D

    A = points[1][0] - points[0][0]
    B = points[1][1] - points[0][1]
    C = points[2][0] - points[1][0]
    D = points[2][1] - points[1][1]

    return -(180 / pi) * atan2(
        C * B - D * A,
        C * A + D * B
    )
