from OCC.Core.AIS import AIS_Shape
import copy
from OCC.Core.BRep import BRep_Builder
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
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.gp import gp_Trsf, gp_Ax1, gp_Vec, gp_Pnt
from constants import *
import math
from OCC.Core.StlAPI import StlAPI_Writer
import argparse
from pathlib import Path
import os
import errno
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Solid, TopoDS_Shape, TopoDS_Face

display, start_display, add_menu, add_function_to_menu = init_display()

class CompoundSequenceType(Enum):
    VERTEX = 0
    EDGE = 1
    FACE = 2
    SOLID = 3

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


def combine_words(word1, word2, height_mm):
    assert isinstance(word1, str)
    assert isinstance(word2, str)
    assert len(word1) == len(word2)

    combined_faces = []
    faces1 = []
    faces2 = []
    for letter1, letter2 in zip(word1, word2):
        face1 = FaceFactory.create_char(letter1, height_mm)
        face2 = FaceFactory.create_char(letter2, height_mm)
        faces1.append(face1)
        faces2.append(face2)
        combined_letter = combine_faces(face1, face2, height_mm)
        combined_faces.append(combined_letter)

    # Offset letters so they can be previewed properly from 2 directions
    tf = gp_Trsf()
    p1 = ORIGIN
    offset = 0
    offset_increment = 1.1*height_mm
    offset_letters = []
    for l in combined_faces:
        tf.SetTranslation(p1, gp_Pnt(offset, offset, 0))
        offset_letter = BRepBuilderAPI_Transform(l, tf).Shape()
        assert isinstance(offset_letter, TopoDS_Compound)
        offset_letters.append(offset_letter)
        offset += offset_increment

    return offset_letters, faces1, faces2


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


def solid_box(compound):
    assert isinstance(compound, TopoDS_Compound)
    compound_ = copy.deepcopy(compound)
    props = GlobalProperties(compound_)
    x1, y1, z1, x2, y2, z2 = props.bbox()
    p = gp_Pnt(x1, y1, z1)
    p2 = gp_Pnt(x2, y2, z2)
    result = BRepPrimAPI_MakeBox(p, p2).Shape()
    assert isinstance(result, TopoDS_Solid)
    return copy.deepcopy(result)

def dot(v1, v2):
    assert isinstance(v1, gp_Vec)
    assert isinstance(v2, gp_Vec)
    result =  v1.X() * v2.X() + v1.Y() * v2.Y() + v1.Z() * v2.Z()
    assert isinstance(result, float)
    return result

def get_nonperp_faces(vec, faces):
    assert isinstance(vec, gp_Vec)
    nonperp_faces = []
    for face in faces:
        assert isinstance(face, TopoDS_Face)
        # display.DisplayShape(face, color="GREEN", transparency=0.8)
        gprop = BRepGProp_Face(face)
        normal_point = gp_Pnt(0, 0, 0)
        normal_vec = gp_Vec(0, 0, 0)
        # TODO: how to get middle of face with UV mapping?
        gprop.Normal(0, 0, normal_point, normal_vec)
        if abs(dot(gp_Vec(0, 1, 0), normal_vec)) > 0.01:
            nonperp_faces.append(face)
    return copy.deepcopy(nonperp_faces)

def extrude_and_clamp(faces, vec, clamp, height_mm):
    assert isinstance(clamp, TopoDS_Solid)
    faces_ = copy.deepcopy(faces)
    vec_ = copy.deepcopy(vec)
    clamp_ = copy.deepcopy(clamp)
    extrusions = []
    for face in faces_:
        assert isinstance(face, TopoDS_Face)
        extrusions.append(make_extrusion(face, 2 * height_mm, vec_))
    builder = BOPAlgo_Builder()
    for extrusion in extrusions:
        builder.AddArgument(extrusion)
    builder.SetRunParallel(False)
    builder.Perform()
    if builder.HasErrors():
        raise AssertionError("Failed with error: ", builder.DumpErrorsToString())
    extruded_faces = builder.Shape()
    result = BRepAlgoAPI_Common(extruded_faces, clamp_).Shape()
    assert isinstance(result, TopoDS_Compound)
    return copy.deepcopy(result)

def make_magic_solid(compound, containing_box, height_mm):
    print("~~~ making magic solid")
    assert isinstance(compound, TopoDS_Compound)
    assert isinstance(containing_box, TopoDS_Solid)
    compound_ = copy.deepcopy(compound)
    containing_box_ = copy.deepcopy(containing_box)

    all_faces = get_list_from_compound(compound_, CompoundSequenceType.FACE)
    print("all faces: {}".format(len(all_faces)))
    nonperp_faces = get_nonperp_faces(gp_Vec(0, 1, 0), all_faces)
    print("nonperp faces: {}".format(len(nonperp_faces)))
    if not nonperp_faces:
        raise RuntimeError("AAAAAAAH")
    magic_compound = extrude_and_clamp(nonperp_faces, gp_Vec(0, 1, 0), containing_box_, height_mm)
    assert isinstance(magic_compound, TopoDS_Compound)
    print("~~~ done making magic solid")
    return copy.deepcopy(magic_compound)


def get_list_from_compound(compound, seq_type):
    assert isinstance(seq_type, CompoundSequenceType)
    compound_ = copy.deepcopy(compound)

    se_exp = ShapeExtend_Explorer()
    hseqofshape = se_exp.SeqFromCompound(compound_, True)
    hseq_vertices = TopTools_HSequenceOfShape()
    hseq_edges = TopTools_HSequenceOfShape()
    hseq_wires = TopTools_HSequenceOfShape()
    hseq_faces = TopTools_HSequenceOfShape()
    hseq_shells = TopTools_HSequenceOfShape()
    hseq_solids = TopTools_HSequenceOfShape()
    hseq_compsols = TopTools_HSequenceOfShape()
    hseq_compounds = TopTools_HSequenceOfShape()
    se_exp.DispatchList(hseqofshape, hseq_vertices, hseq_edges, hseq_wires, hseq_faces, hseq_shells, hseq_solids,
                        hseq_compsols, hseq_compounds)

    # Only the solids seem to be populated properly. Need to use TopologyExporer to get other features
    solids = [hseq_solids.Value(i) for i in range(1, hseq_solids.Length() + 1)] # Indices start at 1 :(
    faces = [f for solid in solids for f in TopologyExplorer(solid).faces()]
    edges = [f for solid in solids for f in TopologyExplorer(solid).edges()]
    vertices = [f for solid in solids for f in TopologyExplorer(solid).vertices()]

    if seq_type == CompoundSequenceType.VERTEX:
        return vertices
    elif seq_type == CompoundSequenceType.EDGE:
        return edges
    elif seq_type == CompoundSequenceType.FACE:
        return faces
    elif seq_type == CompoundSequenceType.SOLID:
        return solids
    else:
        raise ValueError("Invalid sequence type")


def get_mass(compound):
    assert isinstance(compound, TopoDS_Compound)
    compound_ = copy.deepcopy(compound)

    solids = get_list_from_compound(compound_, CompoundSequenceType.SOLID)
    print("Found {} solids in the compound".format(len(solids)))

    total_mass = 0
    for solid in solids:
        props = GProp_GProps()
        BRepGProp.brepgprop_VolumeProperties(solid, props)
        mass = props.Mass()
        print("partial mass: ", mass)
        total_mass += mass
    print("total mass ", total_mass)
    return total_mass

def remove_redundant_geometry(compound, face1, face2, height_mm):
    assert isinstance(compound, TopoDS_Compound)
    assert isinstance(face1, TopoDS_Face)
    assert isinstance(face2, TopoDS_Face)

    compound_ = copy.deepcopy(compound)
    face1_ = copy.deepcopy(face1)
    face2_ = copy.deepcopy(face2)

    bounding_box = solid_box(compound_)
    face1_reference_solid = make_magic_solid(compound_, bounding_box, height_mm)
    # display.DisplayShape(face1_reference_solid)

    faces = get_list_from_compound(compound_, CompoundSequenceType.FACE)
    print("total num faces: {}".format(len(faces)))
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

    # NOTES:
    # the display statement is causing foo to change (the magic solid for the temp piece)
    # issue seems to be specifically in make_magic_solid function. Everything else works as expected / the optimized_solid_temp shape is ok
    # IDEA: does an odd number of faces result in no extrusion? Do they cancel out?
    # non-perp faces seem to be the same...
    # containing box is the same
    # magic-extrusions seem to be the same...

    print("len cutting extrusions: {}".format(len(cutting_extrusions)))
    final_cutting_extrusions = []
    for index, cutting_extrusion in enumerate(cutting_extrusions):
        optimized_solid_temp = BRepAlgoAPI_Cut(compound_, cutting_extrusion).Shape()

        ost_mass = get_mass(optimized_solid_temp)
        # print("ost mass: {}".format(ost_mass))
        if index == 17:
            # display.DisplayShape(optimized_solid_temp, color="CYAN", transparency=1.0) # This varies the problem
            # display.DisplayShape(cutting_extrusion, color="BLACK", transparency=0.8)
            print("\n\n\n{} index ost_mass: {}".format(index, ost_mass))
            # continue

        if ost_mass < 1.001:
            # The face we're operating on is likely an entire face. Definitely can't remove it
            # print("{} OST MASS SMALL".format(index))
            pass
        else:
            foo = make_magic_solid(optimized_solid_temp, bounding_box, height_mm)
            # testvar33 = BRepAlgoAPI_Common(magic_extruded_faces, magic_clamp).Shape()
            # foo = copy.deepcopy(testvar33)
            if foo:
                diff = BRepAlgoAPI_Cut(face1_reference_solid, foo).Shape()
                # display.DisplayShape(diff, color="RED", transparency=0.8)
                diff_mass = get_mass(diff)
                if index == 17:
                    # display.DisplayShape(foo, transparency=0.5)
                    # display.DisplayShape(magic_containing_box, color="BLUE", transparency=0.8)
                    # display.DisplayShape(magic_extruded_faces, color="BLUE", transparency=0.8)
                    # display.DisplayShape(magic_clamp, color="RED", transparency=1.0)
                    # testvar = BRepAlgoAPI_Common(magic_extruded_faces, magic_clamp).Shape()
                    # display.DisplayShape(testvar, transparency=0.5)
                    # display.DisplayShape(magic_clamp, color="RED", transparency=0.8)
                    # for me in magic_extrusions:
                    #     display.DisplayShape(me, color=random_color(), transparency=0.8)
                    # for npf in nonperp_faces:
                    #     display.DisplayShape(npf, color="BLUE", transparency=0.8)
                    # display.DisplayShape(optimized_solid_temp, color="BLUE", transparency=0.8)
                    # display.DisplayShape(face1_reference_solid, color="BLUE", transparency=0.8)
                    # display.DisplayShape(diff, color="RED", transparency=0.8)
                    print("{} diff_mass: {}".format(index, diff_mass))
                if diff_mass < 0.1:
                    final_cutting_extrusions.append(cutting_extrusion)
            else:
                pass
        if index == 17:
            print("\n\n\n")

    print("num final cutting extrusions: {}".format(len(final_cutting_extrusions)))
    final_geom = compound_
    for cut in final_cutting_extrusions:
        final_geom = BRepAlgoAPI_Cut(final_geom, cut).Shape()

    display.DisplayShape(final_geom, update=True, color="GREEN", transparency=0.9)
    print("FACES REMOVED: {}".format(len(final_cutting_extrusions)))
    return copy.deepcopy(final_geom)
    # return None

        # CHECK IF FACES STILL EXIST AS NEEDED

        # WHY DOES THIS AFFECT BEHABIOR????
        # display.DisplayShape(face, update=True, color="CYAN", transparency=0.8)
        # if foo:
        #     # display.DisplayShape(foo, color="CYAN", transparency=0.8)
        #     diff = BRepAlgoAPI_Cut(face1_reference_solid, foo).Shape()
        #     # display.DisplayShape(diff, color="RED", transparency=0.8)
        #
        #     diff_mass = get_mass(diff)
        #     print("{}: MASS: {}".format(index, diff_mass))
        #     if diff_mass > 10:
        #         print("keeping diff {}".format(index))
        #
        #     else:
        #         print("######### cutting diff {}".format(index))
        #         optimized_solid = BRepAlgoAPI_Cut(optimized_solid, normal_extrusion).Shape()
        #     # display.DisplayShape(optimized_solid, transparency=0.8)
        # else:
        #     print("keeping diff {}".format(index))
            # optimized_solid = BRepAlgoAPI_Cut(optimized_solid, normal_extrusion).Shape()
            # "GOOD" faces
            # display.DisplayShape(face, update=True, color=random_color())


    # display.DisplayShape(optimized_solid)
    # break









        #
        # containing_box = solid_box(solid)
        # # display.DisplayShape(containing_box, color="WHITE", transparency=0.9)
        # negative_solid = BRepAlgoAPI_Cut(containing_box, solid).Shape()
        # # display.DisplayShape(negative_solid, color="BLACK", transparency=0.8)
        #
        # face1_extruded = make_extrusion(face1, face_width(face2), gp_Vec(0, 1, 0))
        # # display.DisplayShape(face1_extruded, color="BLUE", transparency=0.8)
        # face1_extruded_trimmed = BRepAlgoAPI_Cut(face1_extruded, negative_solid).Shape()
        # display.DisplayShape(face1_extruded_trimmed, color="BLUE", transparency=0.8)
        #
        # remainder = BRepAlgoAPI_Cut(face1_extruded_trimmed, optimized_solid_temp).Shape()
        # # display.DisplayShape(remainder, transparency=0.5)
        # from OCC.Core.TopoDS import TopoDS_Solid
        # from OCC.Core.GProp import GProp_GProps
        # from OCC.Core import BRepGProp
        # props = GProp_GProps()
        # BRepGProp.brepgprop_VolumeProperties(remainder, props)
        # print("{}: MASS: {}".format(index, props.Mass()))

    # display.DisplayShape(optimized_solid, transparency=0.8)

    #
    #
    #
    #
    # from OCCUtils.Construct import project_edge_onto_plane
    # from OCCUtils.Construct import make_edge as make_edge_foo
    # from OCCUtils.edge import Edge
    # from OCC.Core.GeomAdaptor import GeomAdaptor_Curve
    # from OCC.Core.GeomProjLib import geomprojlib_ProjectOnPlane
    # from OCC.Core.Prs3d import Prs3d_Projector
    # from OCC.Core.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
    # from OCC.Extend.TopologyUtils import HLRAlgo_Projector
    # from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_HCurve
    # from OCCUtils.edge import Edge
    # from OCC.Core.Geom import Geom_Plane
    # solid_edges = TopologyExplorer(solid).edges()
    # face1edges = TopologyExplorer(face1).edges()
    # # display.DisplayShape(face1edges)
    # face2edges = TopologyExplorer(face2).edges()
    # proj_edges = []
    # for edge in face1edges:
    #     e = Edge(edge)
    #     pl = Geom_Plane(PL_XZ)
    #     # display.DisplayShape(e, update=True, color="BLUE")
    #     # display.DisplayShape(e.adaptor.Curve().Curve(), update=True, color="BLUE")
    #     # adaptor = BRepAdaptor_Curve(e)
    #     # display.DisplayShape(e.curve)
    #     # proj_edges.append(make_edge())
    #     # adaptor.
    #
    #     # baz = HLRAlgo_Projector(AX_XZ)
    #     # # baz = HLRAlgo_Projector(AX_YZ)
    #     # # baz.
    #     # # projector = Prs3d_Projector(True, 100, proj_vector[0], proj_vector[1], proj_vector[2], view_point[0], view_point[1], view_point[2], vertical_direction_vector[0], vertical_direction_vector[1], vertical_direction_vector[2])
    #     # # algo.Projector(projector.Projector())
    #     # algo = HLRBRep_Algo()
    #     # algo.Add(e)
    #     # algo.Projector(baz)
    #     # algo.Update()
    #     # foobar = HLRBRep_HLRToShape(algo)
    #     # projshape = foobar.VCompound()
    #     # print(type(projshape))
    #     # shapep = AIS_Shape(projshape).Shape()
    #     # display.DisplayShape(projshape, update=True, color="BLUE")
    #     # projshape = foobar.VCompound()
    #     # projshape = foobar.OutLineHCompound()
    #     # projshape = foobar.IsoLineHCompound()
    #     # print(type(projshape))
    #     # shapep = AIS_Shape(projshape).Shape()
    #     # print(type(shapep))
    #     # display.DisplayShape(projshape, update=True, color="BLACK")
    #
    #     # continue
    #     # display.DisplayShape(e)
    #     # proj_edges.append(project_edge_onto_plane(e, pl))
    #     # from OCC.Core.GeomProjLib import geomprojlib_ProjectOnPlane
    #     # proj = geomprojlib_ProjectOnPlane(e.adaptor.Curve().Curve(), pl, pl.Axis().Direction(), False)
    #     proj = geomprojlib_ProjectOnPlane(e.adaptor.Curve().Curve(), pl, pl.Axis().Direction(), False)
    #     print(e.adaptor.Curve().GetType())
    #     print('projtype: ', type(proj))
    #     projedge = Edge(make_edge(proj))
    #     proj_edges.append(projedge)
    #     print("projedge type: ", type(projedge))
    #     test = GeomAdaptor_Curve(proj)
    #     test2 = test.Trim(0, 1, 0.01)
    #     display.DisplayShape(test2.Curve(), update=True, color="RED")
    #
    #     print('test type: ', type(test))
    #     # try:
    #     #     display.DisplayShape(projedge, update=True, color="RED")
    #     # except Exception:
    #     #     pass
    #     # proj_edges.append(proj)
    #     # Geom_Plane
    #     # return make_edge(proj)
    #
    #     # proj = geomprojlib_ProjectOnPlane(edge.Curve(), PL_XZ, PL_XZ.Axis().Direction(), 1)
    #     # proj_edges.append(project_edge_onto_plane(e, PL_XZ))
    #
    # # display.DisplayShape([proj_edges])
    # # print("edge types")
    # # test_edge = make_edge(gp_Pnt(0, 0, 100), gp_Pnt(100, 0, 100))
    # # display.DisplayShape(test_edge, update=True, color="BLACK")
    # # for pe in proj_edges:
    # #     print(type(pe))
    # #     # print(type(make_edge(pe)))
    # #     try:
    # #         display.DisplayShape(pe, update=True, color="RED")
    # #     except Exception:
    # #         pass
    # #     print(pe.closest(test_edge))
    #
    #
    #
    #
    #
    # return None

# Also, useful site to make svg letters: https://maketext.io/
# My blessed documentation: https://old.opencascade.com/doc/occt-6.9.0/refman/html/class_geom2d___b_spline_curve.html#a521ec5263443aca0d5ec43cd3ed32ac6
def main(word1, word2, height_mm, output_dir):
    # display, start_display, add_menu, add_function_to_menu = init_display()

    # face = FaceFactory._create_from_svg(Path(__file__).parent / "face_images/1.svg", height_mm=50)
    # display.DisplayShape(face, update=True, color="BLUE")

    display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
    display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
    display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")

    letters, faces1, faces2 = combine_words(word1, word2, height_mm)
    letter = letters[0]
    face1 = faces1[0]
    face2 = faces2[0]
    new_geom = remove_redundant_geometry(letter, face1, face2, height_mm)
    if new_geom:
        display.DisplayShape(new_geom, update=True, color="GREEN")



    # for l in letters:
    #     display.DisplayColoredShape(l, update=True, color="WHITE")

    # def get_color():
    #     while True:
    #         for c in ["RED", "GREEN", "BLUE", "CYAN", "ORANGE", "YELLOW", "BLACK"]:
    #             yield c
    #
    # for i in range(10):
    #     print(get_color())
    #
    # letter = letters[0]
    # print(type(letter))
    # face1 = faces1[0]
    # face2 = faces2[0]
    # colors = get_color()
    # from OCC.Extend.TopologyUtils import TopologyExplorer
    # from OCC.Core import BRepTools
    # from OCC.Core.BRepGProp import BRepGProp_Face
    # from OCC.Core.GeomLProp import GeomLProp_SLProps
    # # from OCC.Core.HLRTopoBRep import ToShape
    # # from OCC.Core.HLRAlgo import HLRAlgo
    # # from OCC.Core import HLRAlgo
    # # from OCC.Core.HLRBRep import HLRBRep_HLRToShape
    # from OCC.Core.Prs3d import Prs3d_Projector
    # from OCC.Core.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
    # from OCC.Extend.TopologyUtils import HLRAlgo_Projector
    #
    # # def face_center(face):
    # #     face.bb
    #
    # # algo = HLRBRep_Algo()
    # # algo.Add(letter)
    # proj_vector = (1, 0, 0)
    # view_point = (0, -100, 0)
    # vertical_direction_vector = (0, 0, 1)
    #
    # # baz = HLRAlgo_Projector(AX_XZ)
    # # baz = HLRAlgo_Projector(AX_YZ)
    # # baz.
    # # projector = Prs3d_Projector(True, 100, proj_vector[0], proj_vector[1], proj_vector[2], view_point[0], view_point[1], view_point[2], vertical_direction_vector[0], vertical_direction_vector[1], vertical_direction_vector[2])
    # # algo.Projector(projector.Projector())
    # # algo.Projector(baz)
    # # algo.Update()
    # # foobar = HLRBRep_HLRToShape(algo)
    # # projshape = foobar.VCompound()
    # # projshape = foobar.VCompound()
    # # projshape = foobar.OutLineHCompound()
    # # projshape = foobar.IsoLineHCompound()
    # # print(type(projshape))
    # # shapep = AIS_Shape(projshape).Shape()
    # # print(type(shapep))
    # # display.DisplayShape(projshape, update=True, color="BLACK")
    # # print(type(foobar))
    # # shape = None
    # # foobar.HCompound(shape)
    # # print(shape)
    # # proj_shape = AIS_Shape(foobar.HCompound())
    # # display.DisplayShape(letter, update=True, color="BLACK")
    # from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Common
    # from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
    # # from OCC.Core.TopoDS import m
    #
    # from OCC.Extend.TopologyUtils import TopologyExplorer
    # projshape_edges = TopologyExplorer(letter).edges()
    # # BRepAlgoAPI_Common
    # face1_edges = TopologyExplorer(letter).edges()
    # pse = None
    # pse2 = None
    # for i, e in enumerate(projshape_edges):
    #     if i == 10:
    #         pse = e
    #     if i == 11:
    #         pse2 = e
    # fe = None
    # fe2 = None
    # for i, e in enumerate(face1_edges):
    #     if i == 4:
    #         fe = e
    #     if i == 5:
    #         fe2 = e
    # print("types: {}, {}".format(fe, pse))
    # print("types: {}, {}".format(fe2, pse2))
    #
    # # display.DisplayShape(pse, update=True, color="BLACK")
    # # display.DisplayShape(fe, update=True, color="WHITE")
    # print("INFO")
    # print('orientation ', fe.Orientation())
    # print('null ', fe.IsNull())
    # foo = make_edge(gp_Pnt(0, 0, 0), gp_Pnt(10, 10, 10))
    # print(type(foo))
    # # display.DisplayShape(foo, update=True, color="CYAN")
    # dss = BRepExtrema_DistShapeShape(fe, fe2)
    # print(dss.Value())
    # # d = fe.closest(pse)
    # # dss.LoadS1(fe)
    # # dss.LoadS2(pse)
    # # dss.Perform()
    # # for fe in face1_edges:
    # #     for pse in projshape_edges:
    # #         print("types: {}, {}".format(fe, pse))
    # #         # display.DisplayShape([fe, pse])
    # #         display.DisplayShape(pse, update=True, color="BLACK")
    # #         display.DisplayShape(fe, update=True, color="WHITE")
    # #         dss = BRepExtrema_DistShapeShape()
    # #         # d = fe.closest(pse)
    # #         dss.LoadS1(fe)
    # #         dss.LoadS2(pse)
    # #         dss.Perform()
    # #         break
    # #         # assert dss.IsDone()
    # #         # print(dss.Value())
    # #     break
    #
    #
    #
    #
    #
    #
    # # exp = TopologyExplorer(letter)
    # # # for edge in exp.edges():
    # # #     display.DisplayShape(edge, update=True, color=next(colors))
    # # for face in exp.faces():
    # #     display.DisplayShape(face, update=True, color=next(colors))
    # #
    # #     foo = BRepGProp_Face(face)
    # #     normal_point = gp_Pnt(0, 0, 0)
    # #     normal_vec = gp_Vec(0, 0, 0)
    # #     # TODO: how to get middle of face with UV mapping?
    # #     foo.Normal(0, 0, normal_point, normal_vec)
    # #     # display.DisplayShape(normal_point, update=True, color="BLACK")
    # #     normal_vec.Reverse()
    # #     # normal_extrusion = make_extrusion(face, 2*height_mm, normal_vec)
    # #     # display.DisplayShape(normal_extrusion, update=True, color="BLACK")
    # #     # letter = BRepAlgoAPI_Cut(letter, normal_extrusion).Shape()
    # #
    # #     normal_extrusion = make_extrusion(face, 2*height_mm, normal_vec)
    # #     # display.DisplayShape(normal_extrusion, update=True, color="BLACK")
    # #     letter = BRepAlgoAPI_Cut(letter, normal_extrusion).Shape()
    # #
    # #     algo = HLRBRep_Algo()
    # #     algo.Add(letter)
    # #     projector = Prs3d_Projector(False, 0, 0, 0, 5, 0, 0, 1, 0, 1, 0)
    # #     algo.Projector(projector.Projector())
    # #     algo.Update()
    # #     foobar = HLRBRep_HLRToShape(algo)
    # #     print(type(foobar))
    # #     shape = None
    # #     foobar.HCompound(shape)
    # #     print(shape)
    # #     proj_shape = AIS_Shape(foobar.HCompound())
    # #     # display.DisplayShape(foobar.HCompound, update=True, color="CYAN")
    # #
    # #     # print(normal_point)
    # #     # display.DisplayShape(v, update=True, color="BLACK")
    # #     # print(normal_vec)
    # #
    # #     # print(face.normalAt(0, 0))
    # #     # face
    # #     break
    # # display.DisplayShape(letter, update=True, color="BLACK")
    #
    # # save_to_stl(letters, output_dir)

    start_display()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Combine words into Two-Faced Type, and output as STLs")
    parser.add_argument('words', metavar='word', type=str, nargs=2, help='the words to combine')
    parser.add_argument('-o', '--output_dir', metavar='output_directory', type=str,
                        help="The directory to write STL files to. Will be created if it doesn't exist", required=True)
    parser.add_argument('--height', metavar='height_mm', type=float, help="The height of the characters, in mm",
                        required=True)
    args = parser.parse_args()
    print(args)

    main(args.words[0], args.words[1], args.height, args.output_dir)
