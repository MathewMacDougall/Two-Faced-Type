import unittest
import pathlib
from constants import LINE_Z, LINE_Y, LINE_X
from OCC.Extend.ShapeFactory import make_edge
from redundant_geom_line import *
from util import *
from OCC.Display.SimpleGui import init_display
from face_factory import FaceFactory
from OCC.Core.gp import gp_Vec
from OCC.Core.TopoDS import TopoDS_Compound
from main import combine_faces

display, start_display, add_menu, add_function_to_menu = init_display()

class TestRemoveRedundantGeom(unittest.TestCase):
    def setUp(self):
        face_images_dir = pathlib.Path(__file__).parent / "test_data"
        face_factory = FaceFactory(face_images_dir)
        self.height_mm = 40
        self.face_H = face_factory.create_char('H', self.height_mm)
        self.face_E = face_factory.create_char('E', self.height_mm)
        self.face_G = face_factory.create_char('G', self.height_mm)
        self.face_V = face_factory.create_char('V', self.height_mm)
        self.face_T = face_factory.create_char('T', self.height_mm)
        self.compound_HE = combine_faces(self.face_H, self.face_E, self.height_mm)
        self.compound_GE = combine_faces(self.face_G, self.face_E, self.height_mm)
        self.compound_VT = combine_faces(self.face_V, self.face_T, self.height_mm)

    def test_get_point_on_all_faces(self):
        all_faces = get_faces(self.compound_HE)
        points = get_point_on_all_faces(all_faces)
        self.assertEqual(len(all_faces), len(points))

        # display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
        # display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
        # display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")
        # for p in points:
        #     display.DisplayShape(p)
        # start_display()

    def test_get_point_on_all_faces_with_plane(self):
        all_faces = get_faces(self.compound_HE)
        points = get_point_on_all_faces_with_plane(all_faces, PL_XZ, gp_Vec(0, -50, 0))
        self.assertEqual(len(all_faces), len(points))

        # display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
        # display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
        # display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")
        # for p in points:
        #     display.DisplayShape(p)
        # start_display()

    def test_get_lines_through_all_faces(self):
        all_faces = get_faces(self.compound_HE)
        lines = get_lines_through_all_faces(all_faces, PL_XZ)
        self.assertEqual(len(all_faces), len(lines))

        display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
        display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
        display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")
        for l in lines:
            display.DisplayShape(make_edge(l))
        start_display()

    def test_line_face_intersection(self):
        line = gp_Lin(gp_Pnt(-5, 0, -100), gp_Dir(gp_Vec(0,1,0)))
        face = self.face_H
        print(Face(face).domain())
        result = get_line_face_intersection(line, face)
        # self.assertEqual((5, 5, 0), result)

    def test_solid_line_intersection(self):
        line = gp_Lin(gp_Pnt(1, 0, 1), gp_Dir(gp_Vec(0,1,0)))
        compound = self.compound_HE
        result = get_shape_line_intersections(compound, line)
        for p, f in result:
            display.DisplayShape(p)
            display.DisplayShape(f, transparency=0.7)
        start_display()
        # self.assertEqual((5, 5, 0), result)


    def test_remove_geom_HE_H_face(self):
        result = remove_redundant_geometry_lines(self.compound_HE, self.height_mm, display)

        display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
        display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
        display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")
        display.DisplayShape(result, color="BLUE", transparency=0.7)
        # display.DisplayShape(self.compound_HE, color="BLUE", transparency=0.7)
        start_display()



if __name__ == '__main__':
    unittest.main()

