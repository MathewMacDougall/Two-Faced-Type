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
from OCC.Core.TopoDS import TopoDS_Solid
from OCC.Core.GProp import GProp_GProps
from OCC.Core import BRepGProp
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Display.SimpleGui import init_display
from OCC.Extend.ShapeFactory import make_extrusion, make_edge, make_face
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

class CompoundSequenceType(Enum):
    FACE = 0
    SOLID = 1

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


def make_bounding_box(compound):
    assert isinstance(compound, TopoDS_Compound)

    compound_ = copy.deepcopy(compound)
    props = GlobalProperties(compound_)
    x1, y1, z1, x2, y2, z2 = props.bbox()
    fudge_factor = 0.001
    p = gp_Pnt(x1-fudge_factor, y1-fudge_factor, z1-fudge_factor)
    p2 = gp_Pnt(x2+fudge_factor, y2+fudge_factor, z2+fudge_factor)
    result = BRepPrimAPI_MakeBox(p, p2).Shape()
    assert isinstance(result, TopoDS_Solid)
    return copy.deepcopy(result)

def dot(v1, v2):
    assert isinstance(v1, gp_Vec)
    assert isinstance(v2, gp_Vec)
    result =  v1.X() * v2.X() + v1.Y() * v2.Y() + v1.Z() * v2.Z()
    assert isinstance(result, float)
    return result

def get_nonperp_faces(faces, vec, disp=False):
    assert isinstance(vec, gp_Vec)
    assert isinstance(faces, list)

    nonperp_faces = []
    for face in faces:
        assert isinstance(face, TopoDS_Face)
        gprop = BRepGProp_Face(face)
        normal_point = gp_Pnt(0, 0, 0)
        normal_vec = gp_Vec(0, 0, 0)
        foo_face = Face(face)
        # get uv coord of middle
        u_min, u_max, v_min, v_max = foo_face.domain()
        # u_mid = (u_min + u_max) / 2.
        # v_mid = (v_min + v_max) / 2.
        u_mid = u_min + (u_max - u_min) / 100.
        v_mid = v_min + (v_max - v_min) / 100.
        # print("{}, {}, {}, {}, {}, {}".format(u_min, u_mid, u_max, v_min, v_mid, v_max))

        # sas = ShapeAnalysis_Surface(foo_face.surface)
        # uv = sas.ValueOfUV(gp_pnt_middle, 1.)
        # uv_middle = uv.Coord()
        # print(uv_middle.X())
        # TODO: how to get middle of face with UV mapping?
        # UV coord has to be on face to work
        gprop.Normal(u_mid, v_mid, normal_point, normal_vec)
        # gprop.Normal(0, 0, normal_point, normal_vec)
        # print("normal pt: {}".format(normal_point))
        # print("normal vec: {}".format(normal_vec))

        # if disp:
        #     c = random_color()
        #     display.DisplayShape(face, color=c, transparency=0.8)
        #     display.DisplayShape(normal_point, color=c)
        # display.DisplayShape(normal_point, color="BLACK")
        if abs(dot(vec, normal_vec)) != 0:
            # print("good")
            nonperp_faces.append(face)
            # if disp or True:
            #     # print("drawing")
            #     c = random_color()
            #     display.DisplayShape(face, color=c, transparency=0.6)
            #     display.DisplayShape(normal_point, color=c)
        else:
            pass
            # print("DOT PRODUCT VALUE: {}".format(abs(dot(vec, normal_vec))))
    return copy.deepcopy(nonperp_faces)

def extrude_and_clamp(faces, vec, clamp, height_mm):
    assert isinstance(clamp, TopoDS_Solid)

    faces_ = copy.deepcopy(faces)
    vec_ = copy.deepcopy(vec)
    clamp_ = copy.deepcopy(clamp)

    extrusions = []
    for face in faces_:
        assert isinstance(face, TopoDS_Face)
        ext = make_extrusion(face, 2 * height_mm, vec_)
        extrusions.append(ext)

    clamped_extrusions = []
    for e in extrusions:
        ee = BRepAlgoAPI_Common(clamp_, e).Shape()
        clamped_extrusions.append(copy.deepcopy(ee))

    # aRes = TopoDS_Compound()
    # aBuilder = BRep_Builder()
    # aBuilder.MakeCompound(aRes)
    # for e in clamped_extrusions:
    #     aBuilder.Add(aRes, e)
    # print("res ", aRes)

    result = copy.deepcopy(clamped_extrusions[0])
    failed_fuses = []
    for s in clamped_extrusions[1:]:
        test_result = BRepAlgoAPI_Fuse(copy.deepcopy(result), copy.deepcopy(s)).Shape()
        if test_result is None:
            failed_fuses.append(copy.deepcopy(s))
        else:
            result = copy.deepcopy(test_result)
    # display.DisplayShape(result, transparency=0.8)
    fixed_result = copy.deepcopy(result)
    double_failed_fuses = []
    if failed_fuses:
        logger.warning("Failed fuses: {}".format(len(failed_fuses)))
        # print("{} failed fuses".format(len(failed_fuses)))
    for fs in failed_fuses:
        tf = gp_Trsf()
        tf.SetTranslation(gp_Vec(0, 0, 0.001))
        # tf.SetScaleFactor(1.0 + 1e-12)
        fs = BRepBuilderAPI_Transform(copy.deepcopy(fs), tf).Shape()
        tt1 = BRepAlgoAPI_Fuse(copy.deepcopy(fixed_result), copy.deepcopy(fs))
        tt1.SetFuzzyValue(1.0)
        tt1.SetCheckInverted(False)
        tt1.SetNonDestructive(False)
        if tt1.Shape() is not None:
            fixed_result = copy.deepcopy(tt1.Shape())
        else:
            tf = gp_Trsf()
            tf.SetTranslation(gp_Vec(0, 0, -0.001))
            # tf.SetScaleFactor(1.0 + 1e-12)
            fs2 = BRepBuilderAPI_Transform(copy.deepcopy(fs), tf).Shape()
            tt2 = BRepAlgoAPI_Fuse(copy.deepcopy(fixed_result), copy.deepcopy(fs2))
            tt2.SetFuzzyValue(1.0)
            tt2.SetCheckInverted(False)
            tt2.SetNonDestructive(False)
            if tt2.Shape() is not None:
                fixed_result = copy.deepcopy(tt2.Shape())
            else:
                double_failed_fuses.append(copy.deepcopy(fs))

    if failed_fuses:
        logger.warning("Recovered fuses: {}".format(len(failed_fuses)-len(double_failed_fuses)))
        logger.warning("Doubly-failed fuses: {}".format(len(double_failed_fuses)))
        # print("{} recovered fuses".format(len(failed_fuses)-len(double_failed_fuses)))
        # print("{} double failed fuses".format(len(double_failed_fuses)))
    # display.DisplayShape(fixed_result, color="BLUE", transparency=0.8)
    if double_failed_fuses:
        # display.DisplayShape(result, transparency=0.8)
        for f in double_failed_fuses:
            display.DisplayShape(f, color="RED")
        start_display()
        exit(0)

    return copy.deepcopy(fixed_result)


def project_and_clamp(compound, vec, containing_box, height_mm, disp=False):
    assert isinstance(compound, TopoDS_Compound)
    assert isinstance(containing_box, TopoDS_Solid)
    compound_ = copy.deepcopy(compound)
    containing_box_ = copy.deepcopy(containing_box)

    # if disp:
    #     display.DisplayShape(compound_)

    all_faces = get_list_from_compound(compound_, CompoundSequenceType.FACE)
    # if disp:
    #     for f in all_faces:
    #         display.DisplayShape(f)
    nonperp_faces = get_nonperp_faces(all_faces, vec, disp)
    # if disp:
    #     for f in nonperp_faces:
    #         display.DisplayShape(f, color=random_color(), transparency=0.8)
    if not nonperp_faces:
        raise RuntimeError("No nonperp faces. This probably shouldn't happen.")
    magic_compound = extrude_and_clamp(nonperp_faces, vec, containing_box_, height_mm)
    # display.DisplayShape(magic_compound)
    assert isinstance(magic_compound, TopoDS_Compound)
    return copy.deepcopy(magic_compound)


def get_list_from_compound(compound, sequence_type):
    assert isinstance(sequence_type, CompoundSequenceType)
    compound_ = copy.deepcopy(compound)

    se_exp = ShapeExtend_Explorer()
    shape_sequence = se_exp.SeqFromCompound(compound_, True)
    solids_sequence = TopTools_HSequenceOfShape()
    # Only the solids seem to be populated properly.
    # Need to use TopologyExplorer to get other features
    se_exp.DispatchList(shape_sequence,
                        TopTools_HSequenceOfShape(),
                        TopTools_HSequenceOfShape(),
                        TopTools_HSequenceOfShape(),
                        TopTools_HSequenceOfShape(),
                        TopTools_HSequenceOfShape(),
                        solids_sequence,
                        TopTools_HSequenceOfShape(),
                        TopTools_HSequenceOfShape())

    solids = [solids_sequence.Value(i) for i in range(1, solids_sequence.Length() + 1)]  # Indices start at 1 :(
    faces = [f for solid in solids for f in TopologyExplorer(solid).faces()]

    if sequence_type == CompoundSequenceType.FACE:
        return faces
    elif sequence_type == CompoundSequenceType.SOLID:
        return solids
    else:
        raise ValueError("Invalid sequence type")


def get_mass(compound):
    if not (isinstance(compound, TopoDS_Compound) or isinstance(compound, TopoDS_Solid)):
        raise RuntimeError("bad mass instance type")
    compound_ = copy.deepcopy(compound)

    if isinstance(compound, TopoDS_Compound):
        solids = get_list_from_compound(compound_, CompoundSequenceType.SOLID)
    else:
        solids = [compound_]


    total_mass = 0
    for solid in solids:
        props = GProp_GProps()
        BRepGProp.brepgprop_VolumeProperties(solid, props)
        mass = props.Mass()
        total_mass += mass
    return total_mass

def remove_redundant_geometry(shapes, height_mm):
    return [_remove_redundant_geometry_helper2(shape, height_mm) for shape in shapes]

def face_is_valid(temp_cut_compound_, vec_, bounding_box_, reference_solid, height_mm):
    # temp_all_faces = get_list_from_compound(temp_cut_compound_, CompoundSequenceType.FACE)
    # temp_nonperp_faces = get_nonperp_faces(temp_all_faces, vec_, False)
    #
    # reference_all_faces = get_list_from_compound(temp_cut_compound_, CompoundSequenceType.FACE)
    # reference_nonperp_faces = get_nonperp_faces(reference_all_faces, vec_, False)
    #
    # for tf in temp_nonperp_faces:
    #     display.DisplayShape(tf, color="BLUE", transparency=0.8)
    # for rf in reference_nonperp_faces:
    #     display.DisplayShape(rf, color="GREEN", transparency=0.0)
    # start_display()

    temp_projected_compound = project_and_clamp(temp_cut_compound_, vec_, bounding_box_, height_mm, disp=True)
    diff = BRepAlgoAPI_Cut(reference_solid, temp_projected_compound)
    diff.SetNonDestructive(False)
    diff.SetCheckInverted(False)
    diff.SetFuzzyValue(1.01)
    diffff = diff.Shape()
    if diffff is None:
        # display.DisplayShape(reference_solid, color="BLUE", transparency=0.8)
        display.DisplayShape(temp_projected_compound, color="RED", transparency=0.8)
        start_display()
    diff_mass = get_mass(diffff)
    return diff_mass < 0.1

def bounding_rect(compound, plane):
    assert isinstance(compound, TopoDS_Compound)
    assert isinstance(plane, gp_Pln)

    props = GlobalProperties(compound)
    x1, y1, z1, x2, y2, z2 = props.bbox()
    if plane == PL_XZ:
        return x1, z1, x2, z2
    elif plane == PL_YZ:
        return y1, z1, y2, z2
    else:
        raise RuntimeError("bad plane")

def _remove_redundant_geometry_helper2(compound, height_mm):
    assert isinstance(compound, TopoDS_Compound)

    compound_ = copy.deepcopy(compound)
    face1_vec = gp_Vec(0, 1, 0)
    face2_vec = gp_Vec(-1, 0, 0)

    all_compound_faces = get_list_from_compound(compound_, CompoundSequenceType.FACE)
    compound_nonperp_faces = get_nonperp_faces(all_compound_faces, face1_vec, False)

    for cf in compound_nonperp_faces:
        display.DisplayShape(cf, color="BLUE", transparency=0.8)

    for index, face in enumerate(get_list_from_compound(compound_, CompoundSequenceType.FACE)):
        if index != 0:
            continue

        display.DisplayShape(face)

        gprop = BRepGProp_Face(face)
        normal_point = gp_Pnt(0, 0, 0)
        normal_vec = gp_Vec(0, 0, 0)
        # TODO: how to get middle of face with UV mapping?
        gprop.Normal(0, 0, normal_point, normal_vec)
        normal_vec_reversed = normal_vec.Reversed() # point into solid
        normal_extrusion = copy.deepcopy(make_extrusion(face, height_mm, normal_vec_reversed))
        cutting_extrusion = copy.deepcopy(normal_extrusion)

        def _face_can_be_removed(reference_faces, test_faces, bounding_range, pln):
            # pseudocode
            # Generate a grid of points in the bounding rect
            # for each point
            # * project onto each reference face, get min dist
            # * project onto each test face, get min dist
            # * if the min dist changes for any point between
            #   the reference and test faces, then the "POV" has
            #   changed and the face can NOT be removed

            def _gen_pts(bounding_range, pln, num_pts_per_side=100):
                pts = []
                x_min, y_min, x_max, y_max = bounding_range
                x_range = x_max - x_min
                y_range = y_max - y_min
                for ix in range(num_pts_per_side):
                    x = x_min + ix*x_range
                    for iy in range(num_pts_per_side):
                        y = y_min + iy * y_range
                        if pln == PL_XZ:
                            pts.append(gp_Pnt(x, -100, y))
                        elif pln == PL_YZ:
                            pts.append(gp_Pnt(-1, x, y))
                        else:
                            raise RuntimeError()
                return pts

            def dist(p1, p2):
                return math.sqrt(math.pow(p1.X()-p2.X(), 2) + math.pow(p1.Y()-p2.Y(), 2) + math.pow(p1.Z()-p2.Z(), 2))

            def _get_distances(pts, faces):
                distances = []
                for p in pts:
                    for f in faces:
                        ff = Face(f)
                        uv, proj_pnt = ff.project_vertex(p)
                        distances.append(dist(proj_pnt, p))
                return distances


            pts = _gen_pts(bounding_range, pln)
            for p in pts:
                display.DisplayShape(p)

            ref_distances = _get_distances(pts, reference_faces)
            # test_distances = _get_distances(pts, test_faces)
            test_distances = _get_distances(pts, reference_faces)
            diff = [t-r for t, r in zip(test_distances, ref_distances)]
            diff2 = list(filter(lambda x: x > 0.001, diff))
            print("diff ", len(diff))
            print("diff2 ", len(diff2))
            return len(diff2) == 0





        temp_cut_compound = BRepAlgoAPI_Cut(compound_, cutting_extrusion).Shape()
        reference_all_faces = get_list_from_compound(temp_cut_compound, CompoundSequenceType.FACE)
        reference_nonperp_faces = get_nonperp_faces(reference_all_faces, face1_vec, False)
        # for rf in reference_nonperp_faces:
        #     display.DisplayShape(rf, color="GREEN", transparency=0.0)
        _face_can_be_removed(compound_nonperp_faces, reference_nonperp_faces, bounding_rect(compound_, PL_XZ), PL_XZ)

    start_display()

def _remove_redundant_geometry_helper(compound, height_mm):
    assert isinstance(compound, TopoDS_Compound)

    compound_ = copy.deepcopy(compound)

    faces = get_list_from_compound(compound_, CompoundSequenceType.FACE)
    cutting_extrusions = []
    for face in faces:
        gprop = BRepGProp_Face(face)
        normal_point = gp_Pnt(0, 0, 0)
        normal_vec = gp_Vec(0, 0, 0)
        # TODO: how to get middle of face with UV mapping?
        gprop.Normal(0, 0, normal_point, normal_vec)
        normal_vec_reversed = normal_vec.Reversed() # point into solid
        normal_extrusion = make_extrusion(face, height_mm, normal_vec_reversed)
        cutting_extrusions.append(normal_extrusion)

    bounding_box = make_bounding_box(compound_)
    # face1_vec = gp_Vec(0, 1, 0)
    # face1_reference_solid = project_and_clamp(compound_, face1_vec, bounding_box, height_mm)
    # display.DisplayShape(face1_reference_solid)
    # return None
    face2_vec = gp_Vec(-1, 0, 0)
    face2_reference_solid = project_and_clamp(compound_, face2_vec, bounding_box, height_mm)
    # start_display()

    # TODO: YOu are here. Fixed bug with the G curves being ignored (bounding box size)
    # Now the E face errors about 0.25 of the way through. Need ot find out why.
    # maybe not getting perp faces right?

    final_cutting_extrusions = []
    for index, cutting_extrusion in enumerate(cutting_extrusions):
        if index != 12:
            continue
        print("{}: cutting extrusion... {}".format(index, index / len(cutting_extrusions)))
        temp_cut_compound = BRepAlgoAPI_Cut(compound_, cutting_extrusion).Shape()

        temp_cut_compound_mass = get_mass(temp_cut_compound)

        if temp_cut_compound_mass > 0.001:
            # We only care about compounds with non-zero mass. If it has zero mass
            # then this cutting extrusion cuts away the entire object. It was likely create
            # from a face that covers the entire object, and We likely shouldn't remove it.
            # face1_valid = face_is_valid(temp_cut_compound, face1_vec, bounding_box, face1_reference_solid, height_mm)
            face1_valid = True
            # display.DisplayShape(cutting_extrusion, color="WHITE")
            face2_valid = face_is_valid(temp_cut_compound, face2_vec, bounding_box, face2_reference_solid, height_mm)
            # face2_valid = True
            if face1_valid and face2_valid:
                # If this cut removes no mass from the POV of the face(s) we are checking, then
                # we know it won't alter their appearance and is safe to remove
                final_cutting_extrusions.append(cutting_extrusion)

    final_geom = copy.deepcopy(compound_)
    for cut in final_cutting_extrusions:
        final_geom = BRepAlgoAPI_Cut(final_geom, cut).Shape()

    return copy.deepcopy(final_geom)


# Also, useful site to make svg letters: https://maketext.io/
# My blessed documentation: https://old.opencascade.com/doc/occt-6.9.0/refman/html/class_geom2d___b_spline_curve.html#a521ec5263443aca0d5ec43cd3ed32ac6
def main(word1, word2, height_mm, output_dir):
    # display, start_display, add_menu, add_function_to_menu = init_display()

    # face = FaceFactory._create_from_svg(Path(__file__).parent / "face_images/1.svg", height_mm=50)
    # display.DisplayShape(face, update=True, color="BLUE")

    display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
    display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
    display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")

    face_images_dir = pathlib.Path(__file__).parent / "face_images/aldrich"
    face_factory = FaceFactory(face_images_dir)

    letters, faces1, faces2 = combine_words(word1, word2, face_factory, height_mm)
    letters = remove_redundant_geometry(letters, height_mm)
    try:
        letters = remove_redundant_geometry(letters, height_mm)
    except AssertionError as e:
        # print(e)
        # if e
        # if e
        # print("ERROR")
        pass
    letters = offset_shapes(letters, height_mm)

    # for letter in letters:
    #     if letter:
    #         display.DisplayShape(letter)

    # save_to_stl(letters, output_dir)

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
    # test_bad_fusion()

