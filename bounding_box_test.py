import unittest
import math

from bounding_box import BoundingBox


class BoundingBoxTest(unittest.TestCase):
    def test_distance_only_x_different(self):
        a = BoundingBox(0, 0, 0, 10, 10, 10)
        b = BoundingBox(23, 0, 0, 33, 10, 10)
        self.assertEqual(13, a.dist(b))
        self.assertEqual(a.dist(b), b.dist(a))

    def test_distance_only_xy_different(self):
        a = BoundingBox(0, 0, 0, 10, 10, 10)
        b = BoundingBox(23, 5, 0, 33, 15, 10)
        self.assertEqual(13, a.dist(b))
        self.assertEqual(a.dist(b), b.dist(a))

    def test_distance_no_overlap(self):
        a = BoundingBox(0, 0, 0, 10, 10, 10)
        b = BoundingBox(23, 5, -50, 33, 15, -30)
        self.assertEqual(math.sqrt(1069), a.dist(b))
        self.assertEqual(a.dist(b), b.dist(a))

    def test_distance_with_overlap(self):
        a = BoundingBox(0, 0, 0, 10, 10, 10)
        b = BoundingBox(2, 5, 8.8, 33, 15, 30)
        self.assertEqual(0, a.dist(b))

    def test_overlaps_no_overlap(self):
        a = BoundingBox(0, 0, 0, 10, 10, 10)
        b = BoundingBox(20, 20, 20, 30, 30, 30)
        self.assertFalse(a.overlaps(b))
        self.assertEqual(a.overlaps(b), b.overlaps(a))

    def test_overlaps_xy_overlap(self):
        a = BoundingBox(0, 0, 0, 10, 10, 10)
        b = BoundingBox(5, 8, 20, 30, 30, 30)
        self.assertTrue(a.overlaps(b))
        self.assertEqual(a.overlaps(b), b.overlaps(a))

        a = BoundingBox(0, 0, 0, 10, 10, 10)
        b = BoundingBox(11, 8, 20, 30, 30, 30)
        self.assertFalse(a.overlaps(b))
        self.assertEqual(a.overlaps(b), b.overlaps(a))

    def test_overlaps_xz_overlap(self):
        a = BoundingBox(0, 0, 0, 10, 10, 10)
        b = BoundingBox(5, 15, 9.5, 30, 30, 30)
        self.assertTrue(a.overlaps(b))
        self.assertEqual(a.overlaps(b), b.overlaps(a))

        a = BoundingBox(0, 0, 0, 10, 10, 10)
        b = BoundingBox(11, 15, 9.5, 30, 30, 30)
        self.assertFalse(a.overlaps(b))
        self.assertEqual(a.overlaps(b), b.overlaps(a))

    def test_overlaps_boxes_intersecting(self):
        a = BoundingBox(0, 0, 0, 10, 10, 10)
        b = BoundingBox(5, 4, 6, 30, 30, 30)
        self.assertTrue(a.overlaps(b))
        self.assertEqual(a.overlaps(b), b.overlaps(a))

    def test_overlaps_boxes_threshold(self):
        a = BoundingBox(0, 0, 0, 10, 10, 10)
        b = BoundingBox(9, 9, 9, 30, 30, 30)
        self.assertFalse(a.overlaps(b, threshold=5))


if __name__ == '__main__':
    unittest.main()
