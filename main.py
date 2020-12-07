from OCC.Core.AIS import AIS_Shape
import pathlib
import copy
import logging
from OCC.Core.BRep import BRep_Builder
from OCC.Core.GC import GC_MakeArcOfCircle, GC_MakeSegment
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
import math
from OCC.Core.StlAPI import StlAPI_Writer
import argparse
from pathlib import Path
import os
import errno
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Solid, TopoDS_Shape, TopoDS_Face

logger = logging.getLogger("TFT")
logger.setLevel(logging.DEBUG)

display, start_display, add_menu, add_function_to_menu = init_display()

def combine_faces(face1, face2, height_mm):
    assert isinstance(face1, TopoDS_Face)
    assert isinstance(face2, TopoDS_Face)

    face1_ = copy.deepcopy(face1)
    face2_ = copy.deepcopy(face2)

    # assuming both faces start in the XZ plane
    tf = gp_Trsf()
    # rotate from the XZ plane to the YZ plane
    tf.SetRotation(gp_Ax1(ORIGIN, DIR_Z), math.pi / 2)
    face2_ = BRepBuilderAPI_Transform(face2_, tf).Shape()

    # We assume characters are no wider than they are tall, but just in case
    # we extrude by twice the height to make sure to capture all features
    face1_extruded = make_extrusion(face1_, 2 * height_mm, gp_Vec(0, 1, 0))
    face2_extruded = make_extrusion(face2_, 2 * height_mm, gp_Vec(1, 0, 0))
    common = BRepAlgoAPI_Common(face1_extruded, face2_extruded)

    result = common.Shape()
    assert isinstance(result, TopoDS_Compound)
    return copy.deepcopy(result)

def combine_words(word1, word2, face_factory, height_mm):
    assert isinstance(word1, str)
    assert isinstance(word2, str)
    assert len(word1) == len(word2)

    combined_faces = []
    faces1 = []
    faces2 = []
    for letter1, letter2 in zip(word1, word2):
        face1 = face_factory.create_char(letter1, height_mm)
        face2 = face_factory.create_char(letter2, height_mm)
        faces1.append(face1)
        faces2.append(face2)
        combined_letter = combine_faces(face1, face2, height_mm)
        combined_faces.append(combined_letter)

    return combined_faces, faces1, faces2

def offset_shapes(shapes, height_mm):
    # Offset letters so they can be previewed properly from 2 directions
    tf = gp_Trsf()
    p1 = ORIGIN
    offset = 0
    offset_increment = 1.1*height_mm
    offset_letters = []
    for shape in shapes:
        tf.SetTranslation(p1, gp_Pnt(offset, offset, 0))
        offset_letter = BRepBuilderAPI_Transform(shape, tf).Shape()
        assert isinstance(offset_letter, TopoDS_Compound)
        offset_letters.append(offset_letter)
        offset += offset_increment

    return offset_letters

def save_to_stl(shapes, dirpath=Path.home()):
    assert isinstance(shapes, list)

    try:
        os.makedirs(Path(dirpath))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    stl_writer = StlAPI_Writer()
    stl_writer.SetASCIIMode(True)
    for index, shape in enumerate(shapes):
        filepath = Path(dirpath, "combined_shape_" + str(index + 1) + ".stl")
        stl_writer.Write(shape, str(filepath))

# TODO: should creating a disjointed / non-contiguous
# solid make a cutting extrusion invalid?
def remove_redundant_geometry(shapes, height_mm):
    # Do nothing right now. Still testing algos :(
    return shapes

# Also, useful site to make svg letters: https://maketext.io/
# My blessed documentation: https://old.opencascade.com/doc/occt-6.9.0/refman/html/class_geom2d___b_spline_curve.html#a521ec5263443aca0d5ec43cd3ed32ac6
def main(word1, word2, height_mm, output_dir):
    display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
    display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
    display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")

    face_images_dir = pathlib.Path(__file__).parent / "face_images/aldrich"
    face_factory = FaceFactory(face_images_dir)

    letters, faces1, faces2 = combine_words(word1, word2, face_factory, height_mm)
    letters = remove_redundant_geometry(letters, height_mm)
    letters = offset_shapes(letters, height_mm)

    for letter in letters:
        if letter:
            display.DisplayShape(letter)

    save_to_stl(letters, output_dir)

    start_display()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Combine words into Two-Faced Type, and output as STLs")
    parser.add_argument('words', metavar='word', type=str, nargs=2, help='the words to combine')
    parser.add_argument('-o', '--output_dir', metavar='output_directory', type=str,
                        help="The directory to write STL files to. Will be created if it doesn't exist", required=True)
    parser.add_argument('--height', metavar='height_mm', type=float, help="The height of the characters, in mm",
                        required=True)
    args = parser.parse_args()

    main(args.words[0], args.words[1], args.height, args.output_dir)

