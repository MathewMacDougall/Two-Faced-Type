from OCC.Display.SimpleGui import init_display
from OCC.Extend.ShapeFactory import *
from face_factory import FaceFactory
from OCC.Core.BRepAlgoAPI import *
from OCC.Core.gp import *
from constants import *
import math
from OCC.Core.StlAPI import StlAPI_Writer
import argparse
from pathlib import Path
import os
import errno


def combine_faces(face1, face2):
    # assuming both faces start in the XZ plane

    tf = gp_Trsf()
    # rotate from the XZ plane to the YZ plane
    tf.SetRotation(gp_Ax1(ORIGIN, DIR_Z), math.pi / 2)
    face2 = BRepBuilderAPI_Transform(face2, tf).Shape()

    # TODO: extrude proporional to pixels and pixel size
    face1_extruded = make_extrusion(face1, 100*10, gp_Vec(0, 1, 0))
    face2_extruded = make_extrusion(face2, 100*10, gp_Vec(1, 0, 0))
    common = BRepAlgoAPI_Common(face1_extruded, face2_extruded)

    return common.Shape()

def combine_words(word1, word2):
    assert len(word1) == len(word2)

    combined_faces = []
    for letter1, letter2 in zip(word1, word2):
        face1 = FaceFactory.create_char(letter1)
        face2 = FaceFactory.create_char(letter2)
        combined_letter = combine_faces(face1, face2)
        combined_faces.append(combined_letter)

    tf = gp_Trsf()
    p1 = ORIGIN
    offset = 0
    offset_letters = []
    for l in combined_faces:
        tf.SetTranslation(p1, gp_Pnt(offset, offset, 0))
        offset_letters.append(BRepBuilderAPI_Transform(l, tf).Shape())
        offset += 12

    return offset_letters

def save_to_stl(shapes, dirpath="/home/mathew/"):
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


def main(word1, word2, output_dir):
    display, start_display, add_menu, add_function_to_menu = init_display()

    # face1 = FaceFactory.create_from_image(Path("/home/mathew/letter_A.png"))
    # face2 = FaceFactory.create_from_image(Path("/home/mathew/letter_H.png"))
    # letters = [combine_faces(face1, face2)]


    # face = FaceFactory.create_from_image(Path("/home/mathew/testimage.png"))
    # # face = FaceFactory.create_letter('C')
    # display.DisplayShape(face, update=True, color="BLUE")
    # face_extruded = make_extrusion(face, 10, gp_Vec(0, 1, 0))
    # display.DisplayShape(face_extruded, update=True, color="BLUE")
    # start_display()
    # return

    display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
    display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
    display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")

    letters = combine_words(word1, word2)

    for l in letters:
        display.DisplayColoredShape(l, update=True, color="WHITE")

    save_to_stl(letters, output_dir)

    start_display()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Combine words into Two-Faced Type, and output as STLs")
    parser.add_argument('words', metavar='word', type=str, nargs=2, help='the words to combine')
    parser.add_argument('-o', '--output_dir', metavar='output_directory', type=str, help="The directory to write STL files to. Will be created if it doesn't exist", required=True)
    args = parser.parse_args()
    print(args)

    main(args.words[0], args.words[1], args.output_dir)