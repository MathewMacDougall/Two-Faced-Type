import unittest
import pathlib
from constants import LINE_Z, LINE_Y, LINE_X
from OCC.Extend.ShapeFactory import make_edge
from redundant_geom_solid_diff import extrude_and_clamp, project_and_clamp, make_bounding_box, remove_redundant_geometry_solid_diff
from OCC.Display.SimpleGui import init_display
from face_factory import FaceFactory
from OCC.Core.gp import gp_Vec
from OCC.Core.TopoDS import TopoDS_Compound
from main import combine_faces

display, start_display, add_menu, add_function_to_menu = init_display()

class TestProjectAndClamp(unittest.TestCase):
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

    def test_project_and_clamp_normal(self):
        containing_box = make_bounding_box(self.compound_HE)
        vec = gp_Vec(0, 1, 0)

        result = project_and_clamp(self.compound_HE, vec, containing_box, self.height_mm)
        display.DisplayShape(result)
        start_display()
        print(result)

    def test_project_and_clamp_recovery(self):
        containing_box = make_bounding_box(self.compound_GE)
        vec = gp_Vec(-1, 0, 0)

        with self.assertLogs('TFT', level='INFO') as cm:
            result = project_and_clamp(self.compound_GE, vec, containing_box, self.height_mm)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, TopoDS_Compound)
        self.assertIn('WARNING:TFT:Failed fuses: 2', cm.output)
        self.assertIn('WARNING:TFT:Recovered fuses: 2', cm.output)
        self.assertIn('WARNING:TFT:Doubly-failed fuses: 0', cm.output)
        # display.DisplayShape(result)
        # start_display()
        # print(result)


    def test_remove_geom_GE_G_face(self):
        result = remove_redundant_geometry_solid_diff(self.compound_GE, self.height_mm)

        display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
        display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
        display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")
        display.DisplayShape(result, color="GREEN")
        start_display()



if __name__ == '__main__':
    unittest.main()

