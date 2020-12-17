from OCC.Core import BRep
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopoDS import TopoDS_Solid
from OCCUtils import Topo
from OCCUtils.Common import project_point_on_plane, normal_vector_from_plane, intersect_shape_by_line, assert_isdone
import itertools
from OCCUtils.solid import Solid as OCCUtilsSolid
from collections import defaultdict
from OCC.Core.IntCurvesFace import IntCurvesFace_ShapeIntersector
from util import split_compound, point_in_solid
from OCCUtils.base import GlobalProperties
from constants import *
from solid import Solid
import math


class SolidFaceValidator():
    """
    Handles checking a solid still projects to / represents the desired faces
    """

    def __init__(self, compound):
        solids = split_compound(compound)
        self._compound = compound
        self._xz_intersections = self.get_intersections_for_face(solids, PL_XZ)
        self._yz_intersections = self.get_intersections_for_face(solids, PL_YZ)

    def is_valid(self):
        return all([len(l) != 0 for l in self._xz_intersections + self._yz_intersections])

    def is_removal_valid(self, solid):
        """
        Checks if the shape resulting from removing the given solid is valid. If it is, returns True
        and removes the solid from its internal representation. Otherwise returns false and the internal
        representation is unchanged
        :param solid:
        :return:
        """
        assert isinstance(solid, TopoDS_Solid)
        _solid = Solid(solid)
        affected_lists = [l for l in self._xz_intersections + self._yz_intersections if _solid in l]
        bad_lists = [l for l in affected_lists if len(l) == 1]
        if bad_lists:
            return False

        return True

    def remove(self, solid):
        _solid = Solid(solid)
        affected_lists = [l for l in self._xz_intersections + self._yz_intersections if _solid in l]
        for l in affected_lists:
            l.remove(_solid)


    @classmethod
    def get_intersections_for_face(self, solids, pln):
        # TODO: better comment. Doesn't explain where lines come from
        """
        :param solids: The list of solids making up the overall solid
        :param pln: The plane of the face
        :return: A list of lists, where the inner lists are lists of solids that each line intersects
        """
        pts = []
        for s in solids:
            props = GlobalProperties(OCCUtilsSolid(s))
            p = props.centre()
            if point_in_solid(OCCUtilsSolid(s), p):
                pts.append(p)
            else:
                raise NotImplementedError("Need to handle odd shapes")

            t = Topo(s)
            vertices = [v for v in t.vertices()]
            pnts = [BRep_Tool.Pnt(v) for v in vertices]
            pts += pnts

        normal_vec = normal_vector_from_plane(pln)
        normal_dir = gp_Dir(normal_vec)
        lines = [gp_Lin(p, normal_dir) for p in pts]

        # remove redundant lines
        groups = []
        for l in lines:
            for g in groups:
                if any([l.Distance(gl) < 0.0000000001 for gl in g]):
                    g.add(l)
                    break
            else:
                groups.append({l})

        lines = [g.pop() for g in groups]

        # Make sure lines are all perp to the plane
        import numpy as np
        line_dirs = [np.array([l.Direction().X(), l.Direction().Y(), l.Direction().Z()]) for l in lines]
        plane_normal = pln.Axis().Direction()
        plane_normal = np.array([plane_normal.X(), plane_normal.Y(), plane_normal.Z()])
        lines_normal = [np.linalg.norm(np.cross(ld, plane_normal)) < 1e-3 for ld in line_dirs]
        assert all(lines_normal)

        # We have to use lists here rather than sets or dicts, because the solids undergo very minor deviations
        # while operated on by OCC, so we can't get matching hashes
        result = []
        for line in lines:
            result.append([Solid(s) for s in solids if self.get_shape_line_intersections(s, line)])

        return result

    @classmethod
    def get_shape_line_intersections(cls, shape, line):
        """
        Seems to return the intersection for the first face the line runs into
        """
        shape_inter = IntCurvesFace_ShapeIntersector()
        shape_inter.Load(shape, 1e-3)
        shape_inter.PerformNearest(line, float("-inf"), float("+inf"))
        with assert_isdone(shape_inter, "failed to computer shape / line intersection"):
            intersections = [(shape_inter.Pnt(i), shape_inter.Face(i), line) for i in
                             range(1, shape_inter.NbPnt() + 1)]  # Indices start at 1 :(
            return intersections

