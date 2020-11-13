import unittest
from tft.letter import Letter
from tft.geometry import Point, polylines, Segment, Plane


class TestLetterZValues(unittest.TestCase):
    def test_letter_I_in_YZ_plane(self):
        LINES_I = polylines(
            Point(5, 0),
            Point(5, 10),
        )
        letter = Letter(LINES_I, Plane.YZ)

        z_values = letter.vertex_z_values()
        expected = {0, 10}
        self.assertEqual(expected, z_values)

    def test_letter_I_in_XZ_plane(self):
        LINES_I = polylines(
            Point(5, 0),
            Point(5, 10),
        )
        letter = Letter(LINES_I, Plane.XZ)

        z_values = letter.vertex_z_values()
        expected = {0, 10}
        self.assertEqual(expected, z_values)

    def test_letter_T_in_YZ_plane(self):
        LINES_T = [
            Segment(Point(5, 0), Point(5, 10)),
            Segment(Point(0, 10), Point(10, 10)),
        ]
        letter = Letter(LINES_T, Plane.YZ)

        z_values = letter.vertex_z_values()
        expected = {0, 10}
        self.assertEqual(expected, z_values)


if __name__ == '__main__':
    unittest.main()
