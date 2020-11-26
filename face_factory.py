from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.Geom import Geom_BezierCurve
from OCC.Core.TColgp import TColgp_Array1OfPnt
from OCC.Core.gp import gp_Pnt, gp_Trsf, gp_OX, gp_Vec, gp_XYZ
import OCC.Core.GeomConvert as g2dc
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeWire
from OCC.Extend.ShapeFactory import make_edge
from OCC.Core.BRep import BRep_Tool
import pathlib
from OCC.Extend.TopologyUtils import TopologyExplorer
from svgpathtools import svg2paths, Line, CubicBezier, Path, QuadraticBezier
import logging
from constants import PL_XZ
from shapely.geometry import Point, Polygon
from svg_path_hierarchy import SvgPathHierarchy

logging.getLogger("PIL").setLevel(logging.WARNING)


class FaceFactory():
    @classmethod
    def create_from_image(cls, filepath, height_mm):
        assert isinstance(filepath, pathlib.Path)
        if not filepath.is_file():
            raise IOError("Unable to create Face from image file: {}. File does not exist".format(filepath))

        if filepath.suffix == "svg":
            return cls._create_from_svg(filepath, height_mm)
        else:
            raise RuntimeError(
                "Unable to create Face from image file: {}. Unsupported filetype {}. Please use one of {}".format(
                    filepath, filepath.suffix, "svg"))

    @classmethod
    def create_char(cls, char, height_mm):
        if not char.isalpha():
            raise ValueError("Unable to create face from char. Only alphanumeric characters are supported")

        char = char.upper()

        face_images_dir = pathlib.Path(__file__).parent / "face_images"
        assert face_images_dir.is_dir()

        char_image_file = face_images_dir / "{}.svg".format(char)
        assert char_image_file.is_file()

        return cls._create_from_svg(char_image_file, height_mm)

    @classmethod
    def _create_from_svg(cls, filepath, height_mm):
        assert isinstance(filepath, pathlib.Path)
        if not filepath.is_file():
            raise IOError("Unable to create Face from image file: {}. File does not exist".format(filepath))

        paths, attributes = svg2paths(str(filepath))

        paths = cls._get_continuous_subpaths(paths)
        paths = cls._remote_zero_length_lines(paths)
        continuous_paths = cls._normalize_paths_clockwise(paths)
        continuous_paths = cls._create_path_hierarchy(continuous_paths)

        faceMaker = BRepBuilderAPI_MakeFace(PL_XZ)
        for path_hierarchy in continuous_paths:
            root_wire_maker = cls._create_wire_maker_from_lines(path_hierarchy.root_path())
            root_wire = root_wire_maker.Wire()
            faceMaker.Add(root_wire)
            for sub_path in path_hierarchy.child_paths():
                sub_wire_maker = cls._create_wire_maker_from_lines(sub_path)
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
        current_height = max([BRep_Tool.Pnt(vertex).Z() for vertex in mirrored_face_explorer.vertices()]) - min(
            [BRep_Tool.Pnt(vertex).Z() for vertex in mirrored_face_explorer.vertices()])
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
    def _get_create_gp_pnt_func(cls):
        # for now assume everything is in the XZ plane. We can rotate one
        # of the faces when we go to combine them
        return lambda x: gp_Pnt(x[0], 0, x[1])

    @classmethod
    def _remote_zero_length_lines(cls, paths):
        new_paths = []
        for path in paths:
            pp = list(filter(lambda x: x.start != x.end, path))
            newpath = Path()
            for p in pp:
                newpath.append(p)
            new_paths.append(newpath)
        return new_paths

    @classmethod
    def _get_continuous_subpaths(cls, paths):
        subpaths = []
        for path in paths:
            assert isinstance(path, Path)
            subpaths += path.continuous_subpaths()
        return subpaths

    @classmethod
    def _normalize_paths_clockwise(cls, paths):
        assert isinstance(paths, list)
        normalized_paths = []
        for path in paths:
            assert isinstance(path, Path)
            if cls._path_is_clockwise(path):
                normalized_paths.append(path)
            else:
                normalized_paths.append(path.reversed())
        return normalized_paths

    @classmethod
    def _path_is_clockwise(cls, path):
        assert isinstance(path, Path)
        # https://stackoverflow.com/a/1165943
        vertices = [(path_component.start.real, path_component.start.imag) for path_component in path]
        curve_sum = sum((v2[0] - v1[0]) * (v2[1] + v1[1]) for v1, v2 in zip(vertices, vertices[1:] + [vertices[0]]))
        return curve_sum >= 0

    @classmethod
    def _create_path_hierarchy(cls, paths):
        # Find path that is not contained by another
        def get_root_path(all_paths):
            for path in all_paths:
                all_except_path = [p for p in all_paths if p != path]
                path_vertices = [complex(line.start.real, line.start.imag) for line in path]
                # TODO: This doesn't really account for Bezier curves, but is close enough for now
                if not any(
                        [cls._point_in_poly(v, other_path) for other_path in all_except_path for v in path_vertices]):
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
            path_hierarchy = SvgPathHierarchy(root, contained)
            hierarchy.append(path_hierarchy)
            for cp in contained:
                paths_copy.remove(cp)
            paths_copy.remove(root)
        return hierarchy

    @classmethod
    def _point_in_poly(cls, point, lines):
        # helper function for checking if a (complex) point is contained
        # inside a polygon (made of lines)
        poly = Polygon([(line.start.real, line.start.imag) for line in lines])
        return poly.contains(Point(point.real, point.imag))

    @classmethod
    def _create_wire_maker_from_lines(cls, lines):
        wireMaker = BRepBuilderAPI_MakeWire()
        create_gp_pnt = cls._get_create_gp_pnt_func()

        for line in lines:
            if isinstance(line, Line):
                start = line.start
                end = line.end
                p1 = create_gp_pnt((start.real, start.imag))
                p2 = create_gp_pnt((end.real, end.imag))
                wireMaker.Add(make_edge(p1, p2))
            elif isinstance(line, CubicBezier):
                wireMaker.Add(cls._create_edge_from_bezier_pts(line.start, line.end, line.control1, line.control2))
            elif isinstance(line, QuadraticBezier):
                wireMaker.Add(cls._create_edge_from_bezier_pts(line.start, line.end, line.control))
            else:
                raise RuntimeError("Invalid line type")

        return wireMaker

    @classmethod
    def _create_edge_from_bezier_pts(cls, start, end, *control_pts):
        create_gp_pnt = cls._get_create_gp_pnt_func()
        arr = TColgp_Array1OfPnt(0, 1+len(control_pts))
        arr.SetValue(0, create_gp_pnt((start.real, start.imag)))
        index = 1
        for cp in control_pts:
            arr.SetValue(index, create_gp_pnt((cp.real, cp.imag)))
            index += 1
        arr.SetValue(index, create_gp_pnt((end.real, end.imag)))
        bcurve = Geom_BezierCurve(arr)
        bspline = g2dc.GeomConvert_CompCurveToBSplineCurve(bcurve).BSplineCurve()
        edge = BRepBuilderAPI_MakeEdge(bspline).Edge()
        return edge
