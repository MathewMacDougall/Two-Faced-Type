from OCC.Core.TopoDS import TopoDS_Solid
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCCUtils.Common import GpropsFromShape
from OCCUtils.base import GlobalProperties
from bounding_box import BoundingBox
from util import distance, is_faces_overlap
from OCCUtils.Common import minimum_distance


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

def is_bbox_touching(solid1, solid2):
    assert isinstance(solid1, Solid)
    assert isinstance(solid2, Solid)
    return solid1.bbox().dist(solid2.bbox()) < 1e-3


def get_solids_with_touching_bbox(solids, solid):
    assert isinstance(solids, list)
    assert isinstance(solid, Solid)

    result = []
    for s in solids:
        if s != solid and is_bbox_touching(s, solid):
            result.append(s)

    return result

def is_solids_adjacent(solid1, solid2):
    assert isinstance(solid1, TopoDS_Solid)
    assert isinstance(solid2, TopoDS_Solid)

    s1 = Solid(solid1)
    s2 = Solid(solid2)

    if not is_bbox_touching(s1, s2):
        return False

    faces1 = [f for f in TopologyExplorer(solid1).faces()]
    faces2 = [f for f in TopologyExplorer(solid2).faces()]

    for f1 in faces1:
        for f2 in faces2:
            overlap = is_faces_overlap(f1, f2)
            close = minimum_distance(f1, f2)[0] < 1
            if overlap and close:
                return True

    return False

