from pathlib import Path
import copy
import os
import errno
from OCC.Core.StlAPI import StlAPI_Writer, StlAPI_Reader
from OCC.Core.TopoDS import TopoDS_Shape


def read_stl(filepath):
    assert isinstance(filepath, Path)
    assert filepath.is_file()
    stl = TopoDS_Shape()
    reader = StlAPI_Reader()
    success = reader.Read(stl, str(filepath))
    assert success
    return stl

def write_stl(shape, filepath):
    assert isinstance(filepath, Path)

    stl_writer = StlAPI_Writer()
    stl_writer.SetASCIIMode(True)
    stl_writer.Write(copy.deepcopy(shape), str(filepath))


def save_to_stl(shapes, dirpath=Path.home()):
    assert isinstance(shapes, list)

    try:
        os.makedirs(Path(dirpath))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    stl_writer = StlAPI_Writer()
    stl_writer.SetASCIIMode(True)
    for index, shape in enumerate(shapes):
        filepath = Path(dirpath, "combined_shape_" + str(index + 1) + ".stl")
        stl_writer.Write(shape, str(filepath))
