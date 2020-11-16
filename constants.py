from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Lin, gp_Ax2, gp_Pln

ORIGIN = gp_Pnt(0, 0, 0)
DIR_X = gp_Dir(1, 0, 0)
DIR_Y = gp_Dir(0, 1, 0)
DIR_Z = gp_Dir(0, 0, 1)
LINE_X = gp_Lin(ORIGIN, DIR_X)
LINE_Y = gp_Lin(ORIGIN, DIR_Y)
LINE_Z = gp_Lin(ORIGIN, DIR_Z)
AX_XZ = gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0), gp_Dir(0, 0, 1))
AX_YZ = gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0), gp_Dir(0, 0, 1))
PL_XZ = gp_Pln(ORIGIN, DIR_Y)
