from OCC.Core.BRep import BRep_Builder
from OCC.Display.SimpleGui import init_display
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.gp import gp_Trsf
from OCC.Extend.ShapeFactory import make_extrusion
from OCCUtils.Common import fix_tolerance
from OCCUtils.Construct import sew_shapes

from util import *

from OCCUtils.Construct import boolean_fuse

display, start_display, add_menu, add_function_to_menu = init_display()
import logging

logger = logging.getLogger("TFT")


def fix_shape(shape, tolerance=1e-3):
    from OCC.Core.ShapeFix import ShapeFix_Shape
    fix = ShapeFix_Shape(shape)
    fix.SetFixFreeShellMode(True)
    sf = fix.FixShellTool()
    sf.SetFixOrientationMode(True)
    fix.LimitTolerance(tolerance)
    fix.Perform()
    return copy.deepcopy(fix.Shape())

def extrude_and_clamp_old(faces, vec, clamp, height_mm):
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
        eee = fix_shape(ee)
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
        # test_result = boolean_fuse(copy.deepcopy(result), copy.deepcopy(s))
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
        # tt1 = boolean_fuse(copy.deepcopy(fixed_result), copy.deepcopy(fs))
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
            # tt2 = boolean_fuse(copy.deepcopy(fixed_result), copy.deepcopy(fs2))
            tt2.SetFuzzyValue(1.0)
            tt2.SetCheckInverted(False)
            tt2.SetNonDestructive(False)
            if tt2.Shape() is not None:
                fixed_result = copy.deepcopy(tt2.Shape())
            else:
                double_failed_fuses.append(copy.deepcopy(fs))

    if failed_fuses:
        logger.warning("Recovered fuses: {}".format(len(failed_fuses) - len(double_failed_fuses)))
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
        # fix_tolerance(ee, 1e-3)
        # eee = fix_shape(ee, 1e-3)
        clamped_extrusions.append(copy.deepcopy(ee))

    # THIS WORKS????
    # aRes = TopoDS_Compound()
    # aBuilder = BRep_Builder()
    # aBuilder.MakeCompound(aRes)
    # for e in clamped_extrusions:
    #     aBuilder.Add(aRes, e)

    combo = sew_shapes(clamped_extrusions)
    return copy.deepcopy(combo)

    # print("res ", aRes)

    # result = copy.deepcopy(clamped_extrusions[0])
    # failed_fuses = []
    # for s in clamped_extrusions[1:]:
    #     test_result = BRepAlgoAPI_Fuse(copy.deepcopy(result), copy.deepcopy(s))
    #     test_result.SetFuzzyValue(1.0)
    #     test_result.SetNonDestructive(False)
    #     test_result.SetCheckInverted(False)
    #     shape = test_result.Shape()
    #     if shape is None:
    #         failed_fuses.append(copy.deepcopy(s))
    #     else:
    #         shape = fix_shape(shape, 1e-6)
    #         fix_tolerance(shape, 1e-6)
    #         result = copy.deepcopy(shape)
    #
    # print("{} failed fuses".format(len(failed_fuses)))
    # display.DisplayShape(aRes, color="BLUE", transparency=0.7)
    # start_display()
    return copy.deepcopy(aRes)


def project_and_clamp(compound, vec, containing_box, height_mm, disp=False):
    assert isinstance(compound, TopoDS_Compound)
    assert isinstance(containing_box, TopoDS_Solid)
    compound_ = copy.deepcopy(compound)
    containing_box_ = copy.deepcopy(containing_box)

    all_faces = get_faces(compound_)
    nonperp_faces = get_nonperp_faces(all_faces, vec)
    if not nonperp_faces:
        raise RuntimeError("No nonperp faces. This probably shouldn't happen.")
    magic_compound = extrude_and_clamp(nonperp_faces, vec, containing_box_, height_mm)
    assert isinstance(magic_compound, TopoDS_Compound)
    return copy.deepcopy(magic_compound)


def face_is_valid(temp_cut_compound_, vec_, bounding_box_, reference_solid, height_mm):
    temp_projected_compound = project_and_clamp(temp_cut_compound_, vec_, bounding_box_, height_mm, disp=True)
    reference_mass = get_mass(reference_solid)
    temp_mass = get_mass(temp_projected_compound)
    # if temp_mass > reference_mass:
    #     display.DisplayShape(temp_projected_compound, color="BLUE", transparency=0.8)
    #     display.DisplayShape(reference_solid, color="RED", transparency=0.8)
    #     start_display()
    print("reference mass: {}     temp mass: {}".format(reference_mass, temp_mass))
    # return abs(get_mass(reference_solid) - get_mass(temp_projected_compound)) < 1.0
    diff = BRepAlgoAPI_Cut(reference_solid, temp_projected_compound)
    # diff.SetNonDestructive(False)
    # diff.SetCheckInverted(False)
    # diff.SetFuzzyValue(1.01)
    diffff = diff.Shape()
    if diffff is None:
        # display.DisplayShape(reference_solid, color="BLUE", transparency=0.8)
        print("difffff is NOne")
        # display.DisplayShape(temp_projected_compound, color="RED", transparency=0.8)
        return False
        # display.DisplayShape(reference_solid, color="BLUE", transparency=0.8)
        # start_display()
    diff_mass = get_mass(diffff)
    return diff_mass < 0.1


def remove_redundant_geometry_solid_diff(compound, height_mm):
    assert isinstance(compound, TopoDS_Compound)

    compound_ = copy.deepcopy(compound)

    faces = get_faces(compound_)
    cutting_extrusions = []
    for face in faces:
        gprop = BRepGProp_Face(face)
        normal_point = gp_Pnt(0, 0, 0)
        normal_vec = gp_Vec(0, 0, 0)
        # TODO: how to get middle of face with UV mapping?
        gprop.Normal(0, 0, normal_point, normal_vec)
        normal_vec_reversed = normal_vec.Reversed()  # point into solid
        normal_extrusion = make_extrusion(face, height_mm, normal_vec_reversed)
        cutting_extrusions.append(normal_extrusion)

    bounding_box = make_bounding_box(compound_)
    # face1_vec = gp_Vec(0, 1, 0)
    # face1_reference_solid = project_and_clamp(compound_, face1_vec, bounding_box, height_mm)
    # display.DisplayShape(face1_reference_solid)
    # return None
    face2_vec = gp_Vec(-1, 0, 0)
    face2_reference_solid = project_and_clamp(compound_, face2_vec, bounding_box, height_mm)
    # display.DisplayShape(face2_reference_solid, color="BLUE", transparency=0.7)
    # start_display()

    # TODO: YOu are here. Fixed bug with the G curves being ignored (bounding box size)
    # Now the E face errors about 0.25 of the way through. Need ot find out why.
    # maybe not getting perp faces right?

    final_cutting_extrusions = []
    for index, cutting_extrusion in enumerate(cutting_extrusions):
        # if index > 3:
        #     continue
        # display.DisplayShape(cutting_extrusion)
        # display.DisplayShape(compound_, color="BLUE", transparency=0.8)
        # start_display()
        print("{}: {}".format(index, index / len(cutting_extrusions)))
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
                print("{}: cutting extrusion".format(index, index / len(cutting_extrusions)))
                # If this cut removes no mass from the POV of the face(s) we are checking, then
                # we know it won't alter their appearance and is safe to remove
                final_cutting_extrusions.append(cutting_extrusion)

    final_geom = copy.deepcopy(compound_)
    for cut in final_cutting_extrusions:
        final_geom = BRepAlgoAPI_Cut(final_geom, cut).Shape()

    return copy.deepcopy(final_geom)
