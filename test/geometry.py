import unittest
from tft.geometry import Point
import numpy as np

class TestPoint(unittest.TestCase):
    def test_getters_from_constructor(self):
        p = Point(1, -3, 0.025)
        self.assertEqual(1, p.x())
        self.assertEqual(-3, p.y())
        self.assertEqual(0.025, p.z())
        self.assertEqual(np.array([1, -3, 0.025]), p.coords())

    def test_getters_from_array(self):
        p = Point.fromArray([-0.5, 0, 50])
        self.assertEqual(-0.5, p.x())
        self.assertEqual(0, p.y())
        self.assertEqual(50, p.z())
        self.assertEqual(np.array([-0.5, 0, 50]), p.coords())

    def test_addition(self):
        p1 = Point(1, 2, 3)
        p2 = Point(-3, 2, 0)
        expected = Point(-2, 4, 3)
        self.assertEqual(expected, p1 + p2)


if __name__ == '__main__':
    unittest.main()