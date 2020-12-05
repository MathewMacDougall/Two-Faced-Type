import unittest
import pathlib
from main import extrude_and_clamp, combine_words, project_and_clamp, make_bounding_box
from OCC.Display.SimpleGui import init_display
from face_factory import FaceFactory
from OCC.Core.gp import gp_Vec
from OCC.Core.TopoDS import TopoDS_Compound

display, start_display, add_menu, add_function_to_menu = init_display()

class TestProjectAndClamp(unittest.TestCase):
    def test_project_and_clamp_normal(self):
        face_images_dir = pathlib.Path(__file__).parent / "test_data"
        face_factory = FaceFactory(face_images_dir)
        height = 50
        letters, face1, face2 = combine_words("H", "E", face_factory, height)
        self.assertEqual(1, len(letters))

        compound = letters[0]
        containing_box = make_bounding_box(compound)
        vec = gp_Vec(0, 1, 0)

        result = project_and_clamp(letters[0], vec, containing_box, height)
        display.DisplayShape(result)
        start_display()
        print(result)

    def test_project_and_clamp_recovery(self):
        face_images_dir = pathlib.Path(__file__).parent / "test_data"
        face_factory = FaceFactory(face_images_dir)
        height = 40
        letters, face1, face2 = combine_words("G", "E", face_factory, height)
        self.assertEqual(1, len(letters))

        compound = letters[0]
        containing_box = make_bounding_box(compound)
        vec = gp_Vec(-1, 0, 0)

        with self.assertLogs('TFT', level='INFO') as cm:
            result = project_and_clamp(letters[0], vec, containing_box, height)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, TopoDS_Compound)
        self.assertIn('WARNING:TFT:Failed fuses: 2', cm.output)
        self.assertIn('WARNING:TFT:Recovered fuses: 2', cm.output)
        self.assertIn('WARNING:TFT:Doubly-failed fuses: 0', cm.output)
        # display.DisplayShape(result)
        # start_display()
        # print(result)



if __name__ == '__main__':
    unittest.main()

