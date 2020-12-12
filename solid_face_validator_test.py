import unittest
import pathlib
from OCCUtils.Common import random_color
from OCC.Display.SimpleGui import init_display
from constants import LINE_X, LINE_Y, LINE_Z
from OCC.Extend.ShapeFactory import make_edge
from face_factory import FaceFactory
from util import *
from main import combine_faces
from solid_face_validator import SolidFaceValidator

import logging
# logging.getLogger("OCCUtils").setLevel(logging.ERROR)
# logging.getLogger("OCCUtils.Common").setLevel(logging.ERROR)
# logging.getLogger("OCCUtils.solid").setLevel(logging.ERROR)
# logging.getLogger("OCCUtils.base").setLevel(logging.ERROR)
# logging.getLogger("GlobalProperties").setLevel(logging.ERROR)
# logging.getLogger("Solid").setLevel(logging.ERROR)
logging.getLogger("shapely").setLevel(logging.ERROR)
logging.getLogger("shapely.geos").setLevel(logging.ERROR)
logging.getLogger("shapely.geometry.base").setLevel(logging.ERROR)
logging.getLogger("shapely.geometry").setLevel(logging.ERROR)
logging.getLogger("shapely.speedups._speedups").setLevel(logging.ERROR)
logging.getLogger("shapely.speedups").setLevel(logging.ERROR)


loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
logger_names = [name for name in logging.root.manager.loggerDict]
try:
    logger_names.remove("TFT")
except ValueError:
    pass
for name in logger_names:
    # print(name)
    logging.getLogger(name).setLevel(logging.WARNING)
print("LOGGERS:")
print('\n'.join(logger_names))


display, start_display, add_menu, add_function_to_menu = init_display()

class TestSolidFaceValidator(unittest.TestCase):
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

    def test_iteratively_generate_lines_for_face_HE_XZ_plane(self):
        lines = SolidFaceValidator.iteratively_generate_lines_for_face(self.compound_HE, PL_XZ, 100)

        display.DisplayShape(self.compound_HE, transparency=0.8)
        for l in lines:
            display.DisplayShape(make_edge(l), color="RED")
        print("num lines: {}".format(len(lines)))
        start_display()

    def test_iteratively_generate_lines_for_face_HE_YZ_plane(self):
        lines = SolidFaceValidator.iteratively_generate_lines_for_face(self.compound_HE, PL_YZ, 100)

        display.DisplayShape(self.compound_HE, transparency=0.8)
        for l in lines:
            display.DisplayShape(make_edge(l), color="RED")
        print("num lines: {}".format(len(lines)))
        start_display()

    def test_iteratively_generate_lines_for_face_GE_XZ_plane(self):
        lines = SolidFaceValidator.iteratively_generate_lines_for_face(self.compound_GE, PL_XZ, 100)

        display.DisplayShape(self.compound_GE, transparency=0.8)
        for l in lines:
            display.DisplayShape(make_edge(l), color="RED")
        print("num lines: {}".format(len(lines)))
        start_display()

    def test_iteratively_generate_lines_for_face_Q4_XZ_plane(self):
        lines = SolidFaceValidator.iteratively_generate_lines_for_face(self.compound_Q4, PL_XZ, 100)

        display.DisplayShape(self.compound_Q4, transparency=0.8)
        for l in lines:
            display.DisplayShape(make_edge(l), color="RED")
        print("num lines: {}".format(len(lines)))
        start_display()

    def test_generate_lines_for_face_HE_XZ_plane(self):
        lines = SolidFaceValidator.generate_lines_for_face(self.compound_HE, PL_XZ)

        display.DisplayShape(self.compound_HE, transparency=0.8)
        for l in lines:
            display.DisplayShape(make_edge(l), color="RED")
        print("num lines: {}".format(len(lines)))
        start_display()

    def test_generate_lines_for_face_HE_YZ_plane(self):
        lines = SolidFaceValidator.generate_lines_for_face(self.compound_HE, PL_YZ)

        display.DisplayShape(self.compound_HE, transparency=0.8)
        for l in lines:
            display.DisplayShape(make_edge(l), color="RED")
        print("num lines: {}".format(len(lines)))
        start_display()

    def test_generate_lines_for_face_GE_XZ_plane(self):
        lines = SolidFaceValidator.generate_lines_for_face(self.compound_GE, PL_XZ)

        display.DisplayShape(self.compound_GE, transparency=0.8)
        for l in lines:
            display.DisplayShape(make_edge(l), color="RED")
        print("num lines: {}".format(len(lines)))
        start_display()

    def test_generate_lines_for_face_Q4_XZ_plane(self):
        lines = SolidFaceValidator.generate_lines_for_face(self.compound_Q4, PL_XZ)

        display.DisplayShape(self.compound_Q4, transparency=0.8)
        for l in lines:
            display.DisplayShape(make_edge(l), color="RED")
        print("num lines: {}".format(len(lines)))
        start_display()

    def test_is_valid_default_HE(self):
        validator = SolidFaceValidator(self.compound_HE)
        import time
        start = time.time()
        self.assertTrue(validator.is_valid(self.compound_HE))
        end = time.time()
        print("time: ", end-start)

    def test_is_valid_default_GE(self):
        validator = SolidFaceValidator(self.compound_GE)
        self.assertTrue(validator.is_valid(self.compound_GE))

    def test_is_valid_default_VT(self):
        validator = SolidFaceValidator(self.compound_VT)
        self.assertTrue(validator.is_valid(self.compound_VT))

    def test_is_valid_default_Q4(self):
        validator = SolidFaceValidator(self.compound_Q4)
        self.assertTrue(validator.is_valid(self.compound_Q4))


if __name__ == '__main__':
    unittest.main()

