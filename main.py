from OCC.Display.SimpleGui import init_display
from OCC.Core.gp import *
from OCC.Extend.ShapeFactory import *
from face_factory import FaceFactory

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



# ci1 = gp_Circ(AX_XZ, 5)
# display.DisplayColoredShape(make_edge(ci1), update=True, color="GREEN" )
# ci2 = gp_Circ(AX_YZ, 5)
# display.DisplayColoredShape(make_edge(ci2), update=True, color="WHITE" )

#test = gp_Pnt2d(AX_XZ, 0, 2)

# face = make_face(make_wire(make_edge(ci2)))
# display.DisplayColoredShape(face, update=True, color="WHITE" )
#
# ext = make_extrusion(face, 100, gp_Vec(1, 0, 0))
# display.DisplayColoredShape(ext, update=True, color="WHITE" )


T = FaceFactory.create_letter_T(AX_XZ)
# display.DisplayColoredShape(T, update=True, color="WHITE")
ex_T = make_extrusion(T, 100, gp_Vec(0, 1, 0))
display.DisplayColoredShape(ex_T, update=True, color="WHITE" )
# I = FaceFactory.create_letter_I(AX_YZ)
# display.DisplayColoredShape(I, update=True, color="GREEN")
V = FaceFactory.create_letter_V(AX_YZ)
# display.DisplayColoredShape(V, update=True, color="BLUE")
ex_V = make_extrusion(V, 100, gp_Vec(1, 0, 0))
display.DisplayColoredShape(ex_V, update=True, color="BLUE" )

start_display()