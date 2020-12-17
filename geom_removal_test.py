import unittest
from unittest.mock import MagicMock
import pathlib
from face_factory import FaceFactory
from combiner import combine_faces
from geom_removal import *
from OCCUtils.Common import random_color, color
from OCC.Display.SimpleGui import init_display

display, start_display, _, _ = init_display()
# display, start_display, _, _ = MagicMock(), MagicMock(), None, None

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
        self.face_L = face_factory.create_char('L', height_mm)
        self.face_N = face_factory.create_char('N', height_mm)
        self.compound_HE = combine_faces(self.face_H, self.face_E, height_mm)
        self.compound_GE = combine_faces(self.face_G, self.face_E, height_mm)
        self.compound_VT = combine_faces(self.face_V, self.face_T, height_mm)
        self.compound_Q4 = combine_faces(self.face_Q, self.face_4, height_mm)
        self.compound_NL = combine_faces(self.face_N, self.face_L, height_mm)

    def test_order_of_removal(self):
        all_solids = split_compound(self.compound_HE)
        graph = create_solid_graph(all_solids)

        props = GlobalProperties(self.compound_HE)
        x1, y1, z1, x2, y2, z2 = props.bbox()

        corner = Point(x2, y1, z2)
        vertices = list(graph.all_vertices())
        vertices.sort(key=lambda x: x.bbox().max_dist_to_point(corner))

        for index, r in enumerate(vertices):
            val = index / len(vertices)
            col = color(val, 1-val, 0)
            display.DisplayShape(r.solid(), color=col)

        display.FitAll()
        start_display()

    def test_node_equality_same_node(self):
        all_solids = split_compound(self.compound_HE)[:1]
        node = Node(all_solids[0])
        self.assertEqual(node, node)

    def test_node_equality_deep_copy(self):
        all_solids = split_compound(self.compound_HE)[:1]
        node = Node(all_solids[0])
        self.assertEqual(node, copy.deepcopy(node))

    def test_nodes_can_be_removed_from_graph(self):
        all_solids = split_compound(self.compound_HE)[:1]
        graph = create_solid_graph(all_solids)
        self.assertEqual(1, len(graph.all_vertices()))
        nodes = graph.all_vertices()
        node_to_remove = copy.deepcopy(nodes.pop())
        graph.remove_vertex(node_to_remove)
        self.assertEqual(0, len(graph.all_vertices()))

    def test_nodes_can_be_removed_from_graph_2(self):
        all_solids = split_compound(self.compound_HE)
        graph = create_solid_graph(all_solids)
        self.assertEqual(22, len(graph.all_vertices()))
        while graph.all_vertices():
            graph.remove_vertex(copy.deepcopy(graph.all_vertices().pop()))
        self.assertEqual(0, len(graph.all_vertices()))

    def test_remove_geom_HE(self):
        result = remove_redundant_geom(self.compound_HE)
        display.DisplayShape(self.compound_HE, color="WHITE", transparency=0.7)
        display.DisplayShape(result)

        display.FitAll()
        start_display()

    def test_remove_geom_VT(self):
        result = remove_redundant_geom(self.compound_VT)
        display.DisplayShape(self.compound_VT, color="WHITE", transparency=0.7)
        display.DisplayShape(result)

        display.FitAll()
        start_display()

    def test_remove_geom_GE(self):
        result = remove_redundant_geom(self.compound_GE)
        display.DisplayShape(self.compound_GE, color="WHITE", transparency=0.7)
        display.DisplayShape(result)

        display.FitAll()
        start_display()

    def test_remove_geom_NL(self):
        result = remove_redundant_geom(self.compound_NL)
        display.DisplayShape(self.compound_NL, color="WHITE", transparency=0.7)
        display.DisplayShape(result)

        display.FitAll()
        start_display()


if __name__ == '__main__':
    unittest.main()

