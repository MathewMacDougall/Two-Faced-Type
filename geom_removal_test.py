import unittest
import pathlib
from face_factory import FaceFactory
from main import combine_faces
from geom_removal import *
from OCCUtils.Common import random_color, color
from OCC.Display.SimpleGui import init_display
display, start_display, add_menu, add_function_to_menu = init_display()

class TestGeomRemoval(unittest.TestCase):
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

    def test_order_of_removal(self):
        all_solids = split_compound(self.compound_HE)
        graph = create_solid_graph(all_solids)

        props = GlobalProperties(self.compound_HE)
        x1, y1, z1, x2, y2, z2 = props.bbox()

        corner = Point(x2, y1, z2)
        vertices = graph.all_vertices()
        vertices.sort(key=lambda x: x.bbox().max_dist_to_point(corner))

        for index, r in enumerate(vertices):
            val = index / len(vertices)
            col = color(val, 1-val, 0)
            display.DisplayShape(r.solid(), color=col)

        display.FitAll()
        start_display()

    def test_remove_geom_HE(self):
        result = remove_redundant_geom(self.compound_HE)
        for index, r in enumerate(result):
            val = index / len(result)
            col = color(val, 1-val, 0)
            display.DisplayShape(r.solid(), color=col)

        display.FitAll()
        start_display()






if __name__ == '__main__':
    unittest.main()

