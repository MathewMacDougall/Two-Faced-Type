from OCCUtils.base import GlobalProperties
from OCCUtils.Common import project_point_on_plane, normal_vector_from_plane, intersect_shape_by_line, assert_isdone, point_in_solid
from OCCUtils.solid import Solid
from OCC.Core.IntCurvesFace import IntCurvesFace_ShapeIntersector
from util import split_compound
from OCCUtils.base import GlobalProperties
# import logging
# # logging.getLogger("OCCUtils").setLevel(logging.ERROR)
# # logging.getLogger("OCCUtils.Common").setLevel(logging.ERROR)
# # logging.getLogger("OCCUtils.solid").setLevel(logging.ERROR)
# # logging.getLogger("OCCUtils.base").setLevel(logging.ERROR)
# # logging.getLogger("GlobalProperties").setLevel(logging.ERROR)
# # logging.getLogger("Solid").setLevel(logging.ERROR)
# logging.getLogger("shapely").setLevel(logging.ERROR)
# logging.getLogger("shapely.geos").setLevel(logging.ERROR)
# logging.getLogger("shapely.geometry.base").setLevel(logging.ERROR)
# logging.getLogger("shapely.geometry").setLevel(logging.ERROR)
# logging.getLogger("shapely.speedups._speedups").setLevel(logging.ERROR)
# logging.getLogger("shapely.speedups").setLevel(logging.ERROR)
#
#
# loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
# logger_names = [name for name in logging.root.manager.loggerDict]
# try:
#     logger_names.remove("TFT")
# except ValueError:
#     pass
# for name in logger_names:
#     # print(name)
#     logging.getLogger(name).setLevel(logging.WARNING)
# print("LOGGERS:")
# print('\n'.join(logger_names))

from constants import *
import math

class SolidFaceValidator():
    """
    Handles checking a solid still projects to / represents the desired faces
    """

    def __init__(self, compound):
        self._compound = compound
        # self._xz_lines = self.iteratively_generate_lines_for_face(compound, PL_XZ, 100)
        # self._yz_lines = self.iteratively_generate_lines_for_face(compound, PL_YZ, 100)
        self._xz_lines = self.generate_lines_for_face(compound, PL_XZ)
        self._yz_lines = self.generate_lines_for_face(compound, PL_YZ)

    def is_valid(self, compound):
        # checks if all lines intersect the shape.
        xz_intersections = []
        for l in self._xz_lines:
            temp = self.get_shape_line_intersections(compound, l)
            xz_intersections.append(temp)
        xz_valid = len(xz_intersections) == len(self._xz_lines)

        yz_intersections = []
        for l in self._yz_lines:
            temp = self.get_shape_line_intersections(compound, l)
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
    def iteratively_generate_lines_for_face(cls, compound, pln, num_lines):
        props = GlobalProperties(compound)
        x1, y1, z1, x2, y2, z2 = props.bbox()
        x_step = (x2 - x1) / math.sqrt(num_lines)
        y_step = (y2 - y1) / math.sqrt(num_lines)
        z_step = (z2 - z1) / math.sqrt(num_lines)

        initial_pts = []
        if pln == PL_XZ:
            x = x1
            while x <= x2:
                z = z1
                while z < z2:
                    initial_pts.append(gp_Pnt(x, 0, z))
                    z += z_step
                x += x_step
        elif pln == PL_YZ:
            y = y1
            while y <= y2:
                z = z1
                while z < z2:
                    initial_pts.append(gp_Pnt(0, y, z))
                    z += z_step
                y += y_step
        else:
            raise RuntimeError()

        pts = initial_pts
        pts = cls._prune_pts(compound, pts, pln)
        for i in range(2):
            # TODO: decrease generate size over time
            pts = cls._generate_pts(pts, pln)
            pts = cls._prune_pts(compound, pts, pln)

        normal_vec = normal_vector_from_plane(pln)
        normal_dir = gp_Dir(normal_vec)
        lines = [gp_Lin(p, normal_dir) for p in pts]
        return lines

    @classmethod
    def _prune_pts(cls, compound, pts, pln):
        normal_vec = normal_vector_from_plane(pln)
        normal_dir = gp_Dir(normal_vec)
        pts_and_lines = [(p, gp_Lin(p, normal_dir)) for p in pts]

        pruned = list(filter(lambda x: len(cls.get_shape_line_intersections(compound, x[1])) > 0, pts_and_lines))
        return [p[0] for p in pruned]

    @classmethod
    def _generate_pts(cls, pts, pln, size=2, num=4):
        new_pts = []
        step = 2*size / math.sqrt(num)
        print("step: {}".format(step))
        for p in pts:
            x1 = p.X() - size
            x2 = p.X() + size
            y1 = p.Y() - size
            y2 = p.Y() + size
            z1 = p.Z() - size
            z2 = p.Z() + size
            if pln == PL_XZ:
                x = x1
                while x <= x2:
                    z = z1
                    while z <= z2:
                        new_pts.append(gp_Pnt(x, 0, z))
                        z += step
                    x += step
            elif pln == PL_YZ:
                y = y1
                while y <= y2:
                    z = z1
                    while z <= z2:
                        new_pts.append(gp_Pnt(0, y, z))
                        z += step
                    y += step
        return new_pts

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

