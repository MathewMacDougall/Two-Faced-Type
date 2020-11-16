from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace
from OCC.Core.gp import gp_Pnt
from OCC.Extend.ShapeFactory import make_face
from PIL import Image
import numpy as np
from pathlib import Path
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from functools import reduce


class FaceFactory():
    @classmethod
    def _get_create_gp_pnt_func(cls):
        # for now assume everything is in the XZ plane. We can rotate one
        # of the faces when we go to combine them
        return lambda x: gp_Pnt(x[0], 0, x[1])

    @classmethod
    def make_rect(cls, coord, size):
        assert size > 0

        poly = BRepBuilderAPI_MakePolygon()
        vertices = [
            (coord[0] * size, coord[1] * size),
            (coord[0] * size, coord[1] * size + size),
            (coord[0] * size + size, coord[1] * size + size),
            (coord[0] * size + size, coord[1] * size),
        ]
        create_gp_pnt = cls._get_create_gp_pnt_func()
        for v in vertices:
            poly.Add(create_gp_pnt(v))
        poly.Close()
        return poly.Wire()

    @classmethod
    def create_from_image(cls, filepath, height_mm):
        assert isinstance(filepath, Path)
        if not filepath.is_file():
            raise IOError("Unable to create Face from image file: {}. File does not exist".format(filepath))

        # Combining wires didn't work as expected. It left some "pixels" with
        # weird artifacts and wouldn't quite create a contiguous face (some triangles
        # would be missing from pixels).
        # Combining faces seems to work much better, and even allows for non-contiguous
        # shapes (although this won't look good in the final product)

        im_frame = Image.open(filepath)
        np_frame = np.array(im_frame)
        pixel_size = height_mm / np_frame.shape[0]
        faces = []
        for z, row in enumerate(reversed(np_frame)):
            for x, col in enumerate(row):
                if col[0] < 1:
                    # fill in the pixel
                    faces.append(make_face(cls.make_rect((x, z), pixel_size)))

        fuse_faces = lambda f1, f2: BRepAlgoAPI_Fuse(f1, f2).Shape()
        fused = reduce(fuse_faces, faces, faces[0])
        return fused

    @classmethod
    def create_char(cls, char, height_mm):
        if not char.isalpha():
            raise ValueError("Unable to create face from char. Only alphanumeric characters are supported")

        char = char.upper()

        face_images_dir = Path(__file__).parent / "face_images"

        assert face_images_dir.is_dir()
        char_image_file = face_images_dir / "{}.png".format(char)
        assert char_image_file.is_file()
        return cls.create_from_image(char_image_file, height_mm)
