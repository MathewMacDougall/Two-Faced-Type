from OCC.Display.SimpleGui import init_display
from OCC.Extend.ShapeFactory import *
from face_factory import FaceFactory
from OCC.Core.BRepAlgoAPI import *
from constants import *

display, start_display, add_menu, add_function_to_menu = init_display()

display.DisplayShape(make_edge(LINE_X), update=True, color="RED")
display.DisplayShape(make_edge(LINE_Y), update=True, color="GREEN")
display.DisplayShape(make_edge(LINE_Z), update=True, color="BLUE")

T = FaceFactory.create_letter_T(AX_XZ)
# display.DisplayColoredShape(T, update=True, color="WHITE")
ex_T = make_extrusion(T, 100, gp_Vec(0, 1, 0))
# display.DisplayColoredShape(ex_T, update=True, color="WHITE" )
# I = FaceFactory.create_letter_I(AX_YZ)
# display.DisplayColoredShape(I, update=True, color="GREEN")
V = FaceFactory.create_letter_V(AX_YZ)
# display.DisplayColoredShape(V, update=True, color="BLUE")
ex_V = make_extrusion(V, 100, gp_Vec(1, 0, 0))
# display.DisplayColoredShape(ex_V, update=True, color="BLUE" )

common = BRepAlgoAPI_Common(ex_V, ex_T)
display.DisplayColoredShape(common.Shape(), update=True, color="BLUE")

start_display()
