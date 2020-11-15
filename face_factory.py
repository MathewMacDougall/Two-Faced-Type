from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
from OCC.Core.gp import gp_Pnt, gp_Ax2, gp_Dir
from OCC.Extend.ShapeFactory import make_face

# TODO: this is currently copy-pasted
AX_XZ = gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0), gp_Dir(0, 0, 1))
AX_YZ = gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0), gp_Dir(0, 0, 1))

class FaceFactory():
    @classmethod
    def _get_create_gp_pnt_func(cls, ax):
        func = None
        if ax.IsCoplanar(AX_XZ, 0.01, 0.01):
            func = lambda a, b: gp_Pnt(a, 0, b)
        elif ax.IsCoplanar(AX_YZ, 0.01, 0.01):
            func = lambda a, b: gp_Pnt(0, a, b)
        else:
            raise RuntimeError("Unexpected Axis")
        return func

    @classmethod
    def create_letter_T(cls, ax):
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
        create_gp_pnt = cls._get_create_gp_pnt_func(ax)
        for a, b in vertices:
            poly.Add(create_gp_pnt(a, b))
        poly.Close()

        return make_face(poly.Wire())

    @classmethod
    def create_letter_I(cls, ax):
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
        create_gp_pnt = cls._get_create_gp_pnt_func(ax)
        for a, b in vertices:
            poly.Add(create_gp_pnt(a, b))
        poly.Close()

        return make_face(poly.Wire())

    @classmethod
    def create_letter_V(cls, ax):
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
        create_gp_pnt = cls._get_create_gp_pnt_func(ax)
        for a, b in vertices:
            poly.Add(create_gp_pnt(a, b))
        poly.Close()

        return make_face(poly.Wire())
