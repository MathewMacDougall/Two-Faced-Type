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
            print(line)
            if not paths[index] or line.start == paths[index][-1].end:
                paths[index].append(line)
            else:
                paths.append([])
                index += 1
                paths[index].append(line)
        return paths

    @classmethod
    def _svg_lines_to_wire(cls, lines):
        wireMaker = BRepBuilderAPI_MakeWire()
        create_gp_pnt = cls._get_create_gp_pnt_func()
        for line in lines:
            assert isinstance(line, Line)
            start = line.start
            end = line.end
            p1 = create_gp_pnt((start.real, start.imag))
            p2 = create_gp_pnt((end.real, end.imag))
            wireMaker.Add(make_edge(p1, p2))
        return wireMaker.Wire()

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
    def _create_from_svg(cls, filepath, height_mm):
        assert isinstance(filepath, Path)
        if not filepath.is_file():
            raise IOError("Unable to create Face from image file: {}. File does not exist".format(filepath))

        # Find all sets of contiguous lines (assuming they are in order)
        # Create wires/faces for each?
        # Take the largest face, make primary
        # for all other faces, check if they are inside
        #   if yes, make hole

        paths, attributes = svg2paths(str(filepath))
        faceMaker = BRepBuilderAPI_MakeFace(PL_XZ)
        func = cls._get_create_gp_pnt_func()
        continuous_paths = []
        for path in paths:
            continuous_paths += cls._get_contiguous_paths(path)
        for cp in continuous_paths:
            # print("cp")
            # print(cp)
            w1 = cls._svg_lines_to_wire(cp)
            w1.Reverse()
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
