import unittest
from solid import Solid
from unittest.mock import MagicMock
import pathlib
from OCC.Display.SimpleGui import init_display
from OCC.Extend.ShapeFactory import make_edge
from OCCUtils.Common import random_color

from face_factory import FaceFactory
from util import *
from combiner import combine_faces
from solid_face_validator import SolidFaceValidator

display, start_display, _, _ = init_display()
# display, start_display, _, _ = MagicMock(), MagicMock(), None, None


class SolidTest(unittest.TestCase):
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

    def test_equality(self):
        solid = Solid(split_compound(self.compound_HE)[0])
        self.assertEqual(solid, solid)

    def test_equality_deep_copy(self):
        solid = Solid(split_compound(self.compound_HE)[0])
        self.assertEqual(solid, copy.deepcopy(solid))

    def test_hash_equality(self):
        solid = Solid(split_compound(self.compound_HE)[0])
        self.assertEqual(solid.__hash__(), copy.deepcopy(solid).__hash__())


if __name__ == '__main__':
    unittest.main()
