from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Transform
from OCC.Core.gp import gp_Pnt, gp_Trsf, gp_OX
from OCC.Extend.ShapeFactory import make_face, make_edge
from PIL import Image
import numpy as np
from pathlib import Path
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from functools import reduce
from svgpathtools import svg2paths, Line
import logging
logging.getLogger("PIL").setLevel(logging.WARNING)
from constants import PL_XZ
from shapely.geometry import Point, Polygon

class FaceFactory():
    @classmethod
    def _get_create_gp_pnt_func(cls):
        # for now assume everything is in the XZ plane. We can rotate one
        # of the faces when we go to combine them
        return lambda x: gp_Pnt(x[0], 0, x[1])

    @classmethod
    def _make_rect(cls, coord, size):
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
    def _get_contiguous_paths(cls, lines):
        paths = [[]]
        index = 0
        for line in lines:
            if not paths[index] or line.start == paths[index][-1].end:
                paths[index].append(line)
            else:
                paths.append([])
                index += 1
                paths[index].append(line)
        return paths

    @classmethod
    def _lines_are_clockwise(cls, lines):
        # https://stackoverflow.com/a/1165943
        vertices = [(line.start.real, line.start.imag) for line in lines]
        curve_sum = sum((v2[0] - v1[0]) * (v2[1] + v1[1]) for v1, v2 in zip(vertices, vertices[1:] + [vertices[0]]))
        return curve_sum >= 0

    @classmethod
    def _create_wire_maker_from_lines(cls, lines):
        wireMaker = BRepBuilderAPI_MakeWire()
        create_gp_pnt = cls._get_create_gp_pnt_func()

        for line in lines:
            assert isinstance(line, Line)
            start = line.start
            end = line.end
            p1 = create_gp_pnt((start.real, start.imag))
            p2 = create_gp_pnt((end.real, end.imag))
            wireMaker.Add(make_edge(p1, p2))
        return wireMaker

    @classmethod
    def create_from_image(cls, filepath, height_mm):
        assert isinstance(filepath, Path)
        if not filepath.is_file():
            raise IOError("Unable to create Face from image file: {}. File does not exist".format(filepath))

        if filepath.suffix == "svg":
            return cls._create_from_svg(filepath, height_mm)
        elif filepath.suffix == "png":
            # TODO: this probably can handle JPG too?
            return cls._create_from_png(filepath, height_mm)
        else:
            raise RuntimeError("Unable to create Face from image file: {}. Unsupported filetype {}. Please use one of {}".format(filepath, filepath.suffix, "svg, png"))

    @classmethod
    def _normalize_lines_clockwise(cls, paths):
        normalized_paths = []
        for lines in paths:
            if cls._lines_are_clockwise(lines):
                normalized_paths.append(lines)
            else:
                vertices = list(reversed([complex(line.start.real, line.start.imag) for line in lines]))
                clockwise_lines = [Line(v1, v2) for v1, v2 in zip(vertices, vertices[1:] + [vertices[0]])]
                normalized_paths.append(clockwise_lines)
        return normalized_paths

    @classmethod
    def _point_in_poly(cls, point, lines):
        # helper function for checking if a (complex) point is contained
        # inside a polygon (made of lines)
        poly = Polygon([(line.start.real, line.start.imag) for line in lines])
        return poly.contains(Point(point.real, point.imag))

    @classmethod
    def _create_path_hierarchy(cls, paths):
        # list of lists, where the first element contains all subsequent ones
        hierarchy = []
        paths_copy = [p for p in paths]
        for p in paths:
            ch = [p]
            try:
                paths_copy.remove(p)
            except ValueError:
                continue
            other_paths_to_remove = []
            for other_line in paths_copy:
                other_path_vertices = [complex(line.start.real, line.start.imag) for line in other_line]
                if any([cls._point_in_poly(v, p) for v in other_path_vertices]):
                    # poly is contained at least partially by current path
                    ch.append(other_line)
                    other_paths_to_remove.append(other_line)
            for temp_path in other_paths_to_remove:
                try:
                    paths_copy.remove(temp_path)
                    print("removed path")
                except ValueError:
                    pass
            hierarchy.append(ch)

        return hierarchy

    @classmethod
    def _create_from_svg(cls, filepath, height_mm):
        assert isinstance(filepath, Path)
        if not filepath.is_file():
            raise IOError("Unable to create Face from image file: {}. File does not exist".format(filepath))

        paths, attributes = svg2paths(str(filepath))
        continuous_paths = [cp for path in paths for cp in cls._get_contiguous_paths(path) ]
        continuous_paths = cls._normalize_lines_clockwise(continuous_paths)
        continuous_paths = cls._create_path_hierarchy(continuous_paths)
        faceMaker = BRepBuilderAPI_MakeFace(PL_XZ)
        # Right now can only handle a single "main" face with holes
        assert len(continuous_paths) < 2
        for f in continuous_paths:
            root_wire_maker = cls._create_wire_maker_from_lines(f[0])
            root_wire = root_wire_maker.Wire()
            faceMaker.Add(root_wire)
            for sub_wires in f[1:]:
                sub_wire_maker = cls._create_wire_maker_from_lines(sub_wires)
                sub_wire = sub_wire_maker.Wire()
                sub_wire.Reverse()
                faceMaker.Add(sub_wire)
        face = faceMaker.Shape()
        mirror = gp_Trsf()
        mirror.SetMirror(gp_OX())
        mirrored_face = BRepBuilderAPI_Transform(face, mirror, True).Shape()
        return mirrored_face


    @classmethod
    def _create_from_png(cls, filepath, height_mm):
        assert isinstance(filepath, Path)
        if not filepath.is_file():
            raise IOError("Unable to create Face from image file: {}. File does not exist".format(filepath))

        # Combining wires didn't work as expected. It left some "pixels" with
        # weird artifacts and wouldn't quite create a contiguous face (some triangles
        # would be missing from pixels).
        # Combining faces seems to work much better, and even allows for non-contiguous
        # shapes (although this won't look good in the final product)
        from time import time
        im_frame = Image.open(filepath)
        np_frame = np.array(im_frame)
        pixel_size = height_mm / np_frame.shape[0]
        faces = []
        make_faces_start = time()
        for z, row in enumerate(reversed(np_frame)):
            for x, col in enumerate(row):
                if col[0] < 1:
                    # fill in the pixel
                    faces.append(make_face(cls._make_rect((x, z), pixel_size)))
        make_faces_end = time()
        print("Making faces took {} seconds".format(make_faces_end - make_faces_start))
        fuse_start = time()
        fuse_faces = lambda f1, f2: BRepAlgoAPI_Fuse(f1, f2).Shape()
        fused = reduce(fuse_faces, faces, faces[0])
        fuse_end = time()
        print("Fusing faces took {} seconds".format(fuse_end - fuse_start))
        return fused

    @classmethod
    def create_char(cls, char, height_mm):
        if not char.isalpha():
            raise ValueError("Unable to create face from char. Only alphanumeric characters are supported")

        char = char.upper()

        face_images_dir = Path(__file__).parent / "face_images"
        assert face_images_dir.is_dir()

        char_image_file = face_images_dir / "{}.png".format(char)
        assert char_image_file.is_file()

        return cls._create_from_png(char_image_file, height_mm)
