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
    def create_from_image(cls, filepath):
        assert isinstance(filepath, Path)
        assert filepath.exists() and filepath.is_file()

        # Combining wires didn't work as expected. It left some "pixels" with
        # weird artifacts and wouldn't quite create a contiguous face (some triangles
        # would be missing from pixels).
        # Combining faces seems to work much better, and even allows for non-contiguous
        # shapes (although this won't look good in the final product)

        im_frame = Image.open(filepath)
        np_frame = np.array(im_frame)
        pixel_size = 10
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
    def create_letter(cls, char):
        assert char.isalpha()
        char = char.upper()

        if char == 'T':
            return cls._create_letter_T()
        elif char == 'I':
            return cls._create_letter_I()
        elif char == 'V':
            return cls._create_letter_V()
        elif char == 'S':
            return cls._create_letter_S()
        elif char == 'C':
            return cls._create_letter_C()
        elif char == 'E':
            return cls._create_letter_E()
        elif char == 'F':
            return cls._create_letter_F()
        else:
            raise RuntimeError("Unsupported character")

    @classmethod
    def _get_create_gp_pnt_func(cls):
        # for now assume everything is in the XZ plane. We can rotate one
        # of the faces when we go to combine them
        return lambda x: gp_Pnt(x[0], 0, x[1])

    @classmethod
    def _create_letter_T(cls):
        poly = BRepBuilderAPI_MakePolygon()
        vertices = [
            (0, 10),
            (10, 10),
            (10, 8.5),
            (5.5, 8.5),
            (5.5, 0),
            (4.5, 0),
            (4.5, 8.5),
            (0, 8.5),
        ]
        create_gp_pnt = cls._get_create_gp_pnt_func()
        for v in vertices:
            poly.Add(create_gp_pnt(v))
        poly.Close()

        return make_face(poly.Wire())

    @classmethod
    def _create_letter_I(cls):
        poly = BRepBuilderAPI_MakePolygon()
        vertices = [
            (0, 10),
            (10, 10),
            (10, 8.5),
            (5.5, 8.5),
            (5.5, 1.5),
            (10, 1.5),
            (10, 0),
            (0, 0),
            (0, 1.5),
            (4.5, 1.5),
            (4.5, 8.5),
            (0, 8.5),
        ]
        create_gp_pnt = cls._get_create_gp_pnt_func()
        for v in vertices:
            poly.Add(create_gp_pnt(v))
        poly.Close()

        return make_face(poly.Wire())

    @classmethod
    def _create_letter_V(cls):
        poly = BRepBuilderAPI_MakePolygon()
        vertices = [
            (0, 10),
            (1, 10),
            (5, 1),
            (9, 10),
            (10, 10),
            (5.75, 0),
            (4.25, 0),
        ]
        create_gp_pnt = cls._get_create_gp_pnt_func()
        for v in vertices:
            poly.Add(create_gp_pnt(v))
        poly.Close()

        return make_face(poly.Wire())

    @classmethod
    def _create_letter_S(cls):
        poly = BRepBuilderAPI_MakePolygon()
        vertices = [
            (0, 10),
            (10, 10),
            (10, 8.5),
            (1.5, 8.5),
            (1.5, 6),
            (10, 6),
            (10, 0),
            (0, 0),
            (0, 1.5),
            (8.5, 1.5),
            (8.5, 4.5),
            (0, 4.5),
        ]
        create_gp_pnt = cls._get_create_gp_pnt_func()
        for v in vertices:
            poly.Add(create_gp_pnt(v))
        poly.Close()

        return make_face(poly.Wire())

    @classmethod
    def _create_letter_C(cls):
        poly = BRepBuilderAPI_MakePolygon()
        vertices = [
            (0, 10),
            (10, 10),
            (10, 8.5),
            (1.5, 8.5),
            (1.5, 1.5),
            (10, 1.5),
            (10, 0),
            (0, 0),
        ]
        create_gp_pnt = cls._get_create_gp_pnt_func()
        for v in vertices:
            poly.Add(create_gp_pnt(v))
        poly.Close()
        return make_face(poly.Wire())

    @classmethod
    def _create_letter_E(cls):
        poly = BRepBuilderAPI_MakePolygon()
        vertices = [
            (0, 10),
            (10, 10),
            (10, 8.5),
            (1.5, 8.5),
            (1.5, 5.75),
            (8, 5.75),
            (8, 4.25),
            (1.5, 4.25),
            (1.5, 1.5),
            (10, 1.5),
            (10, 0),
            (0, 0),
        ]
        create_gp_pnt = cls._get_create_gp_pnt_func()
        for v in vertices:
            poly.Add(create_gp_pnt(v))
        poly.Close()
        return make_face(poly.Wire())

    @classmethod
    def _create_letter_F(cls):
        poly = BRepBuilderAPI_MakePolygon()
        vertices = [
            (0, 10),
            (10, 10),
            (10, 8.5),
            (1.5, 8.5),
            (1.5, 5.75),
            (8, 5.75),
            (8, 4.25),
            (1.5, 4.25),
            (1.5, 0),
            (0, 0),
        ]
        create_gp_pnt = cls._get_create_gp_pnt_func()
        for v in vertices:
            poly.Add(create_gp_pnt(v))
        poly.Close()
        return make_face(poly.Wire())
