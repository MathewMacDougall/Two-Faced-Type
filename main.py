from OCC.Core.AIS import AIS_Shape
from OCC.Display.SimpleGui import init_display
from OCC.Extend.ShapeFactory import make_extrusion, make_edge, make_face
from face_factory import FaceFactory
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.gp import gp_Trsf, gp_Ax1, gp_Vec, gp_Pnt
from constants import *
import math
from OCC.Core.StlAPI import StlAPI_Writer
import argparse
from pathlib import Path
import os
import errno

display, start_display, add_menu, add_function_to_menu = init_display()

def combine_faces(face1, face2, height_mm):
    # assuming both faces start in the XZ plane
    tf = gp_Trsf()
    # rotate from the XZ plane to the YZ plane
    tf.SetRotation(gp_Ax1(ORIGIN, DIR_Z), math.pi / 2)
    face2 = BRepBuilderAPI_Transform(face2, tf).Shape()

    # We assume characters are no wider than they are tall, but just in case
    # we extrude by twice the height to make sure to capture all features
    face1_extruded = make_extrusion(face1, 2 * height_mm, gp_Vec(0, 1, 0))
    face2_extruded = make_extrusion(face2, 2 * height_mm, gp_Vec(1, 0, 0))
    common = BRepAlgoAPI_Common(face1_extruded, face2_extruded)

    return common.Shape()


def combine_words(word1, word2, height_mm):
    assert len(word1) == len(word2)

    combined_faces = []
    faces1 = []
    faces2 = []
    for letter1, letter2 in zip(word1, word2):
        face1 = FaceFactory.create_char(letter1, height_mm)
        face2 = FaceFactory.create_char(letter2, height_mm)
        faces1.append(face1)
        faces2.append(face2)
        # display.DisplayShape(face1, update=True, color="RED")
        # display.DisplayShape(face2, update=True, color="RED")
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
        offset_letters.append(BRepBuilderAPI_Transform(l, tf).Shape())
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

    # for l in letters:
    #     display.DisplayColoredShape(l, update=True, color="WHITE")

    def get_color():
        while True:
            for c in ["RED", "GREEN", "BLUE", "CYAN", "ORANGE", "YELLOW", "BLACK"]:
                yield c

    for i in range(10):
        print(get_color())

    letter = letters[0]
    print(type(letter))
    face1 = faces1[0]
    face2 = faces2[0]
    colors = get_color()
    from OCC.Extend.TopologyUtils import TopologyExplorer
    from OCC.Core import BRepTools
    from OCC.Core.BRepGProp import BRepGProp_Face
    from OCC.Core.GeomLProp import GeomLProp_SLProps
    # from OCC.Core.HLRTopoBRep import ToShape
    # from OCC.Core.HLRAlgo import HLRAlgo
    # from OCC.Core import HLRAlgo
    # from OCC.Core.HLRBRep import HLRBRep_HLRToShape
    from OCC.Core.Prs3d import Prs3d_Projector
    from OCC.Core.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
    from OCC.Extend.TopologyUtils import HLRAlgo_Projector

    # def face_center(face):
    #     face.bb

    # algo = HLRBRep_Algo()
    # algo.Add(letter)
    proj_vector = (1, 0, 0)
    view_point = (0, -100, 0)
    vertical_direction_vector = (0, 0, 1)

    # baz = HLRAlgo_Projector(AX_XZ)
    # baz = HLRAlgo_Projector(AX_YZ)
    # baz.
    # projector = Prs3d_Projector(True, 100, proj_vector[0], proj_vector[1], proj_vector[2], view_point[0], view_point[1], view_point[2], vertical_direction_vector[0], vertical_direction_vector[1], vertical_direction_vector[2])
    # algo.Projector(projector.Projector())
    # algo.Projector(baz)
    # algo.Update()
    # foobar = HLRBRep_HLRToShape(algo)
    # projshape = foobar.VCompound()
    # projshape = foobar.VCompound()
    # projshape = foobar.OutLineHCompound()
    # projshape = foobar.IsoLineHCompound()
    # print(type(projshape))
    # shapep = AIS_Shape(projshape).Shape()
    # print(type(shapep))
    # display.DisplayShape(projshape, update=True, color="BLACK")
    # print(type(foobar))
    # shape = None
    # foobar.HCompound(shape)
    # print(shape)
    # proj_shape = AIS_Shape(foobar.HCompound())
    # display.DisplayShape(letter, update=True, color="BLACK")
    from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
    # from OCC.Core.TopoDS import m

    projshape_edges = TopologyExplorer(letter).edges()
    # BRepAlgoAPI_Common
    face1_edges = TopologyExplorer(letter).edges()
    pse = None
    pse2 = None
    for i, e in enumerate(projshape_edges):
        if i == 10:
            pse = e
        if i == 11:
            pse2 = e
    fe = None
    fe2 = None
    for i, e in enumerate(face1_edges):
        if i == 4:
            fe = e
        if i == 5:
            fe2 = e
    print("types: {}, {}".format(fe, pse))
    print("types: {}, {}".format(fe2, pse2))

    display.DisplayShape(pse, update=True, color="BLACK")
    display.DisplayShape(fe, update=True, color="WHITE")
    print("INFO")
    print('orientation ', fe.Orientation())
    print('null ', fe.IsNull())
    foo = make_edge(gp_Pnt(0, 0, 0), gp_Pnt(10, 10, 10))
    print(type(foo))
    display.DisplayShape(foo, update=True, color="CYAN")
    dss = BRepExtrema_DistShapeShape(fe, fe2)
    print(dss.Value())
    # d = fe.closest(pse)
    # dss.LoadS1(fe)
    # dss.LoadS2(pse)
    # dss.Perform()
    # for fe in face1_edges:
    #     for pse in projshape_edges:
    #         print("types: {}, {}".format(fe, pse))
    #         # display.DisplayShape([fe, pse])
    #         display.DisplayShape(pse, update=True, color="BLACK")
    #         display.DisplayShape(fe, update=True, color="WHITE")
    #         dss = BRepExtrema_DistShapeShape()
    #         # d = fe.closest(pse)
    #         dss.LoadS1(fe)
    #         dss.LoadS2(pse)
    #         dss.Perform()
    #         break
    #         # assert dss.IsDone()
    #         # print(dss.Value())
    #     break






    # exp = TopologyExplorer(letter)
    # # for edge in exp.edges():
    # #     display.DisplayShape(edge, update=True, color=next(colors))
    # for face in exp.faces():
    #     display.DisplayShape(face, update=True, color=next(colors))
    #
    #     foo = BRepGProp_Face(face)
    #     normal_point = gp_Pnt(0, 0, 0)
    #     normal_vec = gp_Vec(0, 0, 0)
    #     # TODO: how to get middle of face with UV mapping?
    #     foo.Normal(0, 0, normal_point, normal_vec)
    #     # display.DisplayShape(normal_point, update=True, color="BLACK")
    #     normal_vec.Reverse()
    #     # normal_extrusion = make_extrusion(face, 2*height_mm, normal_vec)
    #     # display.DisplayShape(normal_extrusion, update=True, color="BLACK")
    #     # letter = BRepAlgoAPI_Cut(letter, normal_extrusion).Shape()
    #
    #     normal_extrusion = make_extrusion(face, 2*height_mm, normal_vec)
    #     # display.DisplayShape(normal_extrusion, update=True, color="BLACK")
    #     letter = BRepAlgoAPI_Cut(letter, normal_extrusion).Shape()
    #
    #     algo = HLRBRep_Algo()
    #     algo.Add(letter)
    #     projector = Prs3d_Projector(False, 0, 0, 0, 5, 0, 0, 1, 0, 1, 0)
    #     algo.Projector(projector.Projector())
    #     algo.Update()
    #     foobar = HLRBRep_HLRToShape(algo)
    #     print(type(foobar))
    #     shape = None
    #     foobar.HCompound(shape)
    #     print(shape)
    #     proj_shape = AIS_Shape(foobar.HCompound())
    #     # display.DisplayShape(foobar.HCompound, update=True, color="CYAN")
    #
    #     # print(normal_point)
    #     # display.DisplayShape(v, update=True, color="BLACK")
    #     # print(normal_vec)
    #
    #     # print(face.normalAt(0, 0))
    #     # face
    #     break
    # display.DisplayShape(letter, update=True, color="BLACK")

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
    print(args)

    main(args.words[0], args.words[1], args.height, args.output_dir)
