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

        if char == 'A':
            return cls._create_letter_A()
        elif char == 'B':
            return cls._create_letter_B()
        elif char == 'C':
            return cls._create_letter_C()
        elif char == 'D':
            return cls._create_letter_D()
        elif char == 'E':
            return cls._create_letter_E()
        elif char == 'F':
            return cls._create_letter_F()
        elif char == 'G':
            return cls._create_letter_G()
        elif char == 'H':
            return cls._create_letter_H()
        elif char == 'I':
            return cls._create_letter_I()
        elif char == 'J':
            return cls._create_letter_J()
        elif char == 'K':
            return cls._create_letter_K()
        elif char == 'L':
            return cls._create_letter_L()
        elif char == 'M':
            return cls._create_letter_M()
        elif char == 'N':
            return cls._create_letter_N()
        elif char == 'O':
            return cls._create_letter_O()
        elif char == 'P':
            return cls._create_letter_P()
        elif char == 'Q':
            return cls._create_letter_Q()
        elif char == 'R':
            return cls._create_letter_R()
        elif char == 'S':
            return cls._create_letter_S()
        elif char == 'T':
            return cls._create_letter_T()
        elif char == 'U':
            return cls._create_letter_U()
        elif char == 'V':
            return cls._create_letter_V()
        elif char == 'W':
            return cls._create_letter_W()
        elif char == 'X':
            return cls._create_letter_X()
        elif char == 'Y':
            return cls._create_letter_Y()
        elif char == 'Z':
            return cls._create_letter_Z()
        elif char == '0':
            return cls._create_digit_0()
        elif char == '1':
            return cls._create_digit_1()
        elif char == '2':
            return cls._create_digit_2()
        elif char == '3':
            return cls._create_digit_3()
        elif char == '4':
            return cls._create_digit_4()
        elif char == '5':
            return cls._create_digit_5()
        elif char == '6':
            return cls._create_digit_6()
        elif char == '7':
            return cls._create_digit_7()
        elif char == '8':
            return cls._create_digit_8()
        elif char == '9':
            return cls._create_digit_9()
        else:
            raise RuntimeError("Unsupported character")

    @classmethod
    def _get_create_gp_pnt_func(cls):
        # for now assume everything is in the XZ plane. We can rotate one
        # of the faces when we go to combine them
        return lambda x: gp_Pnt(x[0], 0, x[1])

    @classmethod
    def _create_letter_A(cls):
        pass

    @classmethod
    def _create_letter_B(cls):
        pass

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
    def _create_letter_D(cls):
        pass

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

    @classmethod
    def _create_letter_G(cls):
        pass

    @classmethod
    def _create_letter_H(cls):
        pass

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
    def _create_letter_J(cls):
        pass

    @classmethod
    def _create_letter_K(cls):
        pass

    @classmethod
    def _create_letter_L(cls):
        pass

    @classmethod
    def _create_letter_M(cls):
        pass

    @classmethod
    def _create_letter_N(cls):
        pass

    @classmethod
    def _create_letter_O(cls):
        pass

    @classmethod
    def _create_letter_P(cls):
        pass

    @classmethod
    def _create_letter_Q(cls):
        pass

    @classmethod
    def _create_letter_R(cls):
        pass

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
    def _create_letter_U(cls):
        pass

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
    def _create_letter_W(cls):
        pass

    @classmethod
    def _create_letter_X(cls):
        pass

    @classmethod
    def _create_letter_Y(cls):
        pass

    @classmethod
    def _create_letter_Z(cls):
        pass

    @classmethod
    def _create_digit_0(cls):
        pass

    @classmethod
    def _create_digit_1(cls):
        pass

    @classmethod
    def _create_digit_2(cls):
        pass

    @classmethod
    def _create_digit_3(cls):
        pass

    @classmethod
    def _create_digit_4(cls):
        pass

    @classmethod
    def _create_digit_5(cls):
        pass

    @classmethod
    def _create_digit_6(cls):
        pass

    @classmethod
    def _create_digit_7(cls):
        pass

    @classmethod
    def _create_digit_8(cls):
        pass

    @classmethod
    def _create_digit_9(cls):
        pass