from enum import Enum
import copy

from OCC.Core import BRepGProp
from OCC.Core.BOPAlgo import BOPAlgo_Builder
from OCC.Core.BRepGProp import BRepGProp_Face
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.GProp import GProp_GProps
from OCC.Core.ShapeExtend import ShapeExtend_Explorer
from OCC.Core.TopTools import TopTools_HSequenceOfShape
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Solid, TopoDS_Face
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Pln
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCCUtils import Topo
from OCCUtils.base import GlobalProperties
from OCCUtils.face import Face

from constants import PL_XZ, PL_YZ

import logging
from OCCUtils.Construct import make_box, make_face
from OCCUtils.Construct import vec_to_dir

logger = logging.getLogger("TFT")


class CompoundSequenceType(Enum):
    FACE = 0
    SOLID = 1


def make_bounding_box(compound):
    assert isinstance(compound, TopoDS_Compound)

    compound_ = copy.deepcopy(compound)
    props = GlobalProperties(compound_)
    x1, y1, z1, x2, y2, z2 = props.bbox()
    fudge_factor = 0.001
    p = gp_Pnt(x1 - fudge_factor, y1 - fudge_factor, z1 - fudge_factor)
    p2 = gp_Pnt(x2 + fudge_factor, y2 + fudge_factor, z2 + fudge_factor)
    result = BRepPrimAPI_MakeBox(p, p2).Shape()
    assert isinstance(result, TopoDS_Solid)
    return copy.deepcopy(result)


def dot(v1, v2):
    assert isinstance(v1, gp_Vec)
    assert isinstance(v2, gp_Vec)
    result = v1.X() * v2.X() + v1.Y() * v2.Y() + v1.Z() * v2.Z()
    assert isinstance(result, float)
    return result


def get_perp_faces(faces, vec):
    return _get_faces_helper(faces, vec, perp=True)


def get_nonperp_faces(faces, vec):
    return _get_faces_helper(faces, vec, perp=False)


def add(pnt, vec):
    assert isinstance(pnt, gp_Pnt)
    assert isinstance(vec, gp_Vec)
    result = gp_Pnt(pnt.X() + vec.X(), pnt.Y() + vec.Y(), pnt.Z() + vec.Z())
    return result

def _get_faces_helper(faces, vec, perp=False):
    assert isinstance(vec, gp_Vec)
    assert isinstance(faces, list)

    result = []
    for face in faces:
        assert isinstance(face, TopoDS_Face)

        gprop = BRepGProp_Face(face)
        normal_point = gp_Pnt(0, 0, 0)
        normal_vec = gp_Vec(0, 0, 0)
        foo_face = Face(face)
        u_min, u_max, v_min, v_max = foo_face.domain()
        # Get point slightly in from a corner. This is in case the face
        # is curved, we don't want to mistrea it as perp or not by measuring
        # the normal at the edge
        u_mid = u_min + (u_max - u_min) / 100.
        v_mid = v_min + (v_max - v_min) / 100.
        gprop.Normal(u_mid, v_mid, normal_point, normal_vec)

        if perp:
            if abs(dot(vec, normal_vec)) == 0:
                result.append(face)
        else:
            if abs(dot(vec, normal_vec)) != 0:
                result.append(face)

    return copy.deepcopy(result)


def get_faces(compound):
    return _get_list_from_compound(compound, CompoundSequenceType.FACE)


def get_solids(compound):
    return _get_list_from_compound(compound, CompoundSequenceType.SOLID)


def _get_list_from_compound(compound, sequence_type):
    assert isinstance(sequence_type, CompoundSequenceType)
    assert isinstance(compound, TopoDS_Compound) or isinstance(compound, TopoDS_Solid)
    compound_ = copy.deepcopy(compound)

    if isinstance(compound, TopoDS_Compound):
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
    else:
        solids = [compound]

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
        solids = _get_list_from_compound(compound_, CompoundSequenceType.SOLID)
    else:
        solids = [compound_]

    total_mass = 0
    for solid in solids:
        props = GProp_GProps()
        BRepGProp.brepgprop_VolumeProperties(solid, props)
        mass = props.Mass()
        total_mass += mass
    return total_mass


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

def split_compound(compound, display):
    all_faces = get_faces(compound)
    planar_faces = list(filter(lambda x: Face(x).is_planar(), all_faces))

    p1, v1 = gp_Pnt(50, 50, 25), gp_Vec(0, 0, -1)
    fc1 = make_face(gp_Pln(p1, vec_to_dir(v1)), -1000, 1000, -1000, 1000)  # limited, not infinite plane

    bo = BOPAlgo_Builder()
    bo.AddArgument(copy.deepcopy(compound))
    # bo.AddArgument(fc1)

    # display.DisplayShape(fc1, transparency=0.7)
    for f in planar_faces:
        gprop = BRepGProp_Face(f)
        normal_point = gp_Pnt(0, 0, 0)
        normal_vec = gp_Vec(0, 0, 0)
        gprop.Normal(0, 0, normal_point, normal_vec)
        big_face = make_face(gp_Pln(normal_point, vec_to_dir(normal_vec)), -1000, 1000, -1000, 1000)  # limited, not infinite plane
        bo.AddArgument(big_face)
        # display.DisplayShape(big_face, transparency=0.7)

    bo.Perform()
    # print("error status: {}".format(bo.ErrorStatus()))

    top = Topo(bo.Shape())
    result = [s for s in top.solids()]
    return result