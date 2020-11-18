from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace
from OCC.Core.gp import gp_Pnt
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
    def make_rect(cls, coord, size):
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
        assert len(lines) > 0
        paths = [[]]
        index = 0
        for line in lines:
            # print(line)
            if not paths[index] or line.start == paths[index][-1].end:
                paths[index].append(line)
            else:
                paths.append([])
                index += 1
                paths[index].append(line)
        return paths

    @classmethod
    def lines_are_clockwise(cls, lines):
        # Clockwise = filled in wire/face
        vertices = [(line.start.real, line.start.imag) for line in lines]
        sum = 0
        for v1, v2 in zip(vertices, vertices[1:] + [vertices[0]]):
            sum += (v2[0] - v1[0]) * (v2[1] + v1[1])
        return sum >= 0

    # TODO: you are here
    # https://github.com/tpaviot/pythonocc-utils/tree/master/OCCUtils
    # tyring to figure out wire/face intersections to know what wires to reverse
    # Idea: Take 2 wires/faces, take intersection/AND, and if non-zero area they are intersecting/one is contained in the other

    @classmethod
    def _svg_lines_to_wire_maker(cls, lines):
        wireMaker = BRepBuilderAPI_MakeWire()
        create_gp_pnt = cls._get_create_gp_pnt_func()
        # if not cls.lines_are_clockwise(lines):
        #     lines = reversed(lines)

        for line in lines:
            assert isinstance(line, Line)
            start = line.start
            end = line.end
            p1 = create_gp_pnt((start.real, start.imag))
            p2 = create_gp_pnt((end.real, end.imag))
            if cls.lines_are_clockwise(lines):
                # wireMaker.Add(make_edge(p2, p1))
                wireMaker.Add(make_edge(p1, p2))
            else:
                wireMaker.Add(make_edge(p2, p1))
                # wireMaker.Add(make_edge(p1, p2))
            # print("(({}, {}), ({}, {}))".format(start.real, start.imag, end.real, end.imag))
            # print("(({}, {}), ({}, {}))".format(end.real, end.imag, start.real, start.imag))
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
            return cls.create_from_png(filepath, height_mm)
        else:
            raise RuntimeError("Unable to create Face from image file: {}. Unsupported filetype {}. Please use one of {}".format(filepath, filepath.suffix, "svg, png"))

    @classmethod
    def _normalize_line_direction(cls, paths):
        normalized_paths = []
        for lines in paths:
            if cls.lines_are_clockwise(lines):
                normalized_paths.append(lines)
            else:
                vertices = list(reversed([complex(line.start.real, line.start.imag) for line in lines]))
                clockwise_lines = [Line(v1, v2) for v1, v2 in zip(vertices, vertices[1:] + [vertices[0]])]
                normalized_paths.append(clockwise_lines)
        return normalized_paths

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
                pass
            poly = Polygon([(line.start.real, line.start.imag) for line in p])
            other_paths_to_remove = []
            for other_line in paths_copy:
                other_path_vertices = [complex(line.start.real, line.start.imag) for line in other_line]
                if any([poly.contains(Point(v.real, v.imag)) for v in other_path_vertices]):
                    # poly is contined at least partially by current path
                    ch.append(other_line)
                    other_paths_to_remove.append(other_line)
            for temp_path in other_paths_to_remove:
                try:
                    paths_copy.remove(temp_path)
                except ValueError:
                    pass
            hierarchy.append(ch)

        return hierarchy







    @classmethod
    def _create_from_svg(cls, filepath, height_mm):
        assert isinstance(filepath, Path)
        if not filepath.is_file():
            raise IOError("Unable to create Face from image file: {}. File does not exist".format(filepath))

        # TESTING THAT NESTED WIRES WORK AS I EXPECT AT ALL
        # faceMaker = BRepBuilderAPI_MakeFace(PL_XZ)
        #
        # outer_wire_maker = BRepBuilderAPI_MakeWire()
        # outer_wire_maker.Add(make_edge(gp_Pnt(0, 0, 0), gp_Pnt(0, 0, 100)))
        # outer_wire_maker.Add(make_edge(gp_Pnt(0, 0, 100), gp_Pnt(100, 0, 100)))
        # outer_wire_maker.Add(make_edge(gp_Pnt(100, 0, 100), gp_Pnt(100, 0, 0)))
        # outer_wire_maker.Add(make_edge(gp_Pnt(100, 0, 0), gp_Pnt(0, 0, 0)))
        #
        # inner_wire_maker = BRepBuilderAPI_MakeWire()
        # inner_wire_maker.Add(make_edge(gp_Pnt(30, 0, 30), gp_Pnt(30, 0, 60)))
        # inner_wire_maker.Add(make_edge(gp_Pnt(30, 0, 60), gp_Pnt(60, 0, 60)))
        # inner_wire_maker.Add(make_edge(gp_Pnt(60, 0, 60), gp_Pnt(60, 0, 30)))
        # inner_wire_maker.Add(make_edge(gp_Pnt(60, 0, 30), gp_Pnt(30, 0, 30)))
        #
        # outer_wire = outer_wire_maker.Wire()
        # inner_wire = inner_wire_maker.Wire()
        # inner_wire.Reverse()
        #
        # faceMaker.Add(outer_wire)
        # faceMaker.Add(inner_wire)
        # # outer_wire_maker.Add(inner_wire_maker.Wire())
        #
        # return faceMaker.Shape()

        # NOTE: the above works, but breaks if wires have overlapping edges




        # Find all sets of contiguous lines (assuming they are in order)
        # Create wires/faces for each?
        # Take the largest face, make primary
        # for all other faces, check if they are inside
        #   if yes, make hole

        paths, attributes = svg2paths(str(filepath))
        continuous_paths = [cp for path in paths for cp in cls._get_contiguous_paths(path) ]
        # continuous_paths = cls._normalize_line_direction(continuous_paths)
        continuous_paths = cls._create_path_hierarchy(continuous_paths)
        print("hierarhcy")
        print(continuous_paths)
        faceMaker = BRepBuilderAPI_MakeFace(PL_XZ)
        for f in continuous_paths:
            print("Root wire")
            print(f[0])
            root_wire_maker = cls._svg_lines_to_wire_maker(f[0])
            root_wire = root_wire_maker.Wire()
            faceMaker.Add(root_wire)
            for sub_wires in f[1:]:
                print("sub wire")
                print(sub_wires)
                sub_wire_maker = cls._svg_lines_to_wire_maker(sub_wires)
                sub_wire = sub_wire_maker.Wire()
                sub_wire.Reverse()
                faceMaker.Add(sub_wire)
                # root_wire_maker.Add(sub_wire)
                # assert root_wire_maker.IsDone()
            return faceMaker.Shape()
            # return make_face(root_wire_maker.Wire())




        faceMaker = BRepBuilderAPI_MakeFace(PL_XZ)
        func = cls._get_create_gp_pnt_func()
        continuous_paths = []
        for path in paths:
            continuous_paths += cls._get_contiguous_paths(path)
        # w1 = cls._svg_lines_to_wire(continuous_paths[0])
        # w2 = cls._svg_lines_to_wire(continuous_paths[1])
        # w1.Add(w2)
        # return make_face(w1)
        for cp in continuous_paths:
            # print("cp")
            # print(cp)
            w1 = cls._svg_lines_to_wire_maker(cp)
            # w1.Reverse()
            faceMaker = BRepBuilderAPI_MakeFace(faceMaker.Shape(), w1)
            # w2 = lines_to_wire_maker(cp2).Wire()
            # w2.Reverse()
        return faceMaker.Shape()


    @classmethod
    def create_from_png(cls, filepath, height_mm):
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
                    faces.append(make_face(cls.make_rect((x, z), pixel_size)))
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
        if char == 'E':
            char_image_file = face_images_dir / "E_small.png".format(char)
        elif char == 'Z':
            char_image_file = face_images_dir / "Z_small.png".format(char)
        else:
            char_image_file = face_images_dir / "{}.png".format(char)
        assert char_image_file.is_file()
        return cls.create_from_png(char_image_file, height_mm)
