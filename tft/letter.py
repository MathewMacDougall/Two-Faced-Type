from geometry import *


class Letter:
    def __init__(self, segs, plane):
        self.segs_ = []
        for seg in segs:
            if plane == Plane.XZ:
                # Flip x so it looks right in the plot
                self.segs_.append(
                    Segment(Point(-seg.start().x(), 0, seg.start().y()), Point(-seg.end().x(), 0, seg.end().y())))
            else:
                self.segs_.append(
                    Segment(Point(0, seg.start().x(), seg.start().y()), Point(0, seg.end().x(), seg.end().y())))

    def segs(self):
        return self.segs_


# Try fit letters in 10x10 box
LINES_A = polylines(
    Point(0, 0),
    Point(5, 10),
    Point(10, 0)
)

LINES_L = polylines(
    Point(0, 10),
    Point(0, 0),
    Point(5, 0)
)

LINES_O = polylines(
    Point(0, 0),
    Point(10, 0),
    Point(10, 10),
    Point(0, 10),
)

LINES_C = polylines(
    Point(7, 10),
    Point(0, 10),
    Point(0, 0),
    Point(7, 0),
)
