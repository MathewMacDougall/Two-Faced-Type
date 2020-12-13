from OCC.Core.TopoDS import TopoDS_Solid
from OCCUtils.Common import GpropsFromShape
from OCCUtils.base import GlobalProperties
from bounding_box import BoundingBox
from util import distance


class Solid():
    """
    Quick wrapper for TopoDS_Solid so we can have hashing and equality that doesn't
    depend on memory locations
    """

    def __init__(self, solid):
        assert isinstance(solid, TopoDS_Solid)

        self._solid = solid

        props = GlobalProperties(solid)
        x1, y1, z1, x2, y2, z2 = props.bbox()
        xmin = min(x1, x2)
        xmax = max(x1, x2)
        ymin = min(y1, y2)
        ymax = max(y1, y2)
        zmin = min(z1, z2)
        zmax = max(z1, z2)
        self._bbox = BoundingBox(xmin, ymin, zmin, xmax, ymax, zmax)

    def bbox(self):
        return self._bbox

    def solid(self):
        return self._solid

    def __hash__(self):
        # TODO: remove this function? Or force to not be used?
        return self._bbox.__hash__()

    def __eq__(self, other):
        self_com = GpropsFromShape(self._solid).volume().CentreOfMass()
        other_com = GpropsFromShape(other._solid).volume().CentreOfMass()
        # Not ideal for equality, but we need to handle minor deviations
        # TODO: does this tolerance really need to be so big?
        return self._bbox.eq_within_tolerance(other._bbox, tolerance=0.1) and distance(self_com, other_com) < 0.1

    def __ne__(self, other):
        return not self.__eq__(other)
