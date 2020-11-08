import numpy as np
from enum import Enum


class Point():
    def __init__(self, x, y, z=0):
        self.coords_ = [x, y, z]

    def fromArray(self, coords):
        if (len(coords) == 2):
            return Point(coords[0], coords[1])
        elif (len(coords) == 3):
            return Point(coords[0], coords[1], coords[2])
        else:
            raise RuntimeError("array should be len 2 or 3")

    def x(self):
        return self.coords_[0]

    def y(self):
        return self.coords_[1]

    def z(self):
        return self.coords_[2]

    def coords(self):
        return self.coords_

    def __add__(self, other):
        return Point.fromArray(self.coords() + other.coords())

    def __sub__(self, other):
        return Point.fromArray(other.coords() - self.coords())

    def __repr__(self):
        return "Point({}, {}, {})".format(self.x(), self.y(), self.z())


class Segment():
    def __init__(self, start, end):
        self.start_ = start
        self.end_ = end

    def start(self):
        return self.start_

    def end(self):
        return self.end_

    def at(self, t):
        """
        :param t: in [0, 1]
        :return: Point along segment
        """
        return self.start() + np.array((self.end() - self.start())) * t


class Plane(Enum):
    XZ = 1
    YZ = 2


def polylines(*args):
    return [Segment(p1, p2) for p1, p2 in zip(args, args[1:])]
