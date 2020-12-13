import unittest
from unittest.mock import MagicMock

from stl import read_stl, write_stl
import pathlib
from face_factory import FaceFactory
from util import *
from geom_removal import remove_redundant_geometry
from combiner import combine_words
from OCC.Display.SimpleGui import init_display
from OCCUtils.Common import GpropsFromShape

# display, start_display, _, _ = init_display()
display, start_display, _, _ = MagicMock(), MagicMock(), None, None


class TestSolidFaceValidator(unittest.TestCase):
    def setUp(self):
        face_images_dir = pathlib.Path(__file__).parent / "face_images/aldrich"
        self.face_factory = FaceFactory(face_images_dir)
        self.height_mm = 50
        self.test_data_dir = pathlib.Path(__file__).parent / "test_data"
        assert self.test_data_dir.is_dir()

    def assert_mass_eq(self, letter, golden):
        letter_props = GpropsFromShape(letter)
        letter_mass = letter_props.volume().Mass()

        golden_props = GpropsFromShape(golden)
        golden_mass = golden_props.volume().Mass()

        self.assertAlmostEqual(letter_mass, golden_mass, delta=0.1)

    def assert_center_of_mass_eq(self, letter, golden):
        letter_props = GpropsFromShape(letter)
        letter_com = letter_props.volume().CentreOfMass()

        golden_props = GpropsFromShape(golden)
        golden_com = golden_props.volume().CentreOfMass()

        self.assertLess(distance(letter_com, golden_com), 0.01)

    # TODO: Disabled for now because getting negative mass. Need to find a better way to load and
    # compare shapes
    def test_HE(self):
        return
        letters, faces1, faces2 = combine_words("H", "E", self.face_factory, self.height_mm)
        letters = remove_redundant_geometry(letters)
        letter = remove_redundant_geometry(letters)[0]

        golden_file = self.test_data_dir / "HE.stl"
        golden_stl = read_stl(golden_file)

        # TODO: Why is this needed to write files?
        # display.DisplayShape(letter)
        # start_display()
        # write_stl(letter, golden_file)

        # self.assert_mass_eq(letter, golden_stl)
        # self.assert_center_of_mass_eq(letter, golden_stl)

    # TODO: Disabled for now because getting negative mass. Need to find a better way to load and
    # compare shapes
    def test_VT(self):
        return
        letters, faces1, faces2 = combine_words("V", "T", self.face_factory, self.height_mm)
        letters = remove_redundant_geometry(letters)
        letter = remove_redundant_geometry(letters)[0]

        golden_file = self.test_data_dir / "VT.stl"
        golden_stl = read_stl(golden_file)

        # TODO: Why is this needed to write files?
        # display.DisplayShape(letter)
        # start_display()
        # write_stl(letter, golden_file)

        self.assert_mass_eq(letter, golden_stl)
        self.assert_center_of_mass_eq(letter, golden_stl)
