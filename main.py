##Copyright 2010-2014 Thomas Paviot (tpaviot@gmail.com)
##
##This file is part of pythonOCC.
##
##pythonOCC is free software: you can redistribute it and/or modify
##it under the terms of the GNU Lesser General Public License as published by
##the Free Software Foundation, either version 3 of the License, or
##(at your option) any later version.
##
##pythonOCC is distributed in the hope that it will be useful,
##but WITHOUT ANY WARRANTY; without even the implied warranty of
##MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##GNU Lesser General Public License for more details.
##
##You should have received a copy of the GNU Lesser General Public License
##along with pythonOCC.  If not, see <http://www.gnu.org/licenses/>.

"""
The very first pythonocc example. This used to be the script
used to check the following points:
pythonocc installation is correct, i.e. pythonocc modules are found
and properly imported
a GUI manager is installed. Whether it is wxpython or pyqt/pyside, it's necessary
to display a 3d window
the rendering window can be initialized and set up, that is to say the
graphic driver and OpenGl works correctly.
If this example runs on your machine, that means you're ready to explore the wide
pythonocc world and run all the other examples.
"""
from OCC.Display.SimpleGui import init_display
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.gp import gp_Lin2d, gp_Pnt2d, gp_Dir2d, gp_Circ2d, gp_Ax22d, gp_Ax3
from OCC.Core.gp import *
from OCC.Extend.ShapeFactory import make_edge2d
from OCC.Extend.ShapeFactory import *

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
ci1 = gp_Circ(AX_XZ, 5)
display.DisplayColoredShape(make_edge(ci1), update=True, color="GREEN" )
ci2 = gp_Circ(AX_YZ, 5)
display.DisplayColoredShape(make_edge(ci2), update=True, color="WHITE" )

start_display()