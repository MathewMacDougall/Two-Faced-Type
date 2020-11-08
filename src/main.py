from util import static_vars
from mpl_toolkits import mplot3d
from matplotlib import pyplot
from letter import *


@static_vars(color_index=0)
def draw_letter(axes, letter):
    color = ['b', 'r', ][draw_letter.color_index]
    draw_letter.color_index = (draw_letter.color_index + 1) % 2
    for seg in letter.segs():
        x = [seg.start().x(), seg.end().x()]
        y = [seg.start().y(), seg.end().y()]
        z = [seg.start().z(), seg.end().z()]
        axes.plot(x, y, z, c=color)


figure = pyplot.figure()
axes = mplot3d.Axes3D(figure)

O = Letter(LINES_O, Plane.XZ)
C = Letter(LINES_C, Plane.YZ)
draw_letter(axes, O)
draw_letter(axes, C)

pyplot.show()
