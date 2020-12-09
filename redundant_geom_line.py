from OCC.Core.AIS import AIS_Shape
import pathlib
import copy
import logging

from OCC.Core.GeomAPI import GeomAPI_IntCS

from OCCUtils.Common import minimum_distance
from OCCUtils.Construct import face_normal
from OCC.Core.gp import gp_Pnt
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.Core.TColgp import TColgp_Array2OfPnt
from OCC.Core.GeomAPI import GeomAPI_PointsToBSplineSurface
from OCC.Core.GeomAbs import GeomAbs_C2
from OCC.Core.ShapeAnalysis import ShapeAnalysis_Surface, shapeanalysis_GetFaceUVBounds
from util import add
from OCC.Core.BRep import BRep_Builder
from OCC.Core.GC import GC_MakeArcOfCircle, GC_MakeSegment
from OCC.Core.Geom import Geom_Plane, Geom_Line
from OCC.Core.ShapeAnalysis import ShapeAnalysis_Surface
from OCC.Core.ShapeExtend import ShapeExtend_Explorer
from enum import Enum
from OCC.Core.TopTools import TopTools_HSequenceOfShape
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCCUtils.Common import random_color
from OCC.Core.BRepGProp import BRepGProp_Face
from OCCUtils.base import GlobalProperties
from OCCUtils.face import Face
from OCCUtils.solid import Solid
from OCC.Core.BOPAlgo import BOPAlgo_Builder
from OCC.Core.TopoDS import TopoDS_Solid, TopoDS_Vertex
from OCC.Core.GProp import GProp_GProps
from OCC.Core import BRepGProp
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Display.SimpleGui import init_display
from OCC.Extend.ShapeFactory import make_extrusion, make_edge, make_face, make_vertex
from face_factory import FaceFactory
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse, BRepAlgoAPI_Check, BRepAlgoAPI_Section, BRepAlgoAPI_Splitter
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
from OCC.Core.gp import gp_Trsf, gp_Ax1, gp_Vec, gp_Pnt
from constants import *
from util import *
import math
from OCC.Core.StlAPI import StlAPI_Writer
import argparse
from pathlib import Path
import os
import errno
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Solid, TopoDS_Shape, TopoDS_Face
from OCCUtils.Common import project_point_on_plane, normal_vector_from_plane, intersect_shape_by_line, assert_isdone
# display, start_display, add_menu, add_function_to_menu = init_display()

logger = logging.getLogger("TFT")
logger.setLevel(logging.DEBUG)

def fix_shape(shape, tolerance=1e-3):
    from OCC.Core.ShapeFix import ShapeFix_Shape
    fix = ShapeFix_Shape(shape)
    fix.SetFixFreeShellMode(True)
    sf = fix.FixShellTool()
    sf.SetFixOrientationMode(True)
    fix.LimitTolerance(tolerance)
    fix.Perform()
    return copy.deepcopy(fix.Shape())

def get_point_on_face(face):
    assert isinstance(face, TopoDS_Face) or isinstance(face, Face)

    foo_face = Face(face)
    u_min, u_max, v_min, v_max = foo_face.domain()
    # Get point slightly in from a corner. This is in case the face
    # is curved, we don't want to mistrea it as perp or not by measuring
    # the normal at the edge
    u_mid = u_min + (u_max - u_min) / 100.
    v_mid = v_min + (v_max - v_min) / 100.
    point = foo_face.parameter_to_point(u_mid, v_mid)
    return point

def sample_pts_on_face(face, increment_percentage=0.49):
    """ Creates a list of gp_Pnt points from a bspline surface
    """
    umin, umax, vmin, vmax = shapeanalysis_GetFaceUVBounds(face)
    print(umin, umax, vmin, vmax)

    pnts = []
    sas = ShapeAnalysis_Surface(Face(face).surface)

    v_increment = (vmax - vmin) * increment_percentage
    u_increment = (umax - umin) * increment_percentage
    u = umin + 0.01
    while u < umax:
        v = vmin + 0.01
        while v < vmax:
            p = sas.Value(u, v)
            # print(minimum_distance(make_vertex(p), face)[0])
            # TODO: This is kind of a hack
            if minimum_distance(make_vertex(p), face)[0] < 1e-12:
                pnts.append(p)
            # print("u=", u, " v=", v, "->X=", p.X(), " Y=", p.Y(), " Z=", p.Z())
            v += v_increment
        u += u_increment
    return pnts

def get_point_on_all_faces(faces):
    result = []
    for f in faces:
        result += sample_pts_on_face(f)
    return result
    # assert isinstance(faces, list)
    # return [get_point_on_face(f) for f in faces]

def get_point_on_all_faces_with_plane(faces, plane, vec):
    plane_ = plane
    if isinstance(plane, gp_Pln):
        plane_ = Geom_Plane(plane_)

    points = get_point_on_all_faces(faces)
    proj_points = [add(project_point_on_plane(plane_, p), vec) for p in points]
    return proj_points

def get_lines_through_all_faces(faces, plane):
    points = get_point_on_all_faces_with_plane(faces, plane, gp_Vec(0, 0, 0))
    normal_vec = normal_vector_from_plane(plane)
    normal_dir = gp_Dir(normal_vec)
    lines = [gp_Lin(p, normal_dir) for p in points]
    return lines

def get_shape_line_intersections(shape, line):
    """
    Seems to return the intersection for the first face the line runs into
    """
    from OCC.Core.IntCurvesFace import IntCurvesFace_ShapeIntersector
    shape_inter = IntCurvesFace_ShapeIntersector()
    shape_inter.Load(shape, 1e-3)
    shape_inter.PerformNearest(line, float("-inf"), float("+inf")) # TODO: replace with +- inf

    with assert_isdone(shape_inter, "failed to computer shape / line intersection"):
        intersections = [(shape_inter.Pnt(i), shape_inter.Face(i), line) for i in range(1, shape_inter.NbPnt() + 1)] # Indices start at 1 :(
        return intersections

def get_line_face_intersection(line, face):
    assert isinstance(line, gp_Lin)

    geom_line = Geom_Line(line)

    surface = Face(face).surface
    uvw = GeomAPI_IntCS(geom_line, surface)
    u = 0
    v = 0
    w = 0
    # uvw.Parameters(0, u, v, w)
    u, v, w = uvw.Parameters(1)
    # TODO: you are here. Trying to figure out intersections
    print("u: {}    v: {}     w: {}".format(u, v, w))
    return u, v, w


def shape_valid(shape, lines):
    # checks if all lines intersect the shape.
    intersections = []
    for l in lines:
        temp = get_shape_line_intersections(shape, l)
        intersections.append(temp)
    num_non_intersections = len([i for i in intersections if not i])
    # num_non_intersections = len(lines) - len(intersections)
    print("{} intersections, {} nonintersections".format(len(intersections), num_non_intersections))

    return num_non_intersections <= 0, intersections, num_non_intersections

def remove_redundant_geometry_lines(compound, height_mm, display):
    compound = fix_shape(compound)
    all_faces = get_faces(compound)
    face1_nonperp_faces = get_nonperp_faces(all_faces, gp_Vec(0, 1, 0))
    # for f in face1_nonperp_faces:
    #     display.DisplayShape(f)
    lines = get_lines_through_all_faces(face1_nonperp_faces, PL_XZ)
    # assert len(lines) == len(face1_nonperp_faces)
    baz = shape_valid(compound, lines)[1]
    # TODO: why is there sometimes more intersections?
    # testval = len(baz) >= len(lines)
    assert len(baz) >= len(lines)
    # testval = shape_valid(compound, lines)
    print("{} lines".format(len(lines)))

    display.DisplayShape([make_edge(l) for l in lines])
    # display.DisplayShape(compound, color="WHITE", transparency=0.8)
    # return None

    result = copy.deepcopy(compound)
    for index, f in enumerate(get_perp_faces(all_faces, gp_Vec(0, 1, 0))):
        if index != 16:
            continue
        #
        display.DisplayShape(f, color="BLUE", transparency=0.7)
        normal_vec = gp_Vec(face_normal(Face(f)))
        # Face(f)>
        # gprop = BRepGProp_Face(f)
        # normal_point = gp_Pnt(0, 0, 0)
        # normal_vec = gp_Vec(0, 0, 0)
        # # TODO: how to get middle of face with UV mapping?
        # gprop.Normal(0, 0, normal_point, normal_vec)
        # normal_vec_reversed = normal_vec.Reversed()  # point into solid
        normal_vec_reversed = normal_vec  # point into solid
        normal_extrusion = make_extrusion(f, height_mm, normal_vec_reversed)
        display.DisplayShape(normal_extrusion, transparency=0.8)

        temp_cut_compound = BRepAlgoAPI_Cut(copy.deepcopy(result), normal_extrusion).Shape()
        display.DisplayShape(temp_cut_compound, color="WHITE", transparency=0.8)
        valid, intersections, num_non_intersections = shape_valid(temp_cut_compound, lines)
        # for inter in intersections:
            # display.DisplayShape(inter[1], color="GREEN", transparency=0.8)
            # display.DisplayShape(make_edge(inter[2]), color="GREEN", transparency=0.0)
        if valid:
            print("{}: removed face".format(index))
            result = copy.deepcopy(temp_cut_compound)
        else:
            print("{}: did NOT remove face".format(index))

        # sometimes the normal isn't always where I expect??? Just try both I guess
        # normal_vec_reversed = normal_vec_reversed.Reversed()
        # normal_extrusion = make_extrusion(f, height_mm, normal_vec_reversed)
        # temp_cut_compound = BRepAlgoAPI_Cut(copy.deepcopy(result), normal_extrusion).Shape()
        # # display.DisplayShape(temp_cut_compound, color="WHITE", transparency=0.8)
        # valid, intersections, num_non_intersections = shape_valid(temp_cut_compound, lines)
        # # for inter in intersections:
        # # display.DisplayShape(inter[1], color="GREEN", transparency=0.8)
        # # display.DisplayShape(make_edge(inter[2]), color="GREEN", transparency=0.0)
        # if valid:
        #     print("{}: removed face".format(index))
        #     result = copy.deepcopy(temp_cut_compound)
        # else:
        #     print("{}: did NOT remove face".format(index))
    return result


