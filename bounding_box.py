import math

class BoundingBox():
    def __init__(self, xmin, ymin, zmin, xmax, ymax, zmax):
        self._xmin = xmin
        self._ymin = ymin
        self._zmin = zmin
        self._xmax = xmax
        self._ymax = ymax
        self._zmax = zmax

        assert xmin <= xmax
        assert ymin <= ymax
        assert zmin <= zmax

    def z_length(self):
        return self._zmax - self._zmin

    def x_length(self):
        return self._xmax - self._xmin

    def y_length(self):
        return self._ymax - self._ymin

    def _xy_rectangles_overlap(self, other):
        assert isinstance(other, BoundingBox)

        if self._xmin >= other._xmax or other._xmin >= self._xmax:
            return False

        if self._ymin >= other._ymax or other._ymin >= self._ymax:
            return False

        return True

    def _xz_rectangles_overlap(self, other):
        assert isinstance(other, BoundingBox)

        if self._xmin >= other._xmax or other._xmin >= self._xmax:
            return False

        if self._zmin >= other._zmax or other._zmin >= self._zmax:
            return False

        return True

    def _yz_rectangles_overlap(self, other):
        assert isinstance(other, BoundingBox)

        if self._ymin >= other._ymax or other._ymin >= self._ymax:
            return False

        if self._zmin >= other._zmax or other._zmin >= self._zmax:
            return False

        return True

    def overlaps(self, other):
        # TODO: Add overlap threshold if needed
        return self._xy_rectangles_overlap(other) or self._xz_rectangles_overlap(other) or self._yz_rectangles_overlap(other)

    def dist(self, other):
        """
        cartesian dist between edges/faces of bboxes. Edges touching
        returns 0
        """
        assert isinstance(other, BoundingBox)

        max_z_dist = max(abs(self._zmax - other._zmin), abs(other._zmax - self._zmin))
        z_dist = max(max_z_dist - self.z_length() - other.z_length(), 0)

        max_y_dist = max(abs(self._ymax - other._ymin), abs(other._ymax - self._ymin))
        y_dist = max(max_y_dist - self.y_length() - other.y_length(), 0)

        max_x_dist = max(abs(self._xmax - other._xmin), abs(other._xmax - self._xmin))
        x_dist = max(max_x_dist - self.x_length() - other.x_length(), 0)

        return math.sqrt(x_dist ** 2 + y_dist ** 2 + z_dist ** 2)
