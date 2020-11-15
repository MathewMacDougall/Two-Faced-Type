from OCC.Display.SimpleGui import init_display
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRepBuilderAPI import *
from OCC.Core.gp import gp_Lin2d, gp_Pnt2d, gp_Dir2d, gp_Circ2d, gp_Ax22d, gp_Ax3
from OCC.Core.gp import *
from OCC.Extend.ShapeFactory import make_edge2d
from OCC.Extend.ShapeFactory import *
from OCC.Core.BRepFeat import BRepFeat_MakeLinearForm

display, start_display, add_menu, add_function_to_menu = init_display()

ORIGIN = gp_Pnt(0, 0, 0)
DIR_X = gp_Dir(1, 0, 0)
DIR_Y = gp_Dir(0, 1, 0)
DIR_Z = gp_Dir(0, 0, 1)
LINE_X = gp_Lin(ORIGIN, DIR_X)
LINE_Y = gp_Lin(ORIGIN, DIR_Y)
LINE_Z = gp_Lin(ORIGIN, DIR_Z)
display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")

AX_XZ = gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0), gp_Dir(0, 0, 1))
AX_YZ = gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0), gp_Dir(0, 0, 1))

def face_t(ax):
    poly = BRepBuilderAPI_MakePolygon()
    foo = None
    if ax.IsCoplanar(AX_XZ, 0.01, 0.01):
        foo = lambda a, b: gp_Pnt(a, 0, b)
    elif ax.IsCoplanar(AX_XZ, 0.01, 0.01):
        foo = lambda a, b: gp_Pnt(0, a, b)
    else:
        raise RuntimeError("Unexepcted Axis")

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
    for a, b in vertices:
        poly.Add(foo(a, b))
    poly.Close()

    return make_face(poly.Wire())

ci1 = gp_Circ(AX_XZ, 5)
display.DisplayColoredShape(make_edge(ci1), update=True, color="GREEN" )
ci2 = gp_Circ(AX_YZ, 5)
display.DisplayColoredShape(make_edge(ci2), update=True, color="WHITE" )

#test = gp_Pnt2d(AX_XZ, 0, 2)

# face = make_face(make_wire(make_edge(ci2)))
# display.DisplayColoredShape(face, update=True, color="WHITE" )
#
# ext = make_extrusion(face, 100, gp_Vec(1, 0, 0))
# display.DisplayColoredShape(ext, update=True, color="WHITE" )
face = face_t(AX_XZ)
display.DisplayColoredShape(face, update=True, color="WHITE")

start_display()