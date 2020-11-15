from OCC.Display.SimpleGui import init_display
from OCC.Extend.ShapeFactory import *
from face_factory import FaceFactory
from OCC.Core.BRepAlgoAPI import *
from OCC.Core.gp import *
from constants import *
import math

def combine_faces(face1, face2):
    # assuming both faces start in the XZ plane

    tf = gp_Trsf()
    # rotate from the XZ plane to the YZ plane
    tf.SetRotation(gp_Ax1(ORIGIN, DIR_Z), math.pi / 2)
    face2 = BRepBuilderAPI_Transform(face2, tf).Shape()

    face1_extruded = make_extrusion(face1, 100, gp_Vec(0, 1, 0))
    face2_extruded = make_extrusion(face2, 100, gp_Vec(1, 0, 0))
    common = BRepAlgoAPI_Common(face1_extruded, face2_extruded)

    return common.Shape()

def create_word(word1, word2):
    assert len(word1) == len(word2)
    combined_letters = []
    for letter1, letter2 in zip(word1, word2):
        face1 = FaceFactory.create_letter(letter1)
        face2 = FaceFactory.create_letter(letter2)
        combined_letter = combine_faces(face1, face2)
        combined_letters.append(combined_letter)

    tf = gp_Trsf()
    p1 = ORIGIN
    x = 0
    new_letters = []
    for l in combined_letters:
        p2 = gp_Pnt(x, x, 0)
        tf.SetTranslation(p1, p2)
        new_letters.append(BRepBuilderAPI_Transform(l, tf).Shape())
        x += 12

    return new_letters

def main():
    display, start_display, add_menu, add_function_to_menu = init_display()
    # Read keyboard input
    word1 = 'IE'
    word2 = 'FT'

    letters = create_word(word1, word2)
    for l in letters:
        display.DisplayColoredShape(l, update=True, color="WHITE")

    # Create faces
    # face_1 = FaceFactory.create_letter(letter_1)
    # face_2 = FaceFactory.create_letter(letter_2)

    # display.DisplayShape(face_2, update=True, color="BLUE")
    # start_display()
    # return

    # Create combined letter shape
    # shape = combine_faces(face_1, face_2)

    # Display final result

    display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
    display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
    display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")

    # display.DisplayColoredShape(shape, update=True, color="WHITE")

    start_display()

    # TODO: output to STL


if __name__ == '__main__':
    main()