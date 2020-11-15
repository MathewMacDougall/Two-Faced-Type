from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
from OCC.Core.gp import gp_Pnt
from OCC.Extend.ShapeFactory import make_face

class FaceFactory():
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
        else:
            raise RuntimeError("Unsupported character")

    @classmethod
    def _get_create_gp_pnt_func(cls):
        # for now assume everything is in the XZ plane. We can rotate one
        # of the faces when we go to combine them
        return lambda a, b: gp_Pnt(a, 0, b)

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
        for a, b in vertices:
            poly.Add(create_gp_pnt(a, b))
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
        for a, b in vertices:
            poly.Add(create_gp_pnt(a, b))
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
        for a, b in vertices:
            poly.Add(create_gp_pnt(a, b))
        poly.Close()

        return make_face(poly.Wire())
