import unittest
from unittest.mock import MagicMock
import pathlib
from OCC.Display.SimpleGui import init_display
from OCC.Extend.ShapeFactory import make_edge
from OCCUtils.Common import random_color

from face_factory import FaceFactory
from util import *
from solid import Solid
from combiner import combine_faces
from solid_face_validator import SolidFaceValidator

# display, start_display, _, _ = init_display()
display, start_display, _, _ = MagicMock(), MagicMock(), None, None

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

    def test_generate_intersections_for_face_HE_XZ_plane(self):
        all_solids = split_compound(self.compound_HE)
        intersections = SolidFaceValidator.get_intersections_for_face(all_solids, PL_XZ)

        self.assertEqual(len(intersections), len(all_solids))
        all_intersected_solids = list({s for inter in intersections for s in inter})
        expected_all_intersected_solids = [Solid(s) for s in all_solids]
        self.assertCountEqual(expected_all_intersected_solids, all_intersected_solids)


    def test_generate_lines_for_face_HE_YZ_plane(self):
        all_solids = split_compound(self.compound_HE)
        intersections = SolidFaceValidator.get_intersections_for_face(all_solids, PL_YZ)

        self.assertEqual(len(intersections), len(all_solids))
        all_intersected_solids = list({s for inter in intersections for s in inter})
        expected_all_intersected_solids = [Solid(s) for s in all_solids]
        self.assertCountEqual(expected_all_intersected_solids, all_intersected_solids)

    def test_generate_lines_for_face_GE_XZ_plane(self):
        all_solids = split_compound(self.compound_GE)
        intersections = SolidFaceValidator.get_intersections_for_face(all_solids, PL_XZ)

        self.assertEqual(len(intersections), len(all_solids))
        all_intersected_solids = list({s for inter in intersections for s in inter})
        expected_all_intersected_solids = [Solid(s) for s in all_solids]
        self.assertCountEqual(expected_all_intersected_solids, all_intersected_solids)

    def test_generate_lines_for_face_Q4_XZ_plane(self):
        all_solids = split_compound(self.compound_Q4)
        intersections = SolidFaceValidator.get_intersections_for_face(all_solids, PL_XZ)

        self.assertEqual(len(intersections), len(all_solids))
        all_intersected_solids = list({s for inter in intersections for s in inter})
        expected_all_intersected_solids = [Solid(s) for s in all_solids]
        self.assertCountEqual(expected_all_intersected_solids, all_intersected_solids)

    def test_is_valid_HE_with_nonredundant_solid_removed(self):
        validator = SolidFaceValidator(self.compound_HE)
        # Bottom-right "leg" of the H. If removed the H will be invalid
        solid = split_compound(self.compound_HE)[7]
        self.assertFalse(validator.remove_if_valid(solid))

    def test_is_valid_HE_with_redundant_solid_removed(self):
        validator = SolidFaceValidator(self.compound_HE)
        # Top-right corner H
        solid = split_compound(self.compound_HE)[0]
        display.DisplayShape(solid)
        self.assertTrue(validator.remove_if_valid(solid))


if __name__ == '__main__':
    unittest.main()

