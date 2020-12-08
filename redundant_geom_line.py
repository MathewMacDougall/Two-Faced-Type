from OCC.Core.AIS import AIS_Shape
import pathlib
import copy
import logging

from OCC.Core.GeomAPI import GeomAPI_IntCS

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

logger = logging.getLogger("TFT")
logger.setLevel(logging.DEBUG)

def get_point_on_face(face):
    assert isinstance(face, TopoDS_Face) or isinstance(face, Face)

    gprop = BRepGProp_Face(face)
    foo_face = Face(face)
    u_min, u_max, v_min, v_max = foo_face.domain()
    # Get point slightly in from a corner. This is in case the face
    # is curved, we don't want to mistrea it as perp or not by measuring
    # the normal at the edge
    u_mid = u_min + (u_max - u_min) / 100.
    v_mid = v_min + (v_max - v_min) / 100.
    point = foo_face.parameter_to_point(u_mid, v_mid)
    return point

def get_point_on_all_faces(faces):
    assert isinstance(faces, list)
    return [get_point_on_face(f) for f in faces]

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

def get_line_face_intersection(line, face):
    assert isinstance(line, gp_Lin)

    geom_line = Geom_Line(line)

    surface = Face(face).surface
    uvw = GeomAPI_IntCS(geom_line, surface).Parameters(1)
    # TODO: you are here. Trying to figure out intersections
    print(uvw)
    return uvw


def remove_redundant_geometry_lines(compound, height_mm):
    all_faces = get_faces(compound)
    face1_nonperp_faces = get_nonperp_faces(all_faces, gp_Vec(0, 1, 0))
    lines = get_lines_through_all_faces(face1_nonperp_faces, PL_XZ)
    intersections = []
    for l in lines:
        from OCC.Core.IntCurvesFace import IntCurvesFace_ShapeIntersector
        shape_inter = IntCurvesFace_ShapeIntersector()
        shape_inter.Load(compound, 1e-3)
        shape_inter.PerformNearest(l, 0, 1000)

        with assert_isdone(shape_inter, "failed to computer shape / line intersection"):
            foo = shape_inter.Pnt(0)
            print("foo")
            # return (shape_inter.Pnt(1),
            #         shape_inter.Face(1),
            #         shape_inter.UParameter(1),
            #         shape_inter.VParameter(1),
            #         shape_inter.WParameter(1))
        # temp = intersect_shape_by_line(compound, l)
        intersections += temp

    print(len(intersections))

