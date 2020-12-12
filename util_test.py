import unittest
import pathlib
from OCCUtils.Common import random_color
from OCC.Display.SimpleGui import init_display
from constants import LINE_X, LINE_Y, LINE_Z
from OCC.Extend.ShapeFactory import make_edge
from face_factory import FaceFactory
from util import *
from main import combine_faces

display, start_display, add_menu, add_function_to_menu = init_display()

class TestUtil(unittest.TestCase):
    def setUp(self):
        face_images_dir = pathlib.Path(__file__).parent / "test_data"
        face_factory = FaceFactory(face_images_dir)
        height_mm = 50
        self.face_H = face_factory.create_char('H', height_mm)
        self.face_E = face_factory.create_char('E', height_mm)
        self.face_G = face_factory.create_char('G', height_mm)
        self.face_V = face_factory.create_char('V', height_mm)
        self.face_T = face_factory.create_char('T', height_mm)
        self.face_Q = face_factory.create_char('Q', height_mm)
        self.face_4 = face_factory.create_char('4', height_mm)
        self.compound_HE = combine_faces(self.face_H, self.face_E, height_mm)
        self.compound_GE = combine_faces(self.face_G, self.face_E, height_mm)
        self.compound_VT = combine_faces(self.face_V, self.face_T, height_mm)
        self.compound_Q4 = combine_faces(self.face_Q, self.face_4, height_mm)

    def test_get_perp_faces_XZ_plane(self):
        perp_faces_HE = get_perp_faces(get_faces(self.compound_HE), gp_Vec(0, 1, 0))
        self.assertEqual(22, len(perp_faces_HE))

        perp_faces_GE = get_perp_faces(get_faces(self.compound_GE), gp_Vec(0, 1, 0))
        self.assertEqual(39, len(perp_faces_GE))

        perp_faces_VT = get_perp_faces(get_faces(self.compound_VT), gp_Vec(0, 1, 0))
        self.assertEqual(11, len(perp_faces_VT))

        # for f in perp_faces_VT:
        #     display.DisplayShape(f, transparency=0.7)
        #
        # display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
        # display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
        # display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")
        # start_display()

    def test_get_perp_faces_YZ_plane(self):
        perp_faces_HE = get_perp_faces(get_faces(self.compound_HE), gp_Vec(1, 0, 0))
        self.assertEqual(26, len(perp_faces_HE))

        perp_faces_GE = get_perp_faces(get_faces(self.compound_GE), gp_Vec(1, 0, 0))
        self.assertEqual(25, len(perp_faces_GE))

        perp_faces_VT = get_perp_faces(get_faces(self.compound_VT), gp_Vec(1, 0, 0))
        self.assertEqual(13, len(perp_faces_VT))

        # for f in perp_faces_VT:
        #     display.DisplayShape(f, transparency=0.7)
        #
        # display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
        # display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
        # display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")
        # start_display()


    def test_get_nonperp_faces_XZ_plane(self):
        nonperp_faces_HE = get_nonperp_faces(get_faces(self.compound_HE), gp_Vec(0, 1, 0))
        self.assertEqual(10, len(nonperp_faces_HE))

        nonperp_faces_GE = get_nonperp_faces(get_faces(self.compound_GE), gp_Vec(0, 1, 0))
        self.assertEqual(9, len(nonperp_faces_GE))

        nonperp_faces_VT = get_nonperp_faces(get_faces(self.compound_VT), gp_Vec(0, 1, 0))
        self.assertEqual(6, len(nonperp_faces_VT))

        # for f in nonperp_faces_VT:
        #     display.DisplayShape(f, transparency=0.7)
        #
        # display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
        # display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
        # display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")
        # start_display()

    def test_get_nonperp_faces_YZ_plane(self):
        nonperp_faces_HE = get_nonperp_faces(get_faces(self.compound_HE), gp_Vec(1, 0, 0))
        self.assertEqual(6, len(nonperp_faces_HE))

        nonperp_faces_GE = get_nonperp_faces(get_faces(self.compound_GE), gp_Vec(1, 0, 0))
        self.assertEqual(23, len(nonperp_faces_GE))

        nonperp_faces_VT = get_nonperp_faces(get_faces(self.compound_VT), gp_Vec(1, 0, 0))
        self.assertEqual(4, len(nonperp_faces_VT))

        # for f in nonperp_faces_GE:
        #     display.DisplayShape(f, transparency=0.7)
        #
        # display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
        # display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
        # display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")
        # start_display()


    def test_split_compound_HE(self):
        result = split_compound(self.compound_HE, display)
        self.assertEqual(22, len(result))

        # Validated visually
        for solid in result:
            display.DisplayShape(solid, color=random_color(), transparency=0.7)

        display.FitAll()
        start_display()


    def test_split_compound_VT(self):
        result = split_compound(self.compound_VT, display)
        self.assertEqual(9, len(result))

        # Validated visually
        for solid in result:
            display.DisplayShape(solid, color=random_color(), transparency=0.7)

        display.FitAll()
        start_display()

    def test_split_compound_GE(self):
        result = split_compound(self.compound_GE, display)
        self.assertEqual(40, len(result))

        # Validated visually
        for solid in result:
            display.DisplayShape(solid, color=random_color(), transparency=0.7)

        display.FitAll()
        start_display()

    def test_split_compound_Q4(self):
        result = split_compound(self.compound_Q4, display)
        self.assertEqual(65, len(result))

        # Validated visually
        for solid in result:
            display.DisplayShape(solid, color=random_color(), transparency=0.7)

        display.FitAll()
        start_display()


if __name__ == '__main__':
    unittest.main()

