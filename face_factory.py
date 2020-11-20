from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Transform
from OCC.Core.gp import gp_Pnt, gp_Trsf, gp_OX, gp_Vec, gp_XYZ
from OCC.Extend.ShapeFactory import make_face, make_edge
from OCC.Core.BRep import BRep_Tool
from PIL import Image
import numpy as np
import pathlib
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from functools import reduce
from OCC.Extend.TopologyUtils import TopologyExplorer
from svgpathtools import svg2paths, Line, CubicBezier, Path
import logging
logging.getLogger("PIL").setLevel(logging.WARNING)
from constants import PL_XZ
from shapely.geometry import Point, Polygon

class PathHierarhcy():
    def __init__(self, root_path=None, child_paths=None):
        if child_paths is None:
            child_paths = list()
        self._root_path = root_path
        self._child_paths = child_paths

    def root_path(self):
        assert self._root_path
        return self._root_path

    def child_paths(self):
        return self._child_paths

    def set_root_path(self, new_root_path):
        self._root_path = new_root_path

    def add_child_path(self, child_path):
        self._child_paths.append(child_path)

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
    def _path_is_clockwise(cls, path):
        assert isinstance(path, Path)
        # https://stackoverflow.com/a/1165943
        vertices = [(path_component.start.real, path_component.start.imag) for path_component in path]
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
        assert isinstance(filepath, pathlib.Path)
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
        assert isinstance(paths, list)
        normalized_paths = []
        for path in paths:
            assert isinstance(path, Path)
            path_is_clockwise = cls._path_is_clockwise(path)
            if not path_is_clockwise:
                return [path for path in paths]
            clockwise_path = Path()
            for line in reversed(path):
                if isinstance(line, Line):
                    new_start = line.end
                    new_end = line.start
                    line.start = new_start
                    line.end = new_end
                    clockwise_path.append(line)
                elif isinstance(line, CubicBezier):
                    new_start = line.end
                    new_end = line.start
                    new_control1 = line.control2
                    new_control2 = line.control1
                    line.start = new_start
                    line.end = new_end
                    line.control1 = new_control1
                    line.control2 = new_control2
                    clockwise_path.append(line)
                else:
                    raise RuntimeError("Invalid line type")
            normalized_paths.append(clockwise_path)
        return normalized_paths
        # for lines in paths:
        #     if cls._path_is_clockwise(lines):
        #         normalized_paths.append(lines)
        #     else:
        #         vertices = list(reversed([complex(line.start.real, line.start.imag) for line in lines]))
        #         clockwise_lines = [Line(v1, v2) for v1, v2 in zip(vertices, vertices[1:] + [vertices[0]])]
        #         normalized_paths.append(clockwise_lines)
        # return normalized_paths

    @classmethod
    def _point_in_poly(cls, point, lines):
        # helper function for checking if a (complex) point is contained
        # inside a polygon (made of lines)
        poly = Polygon([(line.start.real, line.start.imag) for line in lines])
        return poly.contains(Point(point.real, point.imag))

    @classmethod
    def _create_path_hierarchy(cls, paths):
        # Find path that is not contained by another
        def get_root_path(all_paths):
            for path in all_paths:
                all_except_path = [p for p in all_paths if p != path]
                path_vertices = [complex(line.start.real, line.start.imag) for line in path]
                # TODO: This doesn't really account for Bezier curves, but is close enough for now
                if not any([cls._point_in_poly(v, other_path) for other_path in all_except_path for v in path_vertices]):
                    # No other path contains the current path
                    return path
            return None

        def get_contained_paths(root_path, all_paths):
            all_except_path = [p for p in all_paths if p != root_path]
            contained_paths = []
            for other_path in all_except_path:
                # TODO: This doesn't really account for Bezier curves, but is close enough for now
                other_path_vertices = [complex(line.start.real, line.start.imag) for line in other_path]
                if any([cls._point_in_poly(v, root_path) for v in other_path_vertices]):
                    contained_paths.append(other_path)
            return contained_paths


        hierarchy = []
        paths_copy = [p for p in paths]
        while paths_copy:
            root = get_root_path(paths_copy)
            contained = get_contained_paths(root, paths_copy)
            path_hierarchy = PathHierarhcy(root, contained)
            hierarchy.append(path_hierarchy)
            for cp in contained:
                paths_copy.remove(cp)
            paths_copy.remove(root)
        return hierarchy


        # for path in paths:
        #     path_hierarchy = PathHierarhcy()
        #
        #
        #
        #
        #
        #     ch = [path]
        #     try:
        #         paths_copy.remove(path)
        #     except ValueError:
        #         continue
        #     other_paths_to_remove = []
        #     for other_line in paths_copy:
        #         other_path_vertices = [complex(line.start.real, line.start.imag) for line in other_line]
        #         if any([cls._point_in_poly(v, path) for v in other_path_vertices]):
        #             # poly is contained at least partially by current path
        #             ch.append(other_line)
        #             other_paths_to_remove.append(other_line)
        #     for temp_path in other_paths_to_remove:
        #         try:
        #             paths_copy.remove(temp_path)
        #             print("removed path")
        #         except ValueError:
        #             pass
        #     hierarchy.append(ch)
        #
        # return hierarchy

    @classmethod
    def _create_from_svg(cls, filepath, height_mm):
        assert isinstance(filepath, pathlib.Path)
        if not filepath.is_file():
            raise IOError("Unable to create Face from image file: {}. File does not exist".format(filepath))

        paths, attributes = svg2paths(str(filepath))
        for path in paths:
            print("type: {}     value: {}".format(type(path), path))

        # TODO: is this needed? Are paths generally the single unit of continuity?
        # continuous_paths = [cp for path in paths for cp in cls._get_contiguous_paths(path) ]
        continuous_paths = cls._normalize_lines_clockwise(paths)
        continuous_paths = cls._create_path_hierarchy(continuous_paths)

        # TODO: YOU ARE HERE
        # Got hierarchy (probably) working. Need to convert paths/lines to edges

        from OCC.Core.Geom2d import Geom2d_BezierCurve


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

        # mirror over the x-axis to make the face right-side up
        mirror = gp_Trsf()
        mirror.SetMirror(gp_OX())
        mirrored_face = BRepBuilderAPI_Transform(face, mirror, True).Shape()

        # scale to the desired height
        mirrored_face_explorer = TopologyExplorer(mirrored_face)
        current_height = max([BRep_Tool.Pnt(vertex).Z() for vertex in mirrored_face_explorer.vertices()]) - min([BRep_Tool.Pnt(vertex).Z() for vertex in mirrored_face_explorer.vertices()])
        scaling_factor = height_mm / current_height
        scaling = gp_Trsf()
        scaling.SetScaleFactor(scaling_factor)
        scaled_face = BRepBuilderAPI_Transform(mirrored_face, scaling, True).Shape()

        # Align the face to the x-axis (so it's not floating)
        # and the z-axis (technically not needed, but keeps the location of the
        # combined shape more controlled near the origin)
        scaled_face_explorer = TopologyExplorer(scaled_face)
        smallest_z = min([BRep_Tool.Pnt(vertex).Z() for vertex in scaled_face_explorer.vertices()])
        smallest_x = min([BRep_Tool.Pnt(vertex).X() for vertex in scaled_face_explorer.vertices()])
        translation = gp_Trsf()
        translation.SetTranslation(gp_Vec(gp_XYZ(-smallest_x, 0, -smallest_z)))
        translated_face = BRepBuilderAPI_Transform(scaled_face, translation, True).Shape()

        return translated_face


    @classmethod
    def _create_from_png(cls, filepath, height_mm):
        assert isinstance(filepath, pathlib.Path)
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

        face_images_dir = pathlib.Path(__file__).parent / "face_images"
        assert face_images_dir.is_dir()

        char_image_file = face_images_dir / "{}.png".format(char)
        assert char_image_file.is_file()

        return cls._create_from_png(char_image_file, height_mm)
