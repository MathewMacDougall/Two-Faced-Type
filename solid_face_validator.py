from OCCUtils.Common import project_point_on_plane, normal_vector_from_plane, intersect_shape_by_line, assert_isdone
from OCCUtils.solid import Solid
from OCC.Core.IntCurvesFace import IntCurvesFace_ShapeIntersector
from util import split_compound, point_in_solid
from OCCUtils.base import GlobalProperties
from constants import *
import math

class SolidFaceValidator():
    """
    Handles checking a solid still projects to / represents the desired faces
    """

    def __init__(self, compound):
        self._compound = compound
        self._xz_lines = self.generate_lines_for_face(compound, PL_XZ)
        self._yz_lines = self.generate_lines_for_face(compound, PL_YZ)

    def is_valid(self, compound):
        # checks if all lines intersect the shape.
        xz_intersections = []
        for l in self._xz_lines:
            temp = self.get_shape_line_intersections(compound, l)
            if temp:
                xz_intersections.append(temp)
        xz_valid = len(xz_intersections) == len(self._xz_lines)

        yz_intersections = []
        for l in self._yz_lines:
            temp = self.get_shape_line_intersections(compound, l)
            if temp:
                yz_intersections.append(temp)
        yz_valid = len(yz_intersections) == len(self._yz_lines)

        return xz_valid and yz_valid

    @classmethod
    def generate_lines_for_face(self, compound, pln):
        solids = split_compound(compound)
        pts = []
        for s in solids:
            props = GlobalProperties(Solid(s))
            p = props.centre()
            if point_in_solid(Solid(s), p):
                pts.append(p)
            else:
                raise NotImplementedError("Need to handle odd shapes")

        normal_vec = normal_vector_from_plane(pln)
        normal_dir = gp_Dir(normal_vec)
        lines = [gp_Lin(p, normal_dir) for p in pts]
        return lines

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

